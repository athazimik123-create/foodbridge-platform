# ============================================================
# app.py — FoodBridge: Community Surplus Food Redistribution
# ============================================================
# Run:  streamlit run app.py
#
# Demo credentials (mock mode):
#   admin@foodbridge.com    / demo1234
#   donor@foodbridge.com    / demo1234
#   receiver@foodbridge.com / demo1234
# ============================================================

import streamlit as st

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="FoodBridge — Community Food Redistribution",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded",
)

from datetime import datetime, timezone
from firebase_config import sign_in, sign_up, FIREBASE_WEB_API_KEY
from styles import get_css


st.markdown(get_css(), unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────
_DEFAULTS = {
    "authenticated": False,
    "id_token":      None,
    "uid":           None,
    "user_role":     None,
    "user_name":     None,
    "user_email":    None,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

IS_MOCK = (FIREBASE_WEB_API_KEY == "DEMO_KEY")


# ════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        # Logo
        st.markdown("""
        <div style="text-align:center;padding:1rem 0 1.5rem;">
            <div style="font-size:2.4rem;filter:drop-shadow(0 0 14px rgba(52,211,153,0.55));">🌉</div>
            <div style="font-size:1.35rem;font-weight:800;font-family:'Space Grotesk',sans-serif;
                        background:linear-gradient(135deg,#34D399,#6366F1);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                FoodBridge
            </div>
            <div style="font-size:0.68rem;color:rgba(228,237,255,0.38);letter-spacing:0.12em;text-transform:uppercase;">
                Community Food Rescue
            </div>
        </div>
        """, unsafe_allow_html=True)

        # User card
        role_icon = {"admin": "🛡️", "donor": "🍽️", "receiver": "🤝"}.get(
            st.session_state.user_role, "👤"
        )
        st.markdown(f"""
        <div class="sidebar-user">
            <div class="su-name">{role_icon} {st.session_state.user_name}</div>
            <div class="su-role">{st.session_state.user_role}</div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        st.markdown("**Navigation**")
        st.page_link("app.py", label="🏠 Home Dashboard")

        role = st.session_state.user_role
        if role in ("donor", "admin"):
            st.page_link("pages/01_Donor.py", label="🍽️ Donor Dashboard")
        if role in ("receiver", "admin"):
            st.page_link("pages/02_Receiver.py", label="🤝 Receiver Portal")
        if role == "admin":
            st.page_link("pages/03_Admin.py", label="🛡️ Admin Dashboard")
        st.page_link("pages/04_Route_Optimizer.py", label="🗺️ Route Optimizer")
        st.page_link("pages/05_Feedback.py", label="💬 Feedback")

        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("🚪 Sign Out", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ════════════════════════════════════════════════════════════
# LOGIN PAGE
# ════════════════════════════════════════════════════════════

def render_login():
    # Animated particles (CSS)
    st.markdown("""
    <style>
    @keyframes rise { 0%{transform:translateY(0) rotate(0);opacity:.5} 100%{transform:translateY(-100vh) rotate(540deg);opacity:0} }
    .pt { position:fixed; border-radius:50%; pointer-events:none; z-index:0; background:rgba(52,211,153,0.1); animation:rise linear infinite; }
    @keyframes fadeIn { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
    .login-panel { animation: fadeIn 0.35s ease; }
    </style>
    <div class="pt" style="width:7px;height:7px;left:12%;bottom:-20px;animation-duration:17s;"></div>
    <div class="pt" style="width:4px;height:4px;left:33%;bottom:-20px;animation-duration:21s;animation-delay:4s;"></div>
    <div class="pt" style="width:9px;height:9px;left:58%;bottom:-20px;animation-duration:15s;animation-delay:8s;"></div>
    <div class="pt" style="width:5px;height:5px;left:78%;bottom:-20px;animation-duration:19s;animation-delay:2s;"></div>
    <div class="pt" style="width:6px;height:6px;left:90%;bottom:-20px;animation-duration:23s;animation-delay:6s;background:rgba(99,102,241,0.12);"></div>
    """, unsafe_allow_html=True)

    # Initialise show-form toggle
    if "show_login_form" not in st.session_state:
        st.session_state.show_login_form = False

    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        # ── Hero section ────────────────────────────────────────
        st.markdown("""
        <div style="text-align:center;padding:2.5rem 0 1.8rem;">
            <div style="font-size:3.5rem;filter:drop-shadow(0 0 18px rgba(52,211,153,0.6));">🌉</div>
            <div style="font-size:2.2rem;font-weight:900;font-family:'Space Grotesk',sans-serif;
                        background:linear-gradient(135deg,#34D399,#6366F1);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-top:0.4rem;">
                FoodBridge
            </div>
            <div style="font-size:0.9rem;color:rgba(228,237,255,0.5);margin-top:0.5rem;line-height:1.6;">
                Connecting surplus food with communities who need it.<br>
                <span style="color:#34D399;font-weight:600;">Zero waste. Real impact.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Feature tiles ────────────────────────────────────────
        f1, f2, f3 = st.columns(3)
        tiles = [
            ("🍽️", "#34D399", "Donate Food", "List surplus food instantly"),
            ("🤝", "#6366F1", "Receive Food", "NGOs & individuals request"),
            ("🗺️", "#FB923C", "Route Optimize", "AI-powered delivery routes"),
        ]
        for fcol, (em, color, title, sub) in zip([f1, f2, f3], tiles):
            with fcol:
                fcol.markdown(f"""<div class="glass-card" style="text-align:center;padding:1rem;">
                    <div style="font-size:1.6rem;">{em}</div>
                    <div style="font-size:0.75rem;font-weight:700;color:{color};margin-top:0.4rem;">{title}</div>
                    <div style="font-size:0.68rem;color:rgba(228,237,255,0.4);margin-top:0.2rem;">{sub}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Login button (CTA) ───────────────────────────────────
        if not st.session_state.show_login_form:
            btn_label = "🔐 Sign In to FoodBridge"
            if st.button(btn_label, use_container_width=True, key="open_login_btn"):
                st.session_state.show_login_form = True
                st.rerun()

            st.markdown("""
            <div style="text-align:center;font-size:0.75rem;color:rgba(228,237,255,0.3);margin-top:0.6rem;">
                New here? Click Sign In → Register tab to create a free account.
            </div>
            """, unsafe_allow_html=True)

        # ── Login / Register panel (shown after button click) ───
        if st.session_state.show_login_form:
            st.markdown('<div class="login-panel">', unsafe_allow_html=True)

            # Demo / Live mode banner
            if IS_MOCK:
                st.markdown("""
                <div style="background:rgba(52,211,153,0.07);border:1px solid rgba(52,211,153,0.2);
                            border-radius:12px;padding:0.85rem 1rem;margin-bottom:1.2rem;
                            font-size:0.82rem;color:rgba(228,237,255,0.7);">
                    🔑 <b style="color:#34D399;">Demo Mode</b> — Password: <code>demo1234</code><br>
                    <code>admin@foodbridge.com</code> &nbsp;·&nbsp;
                    <code>donor@foodbridge.com</code> &nbsp;·&nbsp;
                    <code>receiver@foodbridge.com</code>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.2);
                            border-radius:12px;padding:0.85rem 1rem;margin-bottom:1.2rem;
                            font-size:0.82rem;color:rgba(228,237,255,0.7);">
                    🔥 <b style="color:#818CF8;">Live Mode</b> — Connected to Firebase.
                </div>
                """, unsafe_allow_html=True)

            tab_in, tab_up = st.tabs(["🔐 Sign In", "✨ Register"])

            # ── SIGN IN ──────────────────────────────────────────
            with tab_in:
                with st.form("signin_form", clear_on_submit=False):
                    email = st.text_input("Email", placeholder="you@example.com", key="si_email")
                    pw    = st.text_input("Password", type="password", placeholder="••••••••", key="si_pw")
                    submitted = st.form_submit_button("Sign In →", use_container_width=True)

                if submitted:
                    if not email or not pw:
                        st.error("Please enter email and password.")
                    else:
                        with st.spinner("Authenticating…"):
                            res = sign_in(email, pw)
                        if "error" in res:
                            st.error(f"❌ {res['error']}")
                            if any(x in res["error"] for x in ["INVALID", "EMAIL_NOT_FOUND"]):
                                st.info("💡 No account? Switch to the **✨ Register** tab.", icon="ℹ️")
                        else:
                            st.session_state.authenticated = True
                            st.session_state.id_token   = res.get("idToken")
                            st.session_state.uid        = res.get("localId")
                            st.session_state.user_role  = res.get("role", "receiver")
                            st.session_state.user_name  = res.get("name", email.split("@")[0])
                            st.session_state.user_email = email
                            st.session_state.show_login_form = False
                            st.success(f"Welcome, {st.session_state.user_name}! 🎉")
                            st.rerun()

            # ── REGISTER ─────────────────────────────────────────
            with tab_up:
                if IS_MOCK:
                    st.info("Account creation requires a real Firebase project.", icon="🔒")
                else:
                    with st.form("register_form", clear_on_submit=True):
                        r_name  = st.text_input("Full Name", key="r_name")
                        r_email = st.text_input("Email", key="r_email")
                        r_role  = st.selectbox("I am a…", options=["donor", "receiver"],
                                               format_func=lambda x: {"donor": "🍽️ Donor", "receiver": "🤝 Receiver (NGO/Individual)"}[x])
                        r_pw   = st.text_input("Password (min 6 chars)", type="password", key="r_pw")
                        r_pw2  = st.text_input("Confirm Password", type="password", key="r_pw2")
                        r_sub  = st.form_submit_button("Create Account →", use_container_width=True)

                    if r_sub:
                        if not all([r_name, r_email, r_pw, r_pw2]):
                            st.error("All fields are required.")
                        elif r_pw != r_pw2:
                            st.error("Passwords do not match.")
                        elif len(r_pw) < 6:
                            st.error("Password must be at least 6 characters.")
                        else:
                            with st.spinner("Creating account…"):
                                res = sign_up(r_email, r_pw, r_name, r_role)
                            if "error" in res:
                                st.error(f"❌ {res['error']}")
                            else:
                                st.session_state.authenticated = True
                                st.session_state.id_token   = res.get("idToken")
                                st.session_state.uid        = res.get("localId")
                                st.session_state.user_role  = r_role
                                st.session_state.user_name  = r_name
                                st.session_state.user_email = r_email
                                st.session_state.show_login_form = False
                                st.success(f"🎉 Welcome to FoodBridge, {r_name}!")
                                st.rerun()

            # Back link
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("← Back", key="hide_login_btn", use_container_width=False):
                st.session_state.show_login_form = False
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# HOME DASHBOARD
# ════════════════════════════════════════════════════════════

def render_home():
    render_sidebar()

    from firebase_config import get_platform_stats, get_available_listings

    stats    = get_platform_stats()
    listings = get_available_listings(6)
    now_str  = datetime.now(timezone.utc).strftime("%b %d, %Y · %H:%M UTC")

    # Header
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2rem;flex-wrap:wrap;gap:1rem;">
        <div>
            <div class="section-title">Welcome back, {st.session_state.user_name} 👋</div>
            <div class="section-sub">FoodBridge Platform Overview · {now_str}</div>
        </div>
        <div class="live-badge"><span class="pulse-dot"></span>LIVE DATA</div>
    </div>
    """, unsafe_allow_html=True)

    # KPI Row
    k1, k2, k3, k4, k5 = st.columns(5)
    kpis = [
        ("🥗 Listings", str(stats["total_listings"]), "Total submitted"),
        ("✅ Available", str(stats["available"]), "Ready to claim"),
        ("🚚 In Transit", str(stats["requested"]), "Being picked up"),
        ("🍱 Meals Saved", f"{stats['meals_saved']:,}", "Estimated"),
        ("💚 CO₂ Offset", f"{stats['co2_offset_kg']} kg", "Carbon saved"),
    ]
    from styles import render_kpi
    for col, (label, value, sub) in zip([k1, k2, k3, k4, k5], kpis):
        with col:
            col.markdown(render_kpi(label, value, sub), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Revenue + Quick Actions
    col_left, col_right = st.columns([1.7, 1])

    with col_left:
        st.markdown("""<div class="section-title" style="font-size:1.1rem;">🥬 Latest Available Food</div>
        <div class="section-sub">Real-time listings from donors — updated automatically</div>""",
        unsafe_allow_html=True)

        if not listings:
            st.markdown("""<div class="glass-card" style="text-align:center;padding:2rem;">
                <div style="font-size:2rem;">🌾</div>
                <div style="color:rgba(228,237,255,0.5);margin-top:0.6rem;">No listings available right now.</div>
            </div>""", unsafe_allow_html=True)
        else:
            from styles import render_food_card
            grid_cols = st.columns(2)
            for i, listing in enumerate(listings[:6]):
                with grid_cols[i % 2]:
                    st.markdown(render_food_card(listing), unsafe_allow_html=True)

    with col_right:
        st.markdown("""<div class="section-title" style="font-size:1.1rem;">⚡ Quick Actions</div>
        <div class="section-sub">Jump to your module</div>""", unsafe_allow_html=True)

        role = st.session_state.user_role
        actions = []
        if role in ("donor", "admin"):
            actions.append(("🍽️", "Donor Dashboard", "List surplus food", "pages/01_Donor.py"))
        if role in ("receiver", "admin"):
            actions.append(("🤝", "Receiver Portal", "Request available food", "pages/02_Receiver.py"))
        if role == "admin":
            actions.append(("🛡️", "Admin Console", "Monitor platform", "pages/03_Admin.py"))
        actions.append(("🗺️", "Route Optimizer", "Plan delivery routes", "pages/04_Route_Optimizer.py"))

        for em, title, sub, page in actions:
            st.markdown(f"""<div class="glass-card" style="margin-bottom:0.7rem;padding:1rem;">
                <div style="font-size:1.3rem;">{em}</div>
                <div style="font-weight:700;font-size:0.95rem;margin-top:0.3rem;">{title}</div>
                <div style="font-size:0.76rem;color:rgba(228,237,255,0.45);margin-top:0.2rem;">{sub}</div>
            </div>""", unsafe_allow_html=True)
            st.page_link(page, label=f"→ Open {title}")

        # Revenue summary (admin)
        if role == "admin":
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="glass-card" style="padding:1rem;background:rgba(52,211,153,0.06);">
                <div style="font-size:0.75rem;color:rgba(228,237,255,0.5);text-transform:uppercase;letter-spacing:0.08em;">Platform Revenue</div>
                <div style="font-size:1.8rem;font-weight:900;color:#34D399;font-family:'Space Grotesk',sans-serif;">
                    ₹{stats['total_revenue']:,.2f}
                </div>
                <div style="font-size:0.74rem;color:rgba(228,237,255,0.4);margin-top:0.2rem;">
                    💳 Subs: ₹{stats['sub_rev']:.2f} &nbsp;|&nbsp;
                    🚚 Logistics: ₹{stats['logistics_rev']:.2f} &nbsp;|&nbsp;
                    🌍 CSR: ₹{stats['csr_rev']:.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.page_link("pages/03_Admin.py", label="→ Full Revenue Dashboard")


# ════════════════════════════════════════════════════════════
# ROUTER
# ════════════════════════════════════════════════════════════

if st.session_state.authenticated:
    render_home()
else:
    render_login()
