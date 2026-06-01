# ============================================================
# styles.py — FoodBridge Design System
# ============================================================

def get_css() -> str:
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* ── RESET & BASE ─────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #060B18 0%, #0C1A2E 45%, #081220 100%) !important;
    min-height: 100vh;
    font-family: 'Inter', sans-serif !important;
    color: #E4EDFF !important;
}

/* ── HIDE STREAMLIT CHROME ─────────────────────────────────── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] > div:first-child { padding-top: 0.5rem; }

/* ── SCROLLBAR ──────────────────────────────────────────────── */
::-webkit-scrollbar              { width: 5px; }
::-webkit-scrollbar-track        { background: transparent; }
::-webkit-scrollbar-thumb        { background: rgba(52,211,153,0.3); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover  { background: rgba(52,211,153,0.6); }

/* ── SIDEBAR ────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: rgba(6,11,24,0.95) !important;
    backdrop-filter: blur(32px) !important;
    border-right: 1px solid rgba(52,211,153,0.12) !important;
    box-shadow: 4px 0 40px rgba(0,0,0,0.6) !important;
}
section[data-testid="stSidebar"] * { color: #E4EDFF !important; }

/* ── MAIN CONTAINER ─────────────────────────────────────────── */
[data-testid="stMainBlockContainer"] {
    padding: 1.8rem 2.4rem !important;
    max-width: 1400px !important;
    margin: 0 auto !important;
}

/* ── GLASS CARD ─────────────────────────────────────────────── */
.glass-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 20px;
    padding: 1.8rem;
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    box-shadow: 0 8px 40px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.07);
    transition: transform 0.3s cubic-bezier(.25,.8,.25,1), box-shadow 0.3s ease;
    position: relative; overflow: hidden;
}
.glass-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:1px;
    background: linear-gradient(90deg, transparent, rgba(52,211,153,0.45), transparent);
}
.glass-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 60px rgba(52,211,153,0.12), 0 8px 40px rgba(0,0,0,0.5);
}

/* ── FOOD CARD ──────────────────────────────────────────────── */
.food-card {
    background: rgba(255,255,255,0.045);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 18px;
    padding: 1.4rem 1.5rem;
    backdrop-filter: blur(18px);
    box-shadow: 0 4px 28px rgba(0,0,0,0.35);
    transition: all 0.3s cubic-bezier(.25,.8,.25,1);
    cursor: pointer; position: relative; overflow: hidden;
}
.food-card::after {
    content:''; position:absolute; top:0; left:0; width:4px; height:100%;
    background: linear-gradient(180deg, #34D399, #6366F1);
    border-radius: 4px 0 0 4px;
}
.food-card:hover {
    transform: translateY(-5px) scale(1.01);
    border-color: rgba(52,211,153,0.3);
    box-shadow: 0 16px 50px rgba(52,211,153,0.1);
}
.food-icon  { font-size: 2.2rem; margin-bottom: 0.5rem; }
.food-title { font-size: 1.05rem; font-weight: 700; color: #fff; font-family: 'Space Grotesk', sans-serif; }
.food-meta  { font-size: 0.82rem; color: rgba(228,237,255,0.55); margin-top: 0.3rem; }
.food-qty   { font-size: 1.4rem; font-weight: 800; color: #34D399; margin-top: 0.5rem; }
.food-loc   { font-size: 0.78rem; color: rgba(228,237,255,0.45); margin-top: 0.4rem; }

/* ── KPI CARD ───────────────────────────────────────────────── */
.kpi-card {
    background: rgba(255,255,255,0.045);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 18px;
    padding: 1.1rem 0.8rem;
    text-align: center;
    backdrop-filter: blur(18px);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    position: relative; overflow: hidden;
    min-width: 0;
}
.kpi-card::before {
    content:''; position:absolute; bottom:0; left:0; right:0; height:2px;
    background: linear-gradient(90deg, #34D399, #6366F1, #34D399);
    background-size: 200%; animation: shimmer 3s linear infinite;
}
@keyframes shimmer { 0%{background-position:0%} 100%{background-position:200%} }
.kpi-card:hover { transform: translateY(-4px); box-shadow: 0 12px 40px rgba(52,211,153,0.12); }
.kpi-label { font-size: 0.7rem; font-weight: 600; color: rgba(228,237,255,0.5); text-transform: uppercase; letter-spacing: 0.1em; }
.kpi-value { font-size: 1.65rem; font-weight: 900; color: #34D399; margin: 0.2rem 0 0; font-family: 'Space Grotesk', sans-serif; line-height: 1.1; word-wrap: break-word; }
.kpi-sub   { font-size: 0.68rem; color: rgba(228,237,255,0.38); margin-top: 0.2rem; }
.kpi-delta { font-size: 0.78rem; font-weight: 600; margin-top: 0.4rem; }
.kpi-delta.up { color: #34D399; }
.kpi-delta.down { color: #F87171; }

/* ── PULSE / LIVE ────────────────────────────────────────────── */
@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(52,211,153,0.5); }
    50%       { box-shadow: 0 0 0 9px rgba(52,211,153,0); }
}
.pulse-dot {
    display: inline-block; width: 9px; height: 9px;
    border-radius: 50%; background: #34D399;
    animation: pulse-glow 2s infinite;
    vertical-align: middle; margin-right: 6px;
}
.live-badge {
    display: inline-flex; align-items: center;
    background: rgba(52,211,153,0.1);
    border: 1px solid rgba(52,211,153,0.28);
    border-radius: 20px; padding: 4px 13px;
    font-size: 0.74rem; font-weight: 700;
    color: #34D399; letter-spacing: 0.06em;
}

/* ── BADGES ──────────────────────────────────────────────────── */
.badge {
    display: inline-block; padding: 3px 10px;
    border-radius: 20px; font-size: 0.7rem;
    font-weight: 700; letter-spacing: 0.07em;
    text-transform: uppercase;
}
.badge-green  { background: rgba(52,211,153,0.15); color: #34D399; border: 1px solid rgba(52,211,153,0.3); }
.badge-blue   { background: rgba(99,102,241,0.15); color: #818CF8; border: 1px solid rgba(99,102,241,0.3); }
.badge-orange { background: rgba(251,146,60,0.15); color: #FB923C; border: 1px solid rgba(251,146,60,0.3); }
.badge-red    { background: rgba(248,113,113,0.15); color: #F87171; border: 1px solid rgba(248,113,113,0.3); }
.badge-purple { background: rgba(167,139,250,0.15); color: #A78BFA; border: 1px solid rgba(167,139,250,0.3); }

/* ── STATUS COLORS ───────────────────────────────────────────── */
.status-available  { color: #34D399; }
.status-requested  { color: #FB923C; }
.status-in_transit { color: #818CF8; }
.status-delivered  { color: rgba(228,237,255,0.4); }

/* ── CONF BAR ────────────────────────────────────────────────── */
.conf-bar { background: rgba(255,255,255,0.08); border-radius: 6px; height: 6px; overflow: hidden; margin: 0.4rem 0; }
.conf-fill { height: 100%; border-radius: 6px; background: linear-gradient(90deg, #34D399, #6366F1); transition: width 0.7s ease; }

/* ── BUTTONS ─────────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #34D399, #10B981) !important;
    color: #060B18 !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    padding: 0.62rem 1.5rem !important;
    letter-spacing: 0.02em !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 20px rgba(52,211,153,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px rgba(52,211,153,0.5) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── FORM INPUTS ─────────────────────────────────────────────── */
div[data-baseweb="input"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
}
div[data-baseweb="input"] div {
    background-color: transparent !important;
}
div[data-baseweb="input"] input,
div[data-baseweb="input"] textarea {
    background: transparent !important;
    color: #E4EDFF !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stNumberInput"] button {
    background: transparent !important;
    color: #E4EDFF !important;
    border: none !important;
}
[data-testid="stNumberInput"] button:hover {
    color: #34D399 !important;
    background: rgba(255,255,255,0.05) !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus,
[data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within {
    border-color: rgba(52,211,153,0.5) !important;
    box-shadow: 0 0 0 3px rgba(52,211,153,0.1) !important;
}
label { color: rgba(228,237,255,0.7) !important; font-size: 0.84rem !important; font-weight: 500 !important; }

/* ── SELECTBOX ───────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    color: #E4EDFF !important;
}

/* ── SECTION HEADERS ─────────────────────────────────────────── */
.section-title {
    font-size: 1.5rem; font-weight: 800;
    font-family: 'Space Grotesk', sans-serif;
    background: linear-gradient(135deg, #34D399, #6366F1);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 0.3rem;
}
.section-sub { font-size: 0.87rem; color: rgba(228,237,255,0.45); margin-bottom: 1.5rem; }

/* ── SIDEBAR USER CARD ───────────────────────────────────────── */
.sidebar-user {
    background: rgba(52,211,153,0.07);
    border: 1px solid rgba(52,211,153,0.18);
    border-radius: 14px; padding: 0.9rem 1rem; margin-bottom: 1rem;
}
.su-name { font-weight: 700; font-size: 0.95rem; color: #fff; }
.su-role { font-size: 0.72rem; color: #34D399; text-transform: uppercase; letter-spacing: 0.07em; margin-top: 2px; }
.su-tier { font-size: 0.7rem; color: rgba(228,237,255,0.4); margin-top: 2px; }

/* ── ROUTE CARD ──────────────────────────────────────────────── */
.route-card {
    background: rgba(99,102,241,0.07);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 16px; padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
    transition: transform 0.25s ease;
}
.route-card:hover { transform: translateY(-3px); }
.route-step {
    display: flex; align-items: center; gap: 0.6rem;
    font-size: 0.82rem; color: rgba(228,237,255,0.7);
    padding: 0.3rem 0; border-left: 2px solid rgba(52,211,153,0.3);
    padding-left: 0.8rem; margin-left: 0.4rem;
}
.route-step:last-child { border-left: 2px solid transparent; }

/* ── ADMIN TABLE ─────────────────────────────────────────────── */
[data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden; }

/* ── DIVIDER ─────────────────────────────────────────────────── */
hr { border: none; border-top: 1px solid rgba(255,255,255,0.07); margin: 1.4rem 0; }

/* ── ANIMATIONS ──────────────────────────────────────────────── */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}
.animate-in { animation: fadeUp 0.5s ease both; }

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50%       { transform: translateY(-6px); }
}
.fab {
    position: fixed; bottom: 2rem; right: 2rem; z-index: 9999;
    width: 56px; height: 56px;
    background: linear-gradient(135deg, #34D399, #6366F1);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem;
    box-shadow: 0 8px 32px rgba(52,211,153,0.45);
    cursor: pointer;
    animation: float 3.5s ease-in-out infinite;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.fab:hover { transform: scale(1.12) translateY(-4px); box-shadow: 0 16px 48px rgba(52,211,153,0.6); }

/* ── TABS ────────────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tab"] {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    color: rgba(228,237,255,0.6) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #34D399 !important;
    border-bottom-color: #34D399 !important;
}

/* ── MAP CONTAINER ───────────────────────────────────────────── */
.map-container {
    border-radius: 16px; overflow: hidden;
    border: 1px solid rgba(52,211,153,0.15);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
</style>
"""


def render_food_card(listing: dict) -> str:
    _icons = {
        "Bakery": "🥖", "Produce": "🥬", "Prepared Meals": "🍱",
        "Dairy": "🥛", "Seafood": "🐟", "Snacks": "🍿",
        "Grains": "🌾", "Fruits": "🍎", "Mixed": "📦",
    }
    icon = _icons.get(listing.get("food_type", "Mixed"), "📦")
    status = listing.get("status", "available")
    badge_cls = {
        "available": "badge-green", "requested": "badge-orange",
        "in_transit": "badge-blue", "delivered": "badge-purple",
    }.get(status, "badge-green")
    exp_dt = listing.get("expiry_dt", "")
    exp_str = exp_dt[:16].replace("T", " ") if exp_dt else "N/A"
    tags = listing.get("tags", [])
    tag_html = " ".join(f'<span class="badge badge-blue">{t}</span>' for t in tags[:3])

    return f"""
    <div class="food-card animate-in">
        <div class="food-icon">{icon}</div>
        <div class="food-title">{listing.get('food_name', 'Unnamed')}</div>
        <div class="food-meta">{listing.get('food_type','Mixed')} · {listing.get('donor_name','')}</div>
        <div class="food-qty">{listing.get('quantity_kg',0)} kg</div>
        <div class="food-loc">📍 {listing.get('address','')[:45]}</div>
        <div style="margin-top:0.6rem;display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;">
            <span class="badge {badge_cls}">{status}</span>
            {tag_html}
        </div>
        <div style="font-size:0.73rem;color:rgba(228,237,255,0.38);margin-top:0.5rem;">
            ⏰ Expires: {exp_str} · 🕐 {listing.get('pickup_window','Flexible')}
        </div>
    </div>
    """


def render_kpi(label: str, value: str, sub: str = "", delta: str = "") -> str:
    delta_html = ""
    if delta:
        cls = "up" if delta.startswith("+") else "down"
        delta_html = f'<div class="kpi-delta {cls}">{delta}</div>'
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {"<div class='kpi-sub'>" + sub + "</div>" if sub else ""}
        {delta_html}
    </div>
    """
