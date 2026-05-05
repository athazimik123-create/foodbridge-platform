# ============================================================
# pages/05_Feedback.py — User Feedback
# ============================================================
# Allows users to submit feedback and rate their experience.
# ============================================================

import streamlit as st
st.set_page_config(page_title="Feedback · FoodBridge", page_icon="💬", layout="wide")

from firebase_config import submit_feedback
from styles import get_css

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
    </div>
    """, unsafe_allow_html=True)

    st.page_link("app.py", label="🏠 Home")
    role = st.session_state.user_role
    if role in ("donor", "admin"):
        st.page_link("pages/01_Donor.py", label="🍽️ Donor Dashboard")
    if role in ("receiver", "admin"):
        st.page_link("pages/02_Receiver.py", label="🤝 Receiver Portal")
    if role == "admin":
        st.page_link("pages/03_Admin.py", label="🛡️ Admin")
    st.page_link("pages/04_Route_Optimizer.py", label="🗺️ Route Optimizer")
    st.page_link("pages/05_Feedback.py", label="💬 Feedback")
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.switch_page("app.py")

# ── Header ───────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:1.5rem;">
    <div class="section-title">💬 Leave Feedback</div>
    <div class="section-sub">Help us improve FoodBridge</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("""
    <div class="glass-card" style="padding: 2rem;">
        <h3 style="margin-top:0; color:#34D399;">We'd love to hear from you!</h3>
        <p style="color:rgba(228,237,255,0.7); font-size:0.9rem;">
            Your feedback helps us make FoodBridge better for everyone. Whether it's a bug report, a feature request, or just saying hello, we appreciate it.
        </p>
    </div>
    <br>
    """, unsafe_allow_html=True)
    
    with st.form("feedback_form", clear_on_submit=True):
        rating = st.slider("⭐ How would you rate your experience?", 1, 5, 5)
        message = st.text_area("Your Feedback", placeholder="Tell us what you think...", height=150)
        
        submitted = st.form_submit_button("🚀 Submit Feedback", use_container_width=True)
        
        if submitted:
            if not message.strip():
                st.error("Please enter a message before submitting.")
            else:
                submit_feedback(
                    user_id=st.session_state.uid,
                    user_name=st.session_state.user_name,
                    role=st.session_state.user_role,
                    rating=rating,
                    message=message
                )
                st.success("🎉 Thank you! Your feedback has been submitted.")
                st.balloons()
