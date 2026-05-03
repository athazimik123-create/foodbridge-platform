# ============================================================
# pages/01_Donor.py — Donor Dashboard
# ============================================================
# Donors can:
#  • List new surplus food (with quantity, location, type)
#  • View and manage their active listings
#  • See impact stats
# ============================================================

import streamlit as st
import time
from datetime import datetime, timezone, timedelta

from firebase_config import (
    create_food_listing, get_donor_listings, get_all_listings,
    update_listing_status, log_transaction, GOOGLE_MAPS_API_KEY
)
from styles import get_css, render_food_card, render_kpi

st.set_page_config(page_title="Donor Dashboard · FoodBridge", page_icon="🍽️", layout="wide")
st.markdown(get_css(), unsafe_allow_html=True)

# ── Auth guard ────────────────────────────────────────────────
if not st.session_state.get("authenticated"):
    st.warning("Please sign in to access the Donor Dashboard.")
    st.page_link("app.py", label="← Back to Login")
    st.stop()

if st.session_state.get("user_role") not in ("donor", "admin"):
    st.warning("⚠️ This page is for Donors and Admins only.")
    st.page_link("app.py", label="← Go Home")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:0.8rem 0 1.2rem;">
        <div style="font-size:1.8rem;">🌉</div>
        <div style="font-size:1rem;font-weight:800;font-family:'Space Grotesk',sans-serif;
                    background:linear-gradient(135deg,#34D399,#6366F1);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">FoodBridge</div>
    </div>
    """, unsafe_allow_html=True)

    role_icon = {"admin": "🛡️", "donor": "🍽️", "receiver": "🤝"}.get(st.session_state.user_role, "👤")
    st.markdown(f"""
    <div class="sidebar-user">
        <div class="su-name">{role_icon} {st.session_state.user_name}</div>
        <div class="su-role">{st.session_state.user_role}</div>
    </div>
    """, unsafe_allow_html=True)

    st.page_link("app.py", label="🏠 Home")
    st.page_link("pages/01_Donor.py", label="🍽️ Donor Dashboard")
    st.page_link("pages/02_Receiver.py", label="🤝 Receiver Portal")
    if st.session_state.get("user_role") == "admin":
        st.page_link("pages/03_Admin.py", label="🛡️ Admin")
    st.page_link("pages/04_Route_Optimizer.py", label="🗺️ Route Optimizer")
    st.page_link("pages/05_Feedback.py", label="💬 Feedback")
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.switch_page("app.py")

# ── Page header ───────────────────────────────────────────────
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.5rem;flex-wrap:wrap;gap:0.8rem;">
    <div>
        <div class="section-title">🍽️ Donor Dashboard</div>
        <div class="section-sub">List your surplus food and track your impact in real time</div>
    </div>
    <div class="live-badge"><span class="pulse-dot"></span>REAL-TIME</div>
</div>
""", unsafe_allow_html=True)

# ── Donor KPIs ────────────────────────────────────────────────
uid  = st.session_state.uid
role = st.session_state.get("user_role", "donor")

# Admin sees ALL platform listings; donors see only their own
if role == "admin":
    my_listings = get_all_listings(200)
    listing_label = "All Platform"
else:
    my_listings = get_donor_listings(uid)
    listing_label = "My"

total_kg  = sum(l.get("quantity_kg", 0) for l in my_listings)
delivered = [l for l in my_listings if l["status"] == "delivered"]
active    = [l for l in my_listings if l["status"] in ("available", "requested", "in_transit")]

# Admin context banner
if role == "admin":
    st.markdown("""
    <div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.25);
                border-radius:12px;padding:0.7rem 1rem;margin-bottom:1rem;
                font-size:0.83rem;color:rgba(228,237,255,0.7);">
        🛡️ <b style="color:#818CF8;">Admin View</b> — Showing all platform listings.
        Donors only see their own submissions.
    </div>
    """, unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
with k1: st.markdown(render_kpi(f"{listing_label} Listings", str(len(my_listings)), "All time"), unsafe_allow_html=True)
with k2: st.markdown(render_kpi("Active Listings", str(len(active)), "Currently live"), unsafe_allow_html=True)
with k3: st.markdown(render_kpi("Meals Contributed", f"{int(total_kg * 2.5):,}", "Estimated"), unsafe_allow_html=True)
with k4: st.markdown(render_kpi("CO₂ Saved", f"{round(total_kg * 2.1, 1)} kg", "Environmental impact"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════
tab_label = "📋 All Listings" if role == "admin" else "📋 My Listings"
tab_list, tab_new, tab_map = st.tabs([tab_label, "➕ Add New Listing", "📍 Location Preview"])

# ════════════════════════════════════════════════════════════
# TAB 1 — MY LISTINGS
# ════════════════════════════════════════════════════════════
with tab_list:
    # Filter bar
    col_filter, col_sort = st.columns([2, 1])
    with col_filter:
        status_filter = st.selectbox("Filter by Status", ["All", "available", "requested", "in_transit", "delivered"])
    with col_sort:
        sort_by = st.selectbox("Sort By", ["Newest First", "Quantity (High→Low)"])

    filtered = my_listings
    if status_filter != "All":
        filtered = [l for l in filtered if l["status"] == status_filter]
    if sort_by == "Quantity (High→Low)":
        filtered.sort(key=lambda x: x.get("quantity_kg", 0), reverse=True)

    if not filtered:
        st.markdown("""<div class="glass-card" style="text-align:center;padding:3rem;">
            <div style="font-size:2.5rem;">🌾</div>
            <div style="font-weight:600;color:#34D399;margin-top:0.8rem;">No listings found</div>
            <div style="font-size:0.85rem;color:rgba(228,237,255,0.45);margin-top:0.4rem;">
                Use the <b>Add New Listing</b> tab to submit surplus food.
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        cols_per_row = 3
        rows = [filtered[i:i+cols_per_row] for i in range(0, len(filtered), cols_per_row)]
        for row in rows:
            grid = st.columns(cols_per_row)
            for col, listing in zip(grid, row):
                with col:
                    st.markdown(render_food_card(listing), unsafe_allow_html=True)
                    lid = listing["listing_id"]
                    status = listing["status"]

                    if status == "available":
                        if st.button("🗑️ Remove Listing", key=f"del_{lid}", use_container_width=True):
                            update_listing_status(lid, "delivered")  # soft delete → mark delivered
                            st.toast("Listing removed.", icon="✅")
                            time.sleep(0.8)
                            st.rerun()
                    elif status == "requested":
                        if st.button("✅ Confirm Handover", key=f"hov_{lid}", use_container_width=True):
                            update_listing_status(lid, "in_transit")
                            st.toast("Handover confirmed! Marked as in transit.", icon="🚚")
                            time.sleep(0.8)
                            st.rerun()
                    elif status == "in_transit":
                        if st.button("🏁 Mark Delivered", key=f"del_{lid}", use_container_width=True):
                            update_listing_status(lid, "delivered")
                            st.toast("Marked as delivered! Great work 🎉", icon="🍱")
                            time.sleep(0.8)
                            st.rerun()
                    else:
                        st.markdown("""<div style="font-size:0.78rem;color:rgba(228,237,255,0.35);
                            padding:0.4rem;text-align:center;">✓ Completed</div>""",
                            unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# TAB 2 — ADD NEW LISTING
# ════════════════════════════════════════════════════════════
with tab_new:
    st.markdown("""<div class="glass-card" style="margin-bottom:1.5rem;">
        <div style="font-size:1.1rem;font-weight:700;margin-bottom:0.8rem;color:#34D399;">
            📦 Submit Surplus Food Listing
        </div>
        <div style="font-size:0.82rem;color:rgba(228,237,255,0.5);">
            Fill in the details below. Your listing will be <b style="color:#fff;">immediately visible</b>
            to receivers and NGOs on the platform.
        </div>
    </div>""", unsafe_allow_html=True)

    with st.form("add_listing_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            food_name  = st.text_input("Food Name *", placeholder="e.g. Fresh Bread, Cooked Dal, Seasonal Fruits")
            food_type  = st.selectbox("Food Type *", [
                "Bakery", "Prepared Meals", "Produce", "Dairy",
                "Seafood", "Grains", "Fruits", "Snacks", "Mixed"
            ])
            quantity   = st.number_input("Quantity (kg) *", min_value=0.1, max_value=5000.0, value=5.0, step=0.5)
            servings   = st.number_input("Estimated Servings", min_value=1, max_value=10000, value=int(quantity * 2.5))

        with col_b:
            address    = st.text_input("Pickup Address *", placeholder="Full address with city")
            pickup_win = st.selectbox("Pickup Window", [
                "Morning (6am–12pm)", "Afternoon (12pm–5pm)", "Evening (5pm–9pm)", "Flexible (Anytime)"
            ])
            expiry_hrs = st.slider("Food Safe For (hours)", 1, 72, 8)
            premium    = st.checkbox("⚡ Enable Priority Pickup (+$4.99 platform fee)",
                                     help="Logistics partners prioritize premium pickups")

        description = st.text_area("Description", placeholder="Add details about quantity, condition, packaging, etc.", height=90)
        tags_input  = st.text_input("Tags (comma-separated)", placeholder="veg, hot-food, packaged")

        # Location coordinates (auto-fill via Google Maps or manual)
        st.markdown("**📍 Pickup Location Coordinates**")
        col_lat, col_lng = st.columns(2)
        with col_lat:
            lat = st.number_input("Latitude", value=19.0760, format="%.4f")
        with col_lng:
            lng = st.number_input("Longitude", value=72.8777, format="%.4f")

        submit = st.form_submit_button("🚀 Publish Listing", use_container_width=True)

    if submit:
        if not food_name or not address:
            st.error("Please fill in Food Name and Pickup Address.")
        else:
            tags = [t.strip() for t in tags_input.split(",") if t.strip()]
            expiry_dt = (datetime.now(timezone.utc) + timedelta(hours=expiry_hrs)).isoformat()
            data = {
                "donor_id":     uid,
                "donor_name":   st.session_state.user_name,
                "food_name":    food_name,
                "food_type":    food_type,
                "quantity_kg":  quantity,
                "servings":     servings,
                "description":  description,
                "address":      address,
                "lat":          lat,
                "lng":          lng,
                "expiry_dt":    expiry_dt,
                "pickup_window": pickup_win,
                "tags":          tags,
                "premium_pickup": premium,
            }
            with st.spinner("Publishing your listing to Firestore…"):
                listing_id = create_food_listing(data)
                if premium:
                    log_transaction(uid, 4.99, "logistics_fee", {"listing_id": listing_id})

            st.success(f"""
            ✅ **Listing Published!** Listing ID: `{listing_id}`
            Your surplus food is now live and visible to all receivers on the platform.
            """)
            st.balloons()


# ════════════════════════════════════════════════════════════
# TAB 3 — MAP PREVIEW
# ════════════════════════════════════════════════════════════
with tab_map:
    st.markdown("""<div class="section-sub">
        Preview the location of your food listings on the map.
        Powered by Google Maps API.
    </div>""", unsafe_allow_html=True)

    if not my_listings:
        st.info("No listings to show on map yet. Add a listing first.", icon="📍")
    else:
        # Build interactive map using Google Maps embed or folium fallback
        try:
            import folium
            from streamlit_folium import st_folium

            m = folium.Map(
                location=[my_listings[0].get("lat", 19.076), my_listings[0].get("lng", 72.877)],
                zoom_start=10,
                tiles="CartoDB dark_matter",
            )
            status_colors = {
                "available": "green", "requested": "orange",
                "in_transit": "blue", "delivered": "gray"
            }
            for listing in my_listings:
                lat_ = listing.get("lat", 0)
                lng_ = listing.get("lng", 0)
                if lat_ and lng_:
                    folium.Marker(
                        [lat_, lng_],
                        popup=f"""<b>{listing.get('food_name','')}</b><br>
                            {listing.get('quantity_kg',0)} kg · {listing.get('status','')}<br>
                            {listing.get('address','')}""",
                        icon=folium.Icon(
                            color=status_colors.get(listing.get("status","available"), "green"),
                            icon="leaf", prefix="fa"
                        )
                    ).add_to(m)

            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            st_folium(m, width="100%", height=450)
            st.markdown('</div>', unsafe_allow_html=True)

        except ImportError:
            # Fallback: table view of coordinates
            st.warning("Install `folium` and `streamlit-folium` for interactive maps.", icon="🗺️")
            import pandas as pd
            map_data = [{"Food": l.get("food_name"), "lat": l.get("lat"), "lon": l.get("lng"),
                         "Status": l.get("status"), "Qty (kg)": l.get("quantity_kg")}
                        for l in my_listings if l.get("lat") and l.get("lng")]
            if map_data:
                df = pd.DataFrame(map_data)
                st.map(df)
