# ============================================================
# pages/04_Route_Optimizer.py — AI Route Optimizer
# ============================================================
# Features:
#  • Nearest-Neighbor TSP heuristic for multi-pickup routing
#  • Google Maps embed for real route visualization
#  • Auto-selects pending listings and builds optimal route
#  • Estimated distance & time calculation
#  • Save routes to Firestore
# ============================================================

import streamlit as st
st.set_page_config(page_title="Route Optimizer · FoodBridge", page_icon="🗺️", layout="wide")

import math
from datetime import datetime, timezone
from itertools import permutations

from firebase_config import (
    get_available_listings, get_routes,
    save_route, update_listing_status,
    GOOGLE_MAPS_API_KEY
)
from styles import get_css, render_kpi

st.markdown(get_css(), unsafe_allow_html=True)

# ── Auth guard ────────────────────────────────────────────────
if not st.session_state.get("authenticated"):
    st.warning("Please sign in.")
    st.page_link("app.py", label="← Login")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:0.8rem 0 1.2rem;">
        <div style="font-size:1.8rem;">🌉</div>
        <div style="font-size:1rem;font-weight:800;font-family:'Space Grotesk',sans-serif;
                    background:linear-gradient(135deg,#34D399,#6366F1);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">FoodBridge</div>
    </div>""", unsafe_allow_html=True)

    role_icon = {"admin": "🛡️", "donor": "🍽️", "receiver": "🤝"}.get(st.session_state.user_role, "👤")
    st.markdown(f"""
    <div class="sidebar-user">
        <div class="su-name">{role_icon} {st.session_state.user_name}</div>
        <div class="su-role">{st.session_state.user_role}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("### ⚙️ Optimizer Settings")
    driver_start_lat = st.number_input("Driver Start Lat",  value=19.0760, format="%.4f")
    driver_start_lng = st.number_input("Driver Start Lng",  value=72.8777, format="%.4f")
    driver_start_lbl = st.text_input("Start Location Label", value="Driver Base")
    drop_lat = st.number_input("Drop-off Lat",  value=19.0610, format="%.4f")
    drop_lng = st.number_input("Drop-off Lng",  value=72.9570, format="%.4f")
    drop_lbl = st.text_input("Drop-off Label", value="Community Kitchen")
    max_stops = st.slider("Max Pickup Stops", 2, 10, 4)
    avg_speed_kmh = st.number_input("Avg Speed (km/h)", value=25.0, step=5.0)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.page_link("app.py", label="🏠 Home")
    st.page_link("pages/01_Donor.py", label="🍽️ Donor")
    st.page_link("pages/02_Receiver.py", label="🤝 Receiver")
    if st.session_state.get("user_role") == "admin":
        st.page_link("pages/03_Admin.py", label="🛡️ Admin")
    st.page_link("pages/04_Route_Optimizer.py", label="🗺️ Route Optimizer")
    st.page_link("pages/05_Feedback.py", label="💬 Feedback")
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.switch_page("app.py")


# ════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════

def haversine_km(lat1, lng1, lat2, lng2) -> float:
    """Great-circle distance between two GPS points in kilometres."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def nearest_neighbor_route(start: tuple, stops: list[tuple], end: tuple) -> list[tuple]:
    """
    Nearest-Neighbor heuristic for TSP.
    start / end are (lat, lng, label) tuples.
    stops are (lat, lng, label, listing_id) tuples.
    Returns an ordered list of all points including start and end.
    """
    unvisited = list(stops)
    route = [start]
    current = start[:2]  # (lat, lng)

    while unvisited:
        nearest = min(unvisited, key=lambda s: haversine_km(current[0], current[1], s[0], s[1]))
        route.append(nearest)
        current = nearest[:2]
        unvisited.remove(nearest)

    route.append(end)
    return route


def total_route_km(route: list[tuple]) -> float:
    total = 0.0
    for i in range(len(route) - 1):
        total += haversine_km(route[i][0], route[i][1], route[i+1][0], route[i+1][1])
    return round(total, 2)


def build_google_maps_url(waypoints: list[tuple]) -> str:
    """
    Builds a Google Maps Directions URL from waypoints.
    Each waypoint is (lat, lng, label).
    """
    if len(waypoints) < 2:
        return ""
    origin = f"{waypoints[0][0]},{waypoints[0][1]}"
    dest   = f"{waypoints[-1][0]},{waypoints[-1][1]}"
    mids   = "|".join(f"{w[0]},{w[1]}" for w in waypoints[1:-1])
    url    = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={dest}"
    if mids:
        url += f"&waypoints={mids}"
    url += "&travelmode=driving"
    return url


def build_maps_embed_url(waypoints: list[tuple], api_key: str) -> str:
    """
    Builds a Google Maps Embed API URL.
    Falls back gracefully when no API key is provided.
    """
    if not api_key or len(waypoints) < 2:
        return ""
    origin = f"{waypoints[0][0]},{waypoints[0][1]}"
    dest   = f"{waypoints[-1][0]},{waypoints[-1][1]}"
    mids   = "|".join(f"{w[0]},{w[1]}" for w in waypoints[1:-1])
    url = (
        f"https://www.google.com/maps/embed/v1/directions"
        f"?key={api_key}"
        f"&origin={origin}"
        f"&destination={dest}"
        f"&mode=driving"
    )
    if mids:
        url += f"&waypoints={mids}"
    return url


# ════════════════════════════════════════════════════════════
# PAGE CONTENT
# ════════════════════════════════════════════════════════════

st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.5rem;flex-wrap:wrap;gap:0.8rem;">
    <div>
        <div class="section-title">🗺️ Route Optimizer</div>
        <div class="section-sub">AI-powered multi-stop delivery route planning for food redistribution</div>
    </div>
    <div class="live-badge"><span class="pulse-dot"></span>AI ENGINE</div>
</div>
""", unsafe_allow_html=True)

# ── How it works ──────────────────────────────────────────────
with st.expander("ℹ️ How the Route Optimizer Works", expanded=False):
    st.markdown("""
    The **FoodBridge Route Optimizer** uses a **Nearest-Neighbor TSP heuristic** to find
    the most efficient pickup sequence for food redistribution.

    **Algorithm steps:**
    1. Fetch all listings with status `available` or `requested` that have GPS coordinates
    2. Start from the driver's base location
    3. At each step, pick the **nearest unvisited pickup** (minimizes backtracking)
    4. End at the designated **community drop-off point**
    5. Calculate total distance (Haversine formula) and estimated time

    **Google Maps Integration:**
    - After optimization, the route is rendered on an interactive Google Maps embed
    - A "Open in Google Maps" link gives turn-by-turn navigation
    - When Google Maps API key is not configured, we fall back to `folium` (OpenStreetMap)

    *This is a heuristic — for exact optimal TSP you would need exact solvers (e.g. OR-Tools),
    which is overkill for < 20 stops.*
    """)

# ── Load listings with geo data ───────────────────────────────
all_listings = get_available_listings(60)
geo_listings = [l for l in all_listings if l.get("lat") and l.get("lng")]

# Build stop tuples: (lat, lng, label, listing_id)
stops_raw = [
    (l["lat"], l["lng"], f"{l.get('food_name','')} | {l.get('address','')[:30]}", l["listing_id"])
    for l in geo_listings
]

# Listing selector
st.markdown("### 📍 Select Pickup Stops")
st.markdown("""<div style="font-size:0.84rem;color:rgba(228,237,255,0.5);margin-bottom:0.8rem;">
    Choose which available food listings to include in the route. The optimizer will arrange them
    in the most efficient pickup order automatically.
</div>""", unsafe_allow_html=True)

if not stops_raw:
    st.warning("⚠️ No geo-tagged listings available right now. Add listings with coordinates first.", icon="📍")
    st.stop()

# Multiselect for stops
stop_labels = [f"{s[2]} ({s[1]:.4f}, {s[0]:.4f})" for s in stops_raw]
selected_labels = st.multiselect(
    "Available pickups",
    options=stop_labels,
    default=stop_labels[:min(max_stops, len(stop_labels))],
    help="Select up to the max stops you configured in the sidebar"
)

selected_stops = [stops_raw[stop_labels.index(l)] for l in selected_labels]

if not selected_stops:
    st.info("Please select at least one pickup stop.", icon="🗺️")
    st.stop()

# ── Run optimizer ─────────────────────────────────────────────
col_btn, col_note = st.columns([1, 3])
with col_btn:
    run_opt = st.button("🚀 Optimize Route", use_container_width=True)
with col_note:
    st.markdown(f"""
    <div style="padding:0.65rem;font-size:0.83rem;color:rgba(228,237,255,0.5);">
        🧮 Will optimize <b style="color:#34D399;">{len(selected_stops)} stops</b> using
        Nearest-Neighbor heuristic &nbsp;|&nbsp;
        Driver starts at <b style="color:#fff;">{driver_start_lbl}</b> &nbsp;→&nbsp;
        Drops at <b style="color:#fff;">{drop_lbl}</b>
    </div>
    """, unsafe_allow_html=True)

if run_opt or st.session_state.get("route_computed"):
    start_pt = (driver_start_lat, driver_start_lng, driver_start_lbl)
    end_pt   = (drop_lat, drop_lng, drop_lbl)

    with st.spinner("Computing optimal route…"):
        route = nearest_neighbor_route(start_pt, selected_stops, end_pt)

    total_km  = total_route_km(route)
    est_mins  = round((total_km / avg_speed_kmh) * 60)
    est_hrs   = est_mins // 60
    est_rem   = est_mins % 60
    time_str  = f"{est_hrs}h {est_rem}m" if est_hrs else f"{est_mins} min"

    st.session_state.route_computed   = True
    st.session_state.route_data       = route
    st.session_state.route_km         = total_km
    st.session_state.route_mins       = est_mins
    st.session_state.route_stops      = selected_stops

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Route KPIs ─────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    total_food_kg = sum(
        next((l.get("quantity_kg",0) for l in geo_listings if l["listing_id"]==s[3]), 0)
        for s in selected_stops
    )
    with k1: st.markdown(render_kpi("Total Stops", str(len(selected_stops)), "Pickup locations"), unsafe_allow_html=True)
    with k2: st.markdown(render_kpi("Route Distance", f"{total_km} km", "Haversine estimate"), unsafe_allow_html=True)
    with k3: st.markdown(render_kpi("Est. Time", time_str, f"@ {avg_speed_kmh} km/h avg"), unsafe_allow_html=True)
    with k4: st.markdown(render_kpi("Food to Collect", f"{total_food_kg:.1f} kg", "This route"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_route, col_map = st.columns([1, 2])

    # ── Step-by-step route ─────────────────────────────────────
    with col_route:
        st.markdown("""<div class="section-title" style="font-size:1.05rem;">📋 Optimized Stop Sequence</div>
        <div class="section-sub">Nearest-Neighbor ordering</div>""", unsafe_allow_html=True)

        for i, point in enumerate(route):
            is_start = (i == 0)
            is_end   = (i == len(route) - 1)
            icon = "🏁" if is_start else ("🎯" if is_end else f"📍")
            color = "#34D399" if is_start else ("#FB923C" if is_end else "#818CF8")
            label = point[2] if len(point) > 2 else "Stop"

            if i < len(route) - 1:
                seg_km = haversine_km(route[i][0], route[i][1], route[i+1][0], route[i+1][1])
                seg_str = f"→ {seg_km:.1f} km to next"
            else:
                seg_str = "🏁 End"

            st.markdown(f"""
            <div style="display:flex;align-items:flex-start;gap:0.8rem;margin-bottom:0.6rem;padding:0.6rem 0.8rem;
                        background:rgba(255,255,255,0.03);border-radius:10px;
                        border-left:3px solid {color};">
                <div style="font-size:1.1rem;min-width:24px;">{icon}</div>
                <div>
                    <div style="font-size:0.85rem;font-weight:600;color:#fff;">
                        Stop {i}: {label[:45]}
                    </div>
                    <div style="font-size:0.72rem;color:rgba(228,237,255,0.38);margin-top:2px;">
                        {point[0]:.4f}, {point[1]:.4f} &nbsp;·&nbsp; {seg_str}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Google Maps link
        gm_url = build_google_maps_url(route)
        if gm_url:
            st.markdown(f"""
            <a href="{gm_url}" target="_blank" style="
                display:block; margin-top:1rem; padding:0.7rem 1rem; text-align:center;
                background:linear-gradient(135deg,#34D399,#10B981);
                border-radius:12px; color:#060B18; font-weight:700; font-size:0.9rem;
                text-decoration:none; box-shadow:0 4px 16px rgba(52,211,153,0.35);
                transition:all 0.25s ease;">
                🗺️ Open Full Route in Google Maps ↗
            </a>
            """, unsafe_allow_html=True)

        # Save route button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Save Route to Firestore", use_container_width=True):
            waypoints = [{"label": p[2], "lat": p[0], "lng": p[1]} for p in route]
            route_data = {
                "driver_id":    st.session_state.uid,
                "listing_ids":  [s[3] for s in selected_stops],
                "waypoints":    waypoints,
                "total_km":     total_km,
                "est_minutes":  est_mins,
            }
            route_id = save_route(route_data)
            st.success(f"✅ Route saved! ID: `{route_id[:12]}…`")

    # ── Map visualization ──────────────────────────────────────
    with col_map:
        st.markdown("""<div class="section-title" style="font-size:1.05rem;">🗺️ Route Map</div>
        <div class="section-sub">Interactive visualization of the optimized route</div>""",
        unsafe_allow_html=True)

        # Try Google Maps embed
        embed_url = build_maps_embed_url(route, GOOGLE_MAPS_API_KEY)

        if embed_url:
            st.markdown(f"""
            <div class="map-container">
                <iframe width="100%" height="450"
                    src="{embed_url}"
                    style="border:0;border-radius:16px;"
                    allowfullscreen referrerpolicy="no-referrer-when-downgrade">
                </iframe>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Fallback: folium interactive map
            try:
                import folium
                from streamlit_folium import st_folium

                center_lat = sum(p[0] for p in route) / len(route)
                center_lng = sum(p[1] for p in route) / len(route)
                m = folium.Map(location=[center_lat, center_lng], zoom_start=11,
                               tiles="CartoDB dark_matter")

                # Draw route line
                route_coords = [(p[0], p[1]) for p in route]
                folium.PolyLine(
                    route_coords,
                    color="#34D399",
                    weight=4,
                    opacity=0.85,
                    dash_array="8 4",
                ).add_to(m)

                # Markers
                for i, point in enumerate(route):
                    is_start = (i == 0)
                    is_end   = (i == len(route) - 1)
                    color = "green" if is_start else ("red" if is_end else "blue")
                    icon_name = "home" if is_start else ("flag" if is_end else "map-marker")
                    label = point[2] if len(point) > 2 else f"Stop {i}"

                    folium.Marker(
                        [point[0], point[1]],
                        popup=folium.Popup(f"<b>Stop {i}</b><br>{label}", max_width=200),
                        tooltip=f"Stop {i}: {label[:30]}",
                        icon=folium.Icon(color=color, icon="circle", prefix="fa")
                    ).add_to(m)

                st.markdown('<div class="map-container">', unsafe_allow_html=True)
                st_folium(m, width="100%", height=450)
                st.markdown('</div>', unsafe_allow_html=True)

                if not GOOGLE_MAPS_API_KEY:
                    st.caption(
                        "💡 Add `GOOGLE_MAPS_API_KEY` to your `.env` file to enable the official "
                        "Google Maps embed with turn-by-turn route visualization."
                    )

            except ImportError:
                # Final fallback: st.map
                import pandas as pd
                df_map = pd.DataFrame([
                    {"lat": p[0], "lon": p[1]} for p in route
                ])
                st.map(df_map)
                st.caption("Install `folium` and `streamlit-folium` for a richer map experience.")


# ════════════════════════════════════════════════════════════
# SAVED ROUTES HISTORY
# ════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("📂 Saved Routes History", expanded=False):
    routes = get_routes(20)
    if not routes:
        st.info("No routes saved yet.", icon="📭")
    else:
        for r in routes:
            created = str(r.get("created_at",""))[:16]
            wp_count = len(r.get("waypoints", []))
            gm_link = build_google_maps_url([
                (w["lat"], w["lng"], w.get("label","")) for w in r.get("waypoints",[])
            ])
            st.markdown(f"""
            <div class="route-card">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
                    <div>
                        <div style="font-weight:700;color:#fff;">🗺️ Route {r['route_id'][:10]}…</div>
                        <div style="font-size:0.78rem;color:rgba(228,237,255,0.45);margin-top:0.2rem;">
                            {wp_count} waypoints &nbsp;·&nbsp;
                            {r.get('total_km',0):.1f} km &nbsp;·&nbsp;
                            ~{r.get('est_minutes',0)} min &nbsp;·&nbsp;
                            Saved: {created}
                        </div>
                    </div>
                    <span class="badge badge-{'green' if r.get('status')=='planned' else 'blue'}">{r.get('status','planned')}</span>
                </div>
                {"<a href='" + gm_link + "' target='_blank' style='font-size:0.78rem;color:#34D399;text-decoration:none;'>→ Open in Google Maps</a>" if gm_link else ""}
            </div>
            """, unsafe_allow_html=True)
