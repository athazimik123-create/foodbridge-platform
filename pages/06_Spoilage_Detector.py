# ============================================================
# pages/06_Spoilage_Detector.py — Smart Food Spoilage Detector
# ============================================================
# Uses a trained XGBoost model to predict food spoilage from
# IoT sensor readings (Temperature, Humidity, MQ gas sensors).
#
# Required files in the SAME folder as app.py:
#   • xgboost_model.pkl
#   • food_encoder.pkl
#   • label_encoder.pkl
# ============================================================

import streamlit as st
st.set_page_config(
    page_title="Spoilage Detector · FoodBridge",
    page_icon="🧪",
    layout="wide"
)

import numpy as np
import os
import pandas as pd
from styles import get_css, render_kpi

st.markdown(get_css(), unsafe_allow_html=True)

# ── Auth guard & Role guard ──────────────────────────────────
if not st.session_state.get("authenticated"):
    st.warning("Please sign in to access the Spoilage Detector.")
    st.page_link("app.py", label="← Back to Login")
    st.stop()

if st.session_state.get("user_role") not in ("admin", "donor"):
    st.error("🔒 Access Denied: Only administrators and donors can access this module.")
    st.page_link("app.py", label="🏠 Back to Home")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:0.8rem 0 1.2rem;">
        <div style="font-size:1rem;font-weight:800;font-family:'Space Grotesk',sans-serif;
                    background:linear-gradient(135deg,#34D399,#6366F1);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">FoodBridge</div>
    </div>
    """, unsafe_allow_html=True)

    role_icon = {"admin": "🛡️", "donor": "🍽️", "receiver": "🤝"}.get(
        st.session_state.get("user_role", ""), "👤"
    )
    st.markdown(f"""
    <div class="sidebar-user">
        <div class="su-name">{role_icon} {st.session_state.get("user_name", "")}</div>
        <div class="su-role">{st.session_state.get("user_role", "")}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ℹ️ About this Tool")
    st.markdown("""
    <div style="font-size:0.82rem;color:rgba(228,237,255,0.55);line-height:1.7;">
        This detector uses an <b style="color:#34D399;">XGBoost ML model</b>
        trained on IoT sensor data to predict whether food is
        <b style="color:#34D399;">Fresh ✅</b> or
        <b style="color:#F87171;">Spoiled ⚠️</b>.<br><br>
        Input readings from your gas sensors and the model
        will give you an instant prediction with confidence score.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.page_link("app.py",                        label="🏠 Home")
    if st.session_state.get("user_role") in ("donor", "admin"):
        st.page_link("pages/01_Donor.py",          label="🍽️ Donor Dashboard")
    if st.session_state.get("user_role") in ("receiver", "admin"):
        st.page_link("pages/02_Receiver.py",       label="🤝 Receiver Portal")
    if st.session_state.get("user_role") == "admin":
        st.page_link("pages/03_Admin.py",          label="🛡️ Admin Dashboard")
    st.page_link("pages/04_Route_Optimizer.py",    label="🗺️ Route Optimizer")
    st.page_link("pages/05_Feedback.py",           label="💬 Feedback")
    st.page_link("pages/06_Spoilage_Detector.py",  label="🧪 Spoilage Detector")
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.switch_page("app.py")


# ════════════════════════════════════════════════════════════
# PAGE HEADER
# ════════════════════════════════════════════════════════════
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;
            margin-bottom:1.5rem;flex-wrap:wrap;gap:0.8rem;">
    <div>
        <div class="section-title">🧪 Smart Food Spoilage Detector</div>
        <div class="section-sub">
            AI-powered freshness prediction using IoT gas sensor readings
        </div>
    </div>
    <div class="live-badge"><span class="pulse-dot"></span>ML ENGINE</div>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# LOAD MODEL — graceful error if files are missing
# ════════════════════════════════════════════════════════════
MODEL_FILES = {
    "model":            "xgboost_model.pkl",
    "shelf_life_model": "shelf_life_model.pkl",
    "food_encoder":     "food_encoder.pkl",
    "label_encoder":    "label_encoder.pkl",
}

@st.cache_resource(show_spinner="Loading ML models…")
def load_model_files():
    """Load all four pickled model artefacts exactly once."""
    import joblib
    model             = joblib.load(MODEL_FILES["model"])
    shelf_life_model  = joblib.load(MODEL_FILES["shelf_life_model"])
    food_encoder      = joblib.load(MODEL_FILES["food_encoder"])
    label_encoder     = joblib.load(MODEL_FILES["label_encoder"])
    return model, shelf_life_model, food_encoder, label_encoder


# Check that all four files exist before attempting to load
missing = [f for f in MODEL_FILES.values() if not os.path.exists(f)]

if missing:
    st.markdown(f"""
    <div style="background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.3);
                border-radius:14px;padding:1.5rem 1.8rem;margin-bottom:1.5rem;">
        <div style="font-size:1.1rem;font-weight:700;color:#F87171;margin-bottom:0.6rem;">
            ⚠️ Model Files Not Found
        </div>
        <div style="font-size:0.88rem;color:rgba(228,237,255,0.7);line-height:1.8;">
            The following files are missing from the app root directory:
            <ul style="margin-top:0.6rem;">
            {"".join(f"<li><code style='color:#F87171;'>{f}</code></li>" for f in missing)}
            </ul>
            <b style="color:#fff;">How to fix:</b><br>
            Run these lines at the end of your training notebook and place the
            generated <code>.pkl</code> files in the same folder as <code>app.py</code>:
            <pre style="background:rgba(0,0,0,0.3);border-radius:8px;padding:0.8rem;
                        margin-top:0.6rem;font-size:0.82rem;color:#34D399;">
import joblib
joblib.dump(xgb_model,        "xgboost_model.pkl")
joblib.dump(shelf_life_model, "shelf_life_model.pkl")
joblib.dump(food_encoder,     "food_encoder.pkl")
joblib.dump(label_encoder,    "label_encoder.pkl")</pre>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# All files present — load them
try:
    model, shelf_life_model, food_encoder, label_encoder = load_model_files()
    model_ready = True
except Exception as e:
    st.error(f"❌ Failed to load model files: {e}")
    st.stop()


# ════════════════════════════════════════════════════════════
# HOW IT WORKS EXPANDER
# ════════════════════════════════════════════════════════════
with st.expander("ℹ️ How the Spoilage Detector Works", expanded=False):
    st.markdown("""
    The **FoodBridge Spoilage Detector** uses an **XGBoost classifier** trained on
    IoT sensor readings to determine food freshness in real time.

    **Feature inputs (in training order):**
    | # | Feature | Description |
    |---|---------|-------------|
    | 1 | Temperature (°C) | Ambient or food surface temperature |
    | 2 | Humidity (%) | Relative humidity of storage environment |
    | 3 | MQ-2 | Smoke / LPG / combustible gas sensor |
    | 4 | MQ-4 | Methane / CNG sensor |
    | 5 | MQ-135 | Air quality / NH₃ / CO₂ sensor |
    | 6 | MQ-136 | Hydrogen sulfide (H₂S) sensor |
    | 7 | Food Type | Encoded food category |

    **Output:** Binary classification — `0 = Fresh`, `1 = Spoiled`  
    **Confidence:** Probability score from `predict_proba()` (0–100%)
    """)


# ════════════════════════════════════════════════════════════
# INPUT FORM
# ════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-title" style="font-size:1.1rem;margin-bottom:0.4rem;">
    📡 Enter Sensor Readings
</div>
<div class="section-sub" style="margin-bottom:1.2rem;">
    Fill in the values from your IoT sensors. All fields are required.
</div>
""", unsafe_allow_html=True)

with st.form("spoilage_form"):
    st.markdown("""
    <div style="background:rgba(52,211,153,0.04);border:1px solid rgba(52,211,153,0.15);
                border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:1.2rem;">
        <div style="font-size:0.82rem;font-weight:600;color:#34D399;
                    text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem;">
            🌡️ Environmental Sensors
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_env1, col_env2 = st.columns(2)
    with col_env1:
        temp = st.number_input(
            "🌡️ Temperature (°C)",
            min_value=-20.0, max_value=100.0,
            value=25.0, step=0.1,
            help="Ambient or surface temperature of the food storage area"
        )
    with col_env2:
        humidity = st.number_input(
            "💧 Humidity (%)",
            min_value=0.0, max_value=100.0,
            value=60.0, step=0.1,
            help="Relative humidity percentage (0–100%)"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:rgba(99,102,241,0.04);border:1px solid rgba(99,102,241,0.15);
                border-radius:12px;padding:1rem 1.4rem;margin-bottom:1rem;">
        <div style="font-size:0.82rem;font-weight:600;color:#818CF8;
                    text-transform:uppercase;letter-spacing:0.08em;">
            🔬 Gas Sensor Readings (MQ Series)
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    with col_g1:
        mq2 = st.number_input(
            "MQ-2 (Smoke/LPG)",
            min_value=0.0, max_value=5000.0,
            value=100.0, step=1.0,
            help="MQ-2 measures smoke, LPG, butane, propane, methane"
        )
    with col_g2:
        mq4 = st.number_input(
            "MQ-4 (Methane)",
            min_value=0.0, max_value=5000.0,
            value=100.0, step=1.0,
            help="MQ-4 measures methane and CNG gas concentration"
        )
    with col_g3:
        mq135 = st.number_input(
            "MQ-135 (Air Quality)",
            min_value=0.0, max_value=5000.0,
            value=100.0, step=1.0,
            help="MQ-135 measures NH₃, alcohol, benzene, CO₂"
        )
    with col_g4:
        mq136 = st.number_input(
            "MQ-136 (H₂S)",
            min_value=0.0, max_value=5000.0,
            value=50.0, step=1.0,
            help="MQ-136 measures hydrogen sulfide (rotten egg gas)"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:rgba(251,146,60,0.04);border:1px solid rgba(251,146,60,0.15);
                border-radius:12px;padding:1rem 1.4rem;margin-bottom:1rem;">
        <div style="font-size:0.82rem;font-weight:600;color:#FB923C;
                    text-transform:uppercase;letter-spacing:0.08em;">
            🥗 Food Category
        </div>
    </div>
    """, unsafe_allow_html=True)

    food = st.selectbox(
        "Food Type",
        options=food_encoder.classes_,
        help="Select the category of food being tested"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    predict_btn = st.form_submit_button(
        "🔬 Predict Freshness",
        use_container_width=True
    )


# ════════════════════════════════════════════════════════════
# PREDICTION
# ════════════════════════════════════════════════════════════
if predict_btn:
    # Encode food category using the saved LabelEncoder
    food_encoded = food_encoder.transform([food])[0]

    # Build input DataFrame in EXACT same feature order and names as training:
    cols = ['Temperature (°C)', 'Humidity (%)', 'MQ2', 'MQ4', 'MQ135', 'MQ136', 'Food']
    input_df = pd.DataFrame([[
        temp,
        humidity,
        mq2,
        mq4,
        mq135,
        mq136,
        food_encoded
    ]], columns=cols)

    with st.spinner("Running prediction…"):
        prediction  = model.predict(input_df)[0]
        probability = model.predict_proba(input_df)[0]
        shelf_life_hours = shelf_life_model.predict(input_df)[0]

    # Probability for the SPOILED class (index 1)
    spoiled_prob = probability[1]
    fresh_prob   = probability[0]
    confidence_pct = round(spoiled_prob * 100 if prediction == 1 else fresh_prob * 100, 1)
    
    # Calculate shelf life days/hours
    shelf_life_hours_rounded = max(0.0, round(float(shelf_life_hours), 1))
    shelf_life_days = max(0.0, round(shelf_life_hours_rounded / 24.0, 1))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    <div class="section-title" style="font-size:1.1rem;margin-bottom:1rem;">
        📊 Prediction Result
    </div>
    """, unsafe_allow_html=True)

    # ── Result banner ─────────────────────────────────────────
    if prediction == 1:
        st.markdown(f"""
        <div style="background:rgba(248,113,113,0.1);border:2px solid rgba(248,113,113,0.4);
                    border-radius:16px;padding:2rem;text-align:center;margin-bottom:1.5rem;
                    box-shadow:0 4px 24px rgba(248,113,113,0.15);">
            <div style="font-size:3rem;margin-bottom:0.5rem;">⚠️</div>
            <div style="font-size:1.8rem;font-weight:900;color:#F87171;
                        font-family:'Space Grotesk',sans-serif;">
                SPOILED FOOD DETECTED
            </div>
            <div style="font-size:1rem;color:rgba(228,237,255,0.6);margin-top:0.5rem;">
                This food should <b style="color:#F87171;">NOT</b> be distributed or consumed.
            </div>
            <div style="margin-top:1rem;font-size:0.9rem;color:rgba(228,237,255,0.5);">
                Model Confidence: <b style="color:#F87171;font-size:1.2rem;">{confidence_pct}%</b>
                &nbsp;·&nbsp;
                Estimated Shelf Life: <b style="color:#F87171;font-size:1.2rem;">0 hours (0 days)</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:rgba(52,211,153,0.08);border:2px solid rgba(52,211,153,0.35);
                    border-radius:16px;padding:2rem;text-align:center;margin-bottom:1.5rem;
                    box-shadow:0 4px 24px rgba(52,211,153,0.12);">
            <div style="font-size:3rem;margin-bottom:0.5rem;">✅</div>
            <div style="font-size:1.8rem;font-weight:900;color:#34D399;
                        font-family:'Space Grotesk',sans-serif;">
                FRESH FOOD — SAFE TO USE
            </div>
            <div style="font-size:1rem;color:rgba(228,237,255,0.6);margin-top:0.5rem;">
                This food is safe for distribution and consumption.
            </div>
            <div style="margin-top:1rem;font-size:0.9rem;color:rgba(228,237,255,0.5);">
                Model Confidence: <b style="color:#34D399;font-size:1.2rem;">{confidence_pct}%</b>
                &nbsp;·&nbsp;
                Estimated Shelf Life: <b style="color:#34D399;font-size:1.2rem;">{shelf_life_hours_rounded} hours ({shelf_life_days} days)</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Probability breakdown ──────────────────────────────────
    col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
    with col_r1:
        st.markdown(render_kpi(
            "🥗 Food Type", food, "Tested item"
        ), unsafe_allow_html=True)
    with col_r2:
        verdict = "🔴 Spoiled" if prediction == 1 else "🟢 Fresh"
        st.markdown(render_kpi(
            "🔬 Verdict", verdict, "ML prediction"
        ), unsafe_allow_html=True)
    with col_r3:
        st.markdown(render_kpi(
            "✅ Fresh Prob.", f"{fresh_prob*100:.1f}%", "Class 0 score"
        ), unsafe_allow_html=True)
    with col_r4:
        st.markdown(render_kpi(
            "⚠️ Spoil Prob.", f"{spoiled_prob*100:.1f}%", "Class 1 score"
        ), unsafe_allow_html=True)
    with col_r5:
        shelf_text = "0 hrs (0 days)" if prediction == 1 else f"{shelf_life_hours_rounded} hrs (~{shelf_life_days} d)"
        st.markdown(render_kpi(
            "⏳ Est. Shelf Life", shelf_text, "Regressor prediction"
        ), unsafe_allow_html=True)

    # ── Probability bar ────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    bar_color   = "#F87171" if prediction == 1 else "#34D399"
    bar_width   = spoiled_prob * 100 if prediction == 1 else fresh_prob * 100

    st.markdown(f"""
    <div class="glass-card" style="padding:1.2rem 1.5rem;">
        <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;">
            <span style="font-size:0.82rem;color:rgba(228,237,255,0.55);">
                Confidence Meter
            </span>
            <span style="font-size:0.82rem;font-weight:700;color:{bar_color};">
                {confidence_pct}%
            </span>
        </div>
        <div style="background:rgba(255,255,255,0.07);border-radius:999px;height:10px;overflow:hidden;">
            <div style="width:{bar_width}%;height:100%;border-radius:999px;
                        background:linear-gradient(90deg,{bar_color}88,{bar_color});
                        transition:width 0.6s ease;">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Input summary ──────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📋 Sensor Reading Summary"):
        st.markdown(f"""
        | Sensor | Value |
        |---|---|
        | 🌡️ Temperature | `{temp} °C` |
        | 💧 Humidity | `{humidity} %` |
        | MQ-2 (Smoke/LPG) | `{mq2}` |
        | MQ-4 (Methane) | `{mq4}` |
        | MQ-135 (Air Quality) | `{mq135}` |
        | MQ-136 (H₂S) | `{mq136}` |
        | 🥗 Food Type | `{food}` (encoded → `{food_encoded}`) |
        | 🔢 Raw Prediction | `{int(prediction)}` |
        | 📊 Fresh Probability | `{fresh_prob:.4f}` |
        | 📊 Spoiled Probability | `{spoiled_prob:.4f}` |
        | ⏳ Predicted Shelf Life | `{float(shelf_life_hours):.4f} hours (~{float(shelf_life_hours)/24.0:.2f} days)` |
        """)
