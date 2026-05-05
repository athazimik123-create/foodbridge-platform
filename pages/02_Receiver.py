# ============================================================
# pages/02_Receiver.py — Receiver / NGO Portal
# ============================================================
# Receivers can:
#  • Browse available food listings in real time
#  • Filter by food type, quantity, proximity
#  • Request food pickups (with optional premium)
#  • Track status of their requests
# ============================================================

import streamlit as st
st.set_page_config(page_title="Receiver Portal · FoodBridge", page_icon="🤝", layout="wide")

import time
from datetime import datetime, timezone

from firebase_config import (
    get_available_listings, get_all_listings, request_food,
    get_receiver_requests, log_transaction, get_user_notifications
)
from styles import get_css, render_food_card, render_kpi

st.markdown(get_css(), unsafe_allow_html=True)

# ── Auth guard ────────────────────────────────────────────────
if not st.session_state.get("authenticated"):
    st.warning("Please sign in to access the Receiver Portal.")
    st.page_link("app.py", label="← Back to Login")
    st.stop()

if st.session_state.get("user_role") not in ("receiver", "admin"):
    st.warning("⚠️ This page is for Receivers and Admins only.")
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

    st.markdown("### 🔍 Filters")
    food_filter = st.selectbox("Food Type", [
        "All", "Bakery", "Prepared Meals", "Produce",
        "Dairy", "Seafood", "Grains", "Fruits", "Snacks", "Mixed"
    ])
    min_qty  = st.number_input("Min Quantity (kg)", min_value=0.0, value=0.0, step=1.0)
    auto_ref = st.checkbox("🔄 Auto-refresh (30s)", value=True)

    st.markdown("<hr>", unsafe_allow_html=True)
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
now_str = datetime.now(timezone.utc).strftime("%H:%M UTC")
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.5rem;flex-wrap:wrap;gap:0.8rem;">
    <div>
        <div class="section-title">🤝 Receiver Portal</div>
        <div class="section-sub">Browse & request surplus food in real time · Updated {now_str}</div>
    </div>
    <div class="live-badge"><span class="pulse-dot"></span>LIVE LISTINGS</div>
</div>
""", unsafe_allow_html=True)

# ── Fetch & filter ────────────────────────────────────────────
uid  = st.session_state.uid
role = st.session_state.get("user_role", "receiver")

# Available listings (all roles see the same available food)
all_avail = get_available_listings(80)

# Admin sees ALL requests across platform; receivers see only their own
if role == "admin":
    my_reqs = [l for l in get_all_listings(200) if l.get("receiver_id")]
    req_label = "All Platform"
else:
    my_reqs = get_receiver_requests(uid)
    req_label = "My"

# Apply filters
filtered = all_avail
if food_filter != "All":
    filtered = [l for l in filtered if l.get("food_type","") == food_filter]
if min_qty > 0:
    filtered = [l for l in filtered if l.get("quantity_kg", 0) >= min_qty]

# KPIs
total_avail_kg = sum(l.get("quantity_kg", 0) for l in filtered)
my_active      = [r for r in my_reqs if r.get("status") in ("requested", "in_transit")]
my_delivered   = [r for r in my_reqs if r.get("status") == "delivered"]

# Admin context banner
if role == "admin":
    st.markdown("""
    <div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.25);
                border-radius:12px;padding:0.7rem 1rem;margin-bottom:1rem;
                font-size:0.83rem;color:rgba(228,237,255,0.7);">
        🛡️ <b style="color:#818CF8;">Admin View</b> — Showing all platform requests in the
        <b>My Requests</b> tab. Browse Listings and Food Map are the same for all roles.
    </div>
    """, unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
with k1: st.markdown(render_kpi("Available Now", str(len(filtered)), "Listings"), unsafe_allow_html=True)
with k2: st.markdown(render_kpi("Total Kg Available", f"{total_avail_kg:.1f}", "Ready for pickup"), unsafe_allow_html=True)
with k3: st.markdown(render_kpi(f"{req_label} Active Reqs", str(len(my_active)), "In progress"), unsafe_allow_html=True)
with k4: st.markdown(render_kpi("Meals via Requests", f"{int(sum(l.get('quantity_kg',0) for l in my_delivered)*2.5):,}", "All time"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════
req_tab_label = "📦 All Requests" if role == "admin" else "📦 My Requests"
tab_browse, tab_myreq, tab_map, tab_notifs, tab_subs = st.tabs([
    "🥬 Browse Listings", req_tab_label, "🗺️ Food Map", "🔔 Notifications", "💳 Subscription Plans"
])


# ════════════════════════════════════════════════════════════
# TAB 1 — BROWSE LISTINGS
# ════════════════════════════════════════════════════════════
with tab_browse:
    if not filtered:
        st.markdown("""<div class="glass-card" style="text-align:center;padding:3rem;">
            <div style="font-size:2.5rem;">🌾</div>
            <div style="font-weight:600;color:#34D399;margin-top:0.8rem;">No listings available right now</div>
            <div style="font-size:0.85rem;color:rgba(228,237,255,0.45);margin-top:0.4rem;">
                Try adjusting your filters or check back soon.
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        claimed_in_session = st.session_state.get("claimed_ids", set())

        cols_per_row = 3
        rows = [filtered[i:i+cols_per_row] for i in range(0, len(filtered), cols_per_row)]
        for row in rows:
            grid = st.columns(cols_per_row)
            for col, listing in zip(grid, row):
                with col:
                    lid = listing["listing_id"]
                    already_claimed = lid in claimed_in_session

                    st.markdown(render_food_card(listing), unsafe_allow_html=True)

                    # Premium option
                    prem_key = f"prem_{lid}"
                    is_premium = st.checkbox("⚡ Priority Pickup +₹499", key=prem_key,
                                             help="Priority matching with nearest logistics driver")

                    if role == "admin":
                        # Admin monitors but does not claim food
                        st.markdown("""<div style="font-size:0.78rem;color:rgba(228,237,255,0.35);
                            padding:0.4rem;text-align:center;">
                            🛡️ Admin view — claim disabled
                        </div>""", unsafe_allow_html=True)
                    elif already_claimed:
                        st.markdown("""<div style="font-size:0.82rem;color:#34D399;
                            padding:0.5rem;text-align:center;font-weight:600;">✅ Requested this session</div>""",
                            unsafe_allow_html=True)
                    else:
                        if st.button("🙋 Request This Food", key=f"req_{lid}", use_container_width=True):
                            request_food(lid, uid, premium=is_premium)
                            if is_premium:
                                log_transaction(uid, 499.0, "logistics_fee", {"listing_id": lid})
                            if "claimed_ids" not in st.session_state:
                                st.session_state.claimed_ids = set()
                            st.session_state.claimed_ids.add(lid)
                            st.success(f"✅ Food requested! {'Priority pickup enabled.' if is_premium else 'Donor will be notified.'}")
                            time.sleep(1)
                            st.rerun()


# ════════════════════════════════════════════════════════════
# TAB 2 — MY REQUESTS
# ════════════════════════════════════════════════════════════
with tab_myreq:
    if not my_reqs:
        empty_msg = "No food requests on the platform yet." if role == "admin" else "You haven't requested any food yet."
        st.markdown(f"""<div class="glass-card" style="text-align:center;padding:2.5rem;">
            <div style="font-size:2rem;">📭</div>
            <div style="color:rgba(228,237,255,0.5);margin-top:0.6rem;">{empty_msg}</div>
        </div>""", unsafe_allow_html=True)
    else:
        status_order = {"requested": 0, "in_transit": 1, "available": 2, "delivered": 3}
        my_reqs.sort(key=lambda x: status_order.get(x.get("status",""), 99))

        for req in my_reqs:
            status = req.get("status", "")
            badge_cls = {
                "available": "badge-green", "requested": "badge-orange",
                "in_transit": "badge-blue", "delivered": "badge-purple"
            }.get(status, "badge-green")

            status_icon = {
                "available": "🟢", "requested": "🟡",
                "in_transit": "🚚", "delivered": "✅"
            }.get(status, "⚪")

            prem_badge = '<span class="badge badge-orange">⚡ Priority</span>' if req.get("premium_pickup") else ""
            created_at = req.get("created_at", "")
            if hasattr(created_at, "strftime"):
                created_at = created_at.strftime("%b %d, %H:%M")
            else:
                created_at = str(created_at)[:16]

            st.markdown(f"""
            <div class="glass-card" style="margin-bottom:0.9rem;padding:1.2rem 1.4rem;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:0.5rem;">
                    <div>
                        <div style="font-size:1rem;font-weight:700;color:#fff;">
                            {status_icon} {req.get('food_name','Unknown Food')}
                        </div>
                        <div style="font-size:0.81rem;color:rgba(228,237,255,0.5);margin-top:0.2rem;">
                            {req.get('food_type','Mixed')} · {req.get('quantity_kg',0)} kg ·
                            From: {req.get('donor_name','Unknown')}
                        </div>
                        <div style="font-size:0.76rem;color:rgba(228,237,255,0.35);margin-top:0.3rem;">
                            📍 {req.get('address','')[:55]} &nbsp;·&nbsp; Requested: {created_at}
                        </div>
                    </div>
                    <div style="display:flex;gap:0.4rem;flex-wrap:wrap;align-items:flex-start;">
                        <span class="badge {badge_cls}">{status}</span>
                        {prem_badge}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# TAB 3 — FOOD MAP
# ════════════════════════════════════════════════════════════
with tab_map:
    st.markdown("""<div class="section-sub">
        All available food listings near you. Click a marker for details.
    </div>""", unsafe_allow_html=True)

    map_data = [l for l in all_avail if l.get("lat") and l.get("lng")]

    if not map_data:
        st.info("No geo-tagged listings available right now.", icon="📍")
    else:
        try:
            import folium
            from streamlit_folium import st_folium

            center_lat = map_data[0].get("lat", 19.076)
            center_lng = map_data[0].get("lng", 72.877)
            m = folium.Map(location=[center_lat, center_lng], zoom_start=10,
                           tiles="CartoDB dark_matter")

            for listing in map_data:
                lat_ = listing.get("lat", 0)
                lng_ = listing.get("lng", 0)
                if lat_ and lng_:
                    prem = "⚡ Priority" if listing.get("premium_pickup") else ""
                    folium.Marker(
                        [lat_, lng_],
                        popup=folium.Popup(f"""
                            <b style='font-size:13px'>{listing.get('food_name','')}</b><br>
                            <i>{listing.get('food_type','')} · {listing.get('quantity_kg',0)} kg</i><br>
                            📍 {listing.get('address','')}<br>
                            🕐 {listing.get('pickup_window','')}<br>
                            {prem}
                        """, max_width=250),
                        tooltip=f"🥗 {listing.get('food_name','')} — {listing.get('quantity_kg',0)} kg",
                        icon=folium.Icon(color="green", icon="leaf", prefix="fa")
                    ).add_to(m)

            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            st_folium(m, width="100%", height=500)
            st.markdown('</div>', unsafe_allow_html=True)

        except ImportError:
            st.warning("Install `folium` and `streamlit-folium` for interactive maps.", icon="🗺️")
            import pandas as pd
            df_map = pd.DataFrame([
                {"lat": l["lat"], "lon": l["lng"]}
                for l in map_data if l.get("lat") and l.get("lng")
            ])
            if not df_map.empty:
                st.map(df_map)

# ════════════════════════════════════════════════════════════
# TAB 4 — NOTIFICATIONS
# ════════════════════════════════════════════════════════════
with tab_notifs:
    st.markdown("### 🔔 Notification Center")
    notifs = get_user_notifications(uid)
    
    if not notifs:
        st.info("No new notifications.", icon="📭")
    else:
        for n in notifs:
            is_read = n.get("read", False)
            bg_color = "rgba(52,211,153,0.1)" if not is_read else "rgba(255,255,255,0.05)"
            icon = "🚨" if n.get("type") == "system" else "🥗"
            time_str = str(n.get("created_at", ""))[:16]
            
            st.markdown(f"""
            <div class="glass-card" style="background:{bg_color}; padding:1rem 1.5rem; margin-bottom:0.8rem; border-left: 4px solid #34D399;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div style="font-weight:700; font-size:1.05rem;">{icon} {n.get('title')}</div>
                        <div style="color:rgba(228,237,255,0.8); margin-top:0.3rem; font-size:0.9rem;">{n.get('message')}</div>
                    </div>
                    <div style="font-size:0.75rem; color:rgba(228,237,255,0.4);">{time_str}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# TAB 5 — SUBSCRIPTIONS & RAZORPAY
# ════════════════════════════════════════════════════════════
with tab_subs:
    st.markdown("### 💳 Receiver Subscription Plans")
    st.markdown("Choose a plan to upgrade your limits and logistics options.")
    
    col_basic, col_pro = st.columns(2)
    
    with col_basic:
        st.markdown("""
        <div class="glass-card" style="padding:2rem; text-align:center; height:100%;">
            <div style="font-size:1.5rem; font-weight:700; color:#fff;">Basic Plan</div>
            <div style="font-size:2rem; font-weight:900; color:#34D399; margin:1rem 0;">Free</div>
            <div style="text-align:left; color:rgba(228,237,255,0.7); font-size:0.9rem; line-height:1.8;">
                ✓ Browse available listings<br>
                ✓ Standard pickup matching<br>
                ✓ Basic metrics<br>
                ✗ Priority route assignment<br>
                ✗ Dedicated support
            </div>
            <div style="margin-top:2rem; padding:0.6rem; border:1px solid #34D399; color:#34D399; border-radius:8px;">Current Plan</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_pro:
        st.markdown("""
        <div class="glass-card" style="padding:2rem; text-align:center; height:100%; border:1px solid #818CF8; background:rgba(99,102,241,0.05);">
            <div style="font-size:1.5rem; font-weight:700; color:#fff;">Pro Plan</div>
            <div style="font-size:2rem; font-weight:900; color:#818CF8; margin:1rem 0;">₹2,999 <span style="font-size:0.9rem;color:#ccc;">/ month</span></div>
            <div style="text-align:left; color:rgba(228,237,255,0.7); font-size:0.9rem; line-height:1.8;">
                ✓ Browse available listings<br>
                ✓ Premium priority pickup matching<br>
                ✓ Advanced metrics & API access<br>
                ✓ Priority route assignment<br>
                ✓ 24/7 dedicated support
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Razorpay Simulation (Streamlit HTML Component)
        import streamlit.components.v1 as components
        
        # We simulate the Razorpay script here using a generic button for demo purposes
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Upgrade to Pro (Pay with Razorpay)", use_container_width=True, type="primary"):
            st.session_state.show_razorpay = True
            
        if st.session_state.get("show_razorpay"):
            st.info("Simulating Razorpay payment flow...")
            # Note: For a real Razorpay integration, we'd inject their standard <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
            # and pass the order_id created by razorpay python SDK on the backend.
            time.sleep(2)
            log_transaction(uid, 2999.0, "subscription", {"tier": "pro"})
            st.success("✅ Payment successful! You are now subscribed to the Pro Plan.")
            st.balloons()
            st.session_state.show_razorpay = False
            time.sleep(1.5)
            st.rerun()

# ── Auto-refresh ─────────────────────────────────────────────
if auto_ref:
    st.markdown("""<div style="font-size:0.73rem;color:rgba(228,237,255,0.28);text-align:center;margin-top:2rem;">
        🔄 Auto-refreshing every 30 seconds for live data
    </div>""", unsafe_allow_html=True)
    time.sleep(30)
    st.rerun()
