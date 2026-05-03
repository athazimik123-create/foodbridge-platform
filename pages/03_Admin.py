# ============================================================
# pages/03_Admin.py — Admin Dashboard
# ============================================================
# Admin can:
#  • Monitor all platform activity (listings, users, transactions)
#  • Manage listing statuses
#  • View revenue analytics with charts
#  • See CO2 & impact metrics
# ============================================================

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timezone, timedelta

from firebase_config import (
    get_all_listings, get_all_users,
    get_all_transactions, get_platform_stats,
    update_listing_status
)
from styles import get_css, render_kpi

st.set_page_config(page_title="Admin Dashboard · FoodBridge", page_icon="🛡️", layout="wide")
st.markdown(get_css(), unsafe_allow_html=True)

# ── Auth guard ────────────────────────────────────────────────
if not st.session_state.get("authenticated"):
    st.warning("Please sign in.")
    st.page_link("app.py", label="← Login")
    st.stop()
if st.session_state.get("user_role") != "admin":
    st.error("🔒 Admin access only.")
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
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="sidebar-user">
        <div class="su-name">🛡️ Admin Alex</div>
        <div class="su-role">Administrator</div>
    </div>""", unsafe_allow_html=True)

    st.page_link("app.py", label="🏠 Home")
    st.page_link("pages/01_Donor.py", label="🍽️ Donor Dashboard")
    st.page_link("pages/02_Receiver.py", label="🤝 Receiver Portal")
    st.page_link("pages/03_Admin.py", label="🛡️ Admin Dashboard")
    st.page_link("pages/04_Route_Optimizer.py", label="🗺️ Route Optimizer")
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.switch_page("app.py")

# ── Header ───────────────────────────────────────────────────
now_str = datetime.now(timezone.utc).strftime("%b %d, %Y · %H:%M UTC")
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.5rem;flex-wrap:wrap;gap:0.8rem;">
    <div>
        <div class="section-title">🛡️ Admin Dashboard</div>
        <div class="section-sub">Full platform control & analytics · {now_str}</div>
    </div>
    <div class="live-badge"><span class="pulse-dot"></span>LIVE ADMIN</div>
</div>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────
stats    = get_platform_stats()
listings = get_all_listings(200)
users    = get_all_users()
txs      = get_all_transactions(200)

# ── KPI Row ───────────────────────────────────────────────────
k = st.columns(6)
kpi_data = [
    ("Total Users",    str(stats["total_users"]),   "Registered"),
    ("Total Listings", str(stats["total_listings"]), "All time"),
    ("Available",      str(stats["available"]),      "Open listings"),
    ("Delivered",      str(stats["delivered"]),      "Completed"),
    ("Meals Saved",    f"{stats['meals_saved']:,}",  "Est. meals"),
    ("Platform Rev.",  f"${stats['total_revenue']:,.2f}", "Total earned"),
]
for col, (label, value, sub) in zip(k, kpi_data):
    with col:
        col.markdown(render_kpi(label, value, sub), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════
tab_overview, tab_listings, tab_users, tab_revenue, tab_impact = st.tabs([
    "📊 Overview", "🥬 Listings", "👥 Users", "💰 Revenue", "🌱 Impact"
])


# ════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW CHARTS
# ════════════════════════════════════════════════════════════
with tab_overview:
    col_l, col_r = st.columns(2)

    with col_l:
        # Status distribution donut
        status_counts = {}
        for l in listings:
            s = l.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1

        fig_status = go.Figure(go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            hole=0.55,
            marker=dict(colors=["#34D399","#FB923C","#818CF8","#6B7280"]),
            textinfo="label+percent",
            textfont=dict(color="#E4EDFF", size=12),
        ))
        fig_status.update_layout(
            title=dict(text="Listing Status Distribution", font=dict(color="#E4EDFF", size=14)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(font=dict(color="#E4EDFF")),
            margin=dict(t=40, b=10, l=10, r=10),
            height=320,
            annotations=[dict(
                text=f"<b>{sum(status_counts.values())}</b><br>total",
                x=0.5, y=0.5, showarrow=False,
                font=dict(color="#34D399", size=16)
            )]
        )
        st.plotly_chart(fig_status, use_container_width=True)

    with col_r:
        # Revenue breakdown bar
        rev_labels = ["Subscriptions", "Logistics Fees", "CSR Credits"]
        rev_vals   = [stats["sub_rev"], stats["logistics_rev"], stats["csr_rev"]]
        rev_colors = ["#34D399", "#818CF8", "#FB923C"]

        fig_rev = go.Figure(go.Bar(
            x=rev_labels, y=rev_vals,
            marker=dict(color=rev_colors, opacity=0.85),
            text=[f"${v:.2f}" for v in rev_vals],
            textposition="outside",
            textfont=dict(color="#E4EDFF"),
        ))
        fig_rev.update_layout(
            title=dict(text="Revenue by Stream", font=dict(color="#E4EDFF", size=14)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(color="#E4EDFF"),
            yaxis=dict(color="#E4EDFF", gridcolor="rgba(255,255,255,0.06)"),
            margin=dict(t=40, b=10, l=10, r=10),
            height=320,
        )
        st.plotly_chart(fig_rev, use_container_width=True)

    # Food type distribution
    ft_counts = {}
    for l in listings:
        ft = l.get("food_type", "Mixed")
        ft_counts[ft] = ft_counts.get(ft, 0) + 1

    df_ft = pd.DataFrame({"Food Type": list(ft_counts.keys()), "Count": list(ft_counts.values())})
    df_ft.sort_values("Count", ascending=True, inplace=True)

    fig_ft = go.Figure(go.Bar(
        x=df_ft["Count"], y=df_ft["Food Type"], orientation="h",
        marker=dict(
            color=df_ft["Count"],
            colorscale=[[0,"#6366F1"],[1,"#34D399"]],
            showscale=False,
        ),
        text=df_ft["Count"], textposition="outside",
        textfont=dict(color="#E4EDFF"),
    ))
    fig_ft.update_layout(
        title=dict(text="Listings by Food Type", font=dict(color="#E4EDFF", size=14)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(color="#E4EDFF", gridcolor="rgba(255,255,255,0.06)"),
        yaxis=dict(color="#E4EDFF"),
        margin=dict(t=40, b=10, l=10, r=10),
        height=300,
    )
    st.plotly_chart(fig_ft, use_container_width=True)


# ════════════════════════════════════════════════════════════
# TAB 2 — LISTINGS MANAGEMENT
# ════════════════════════════════════════════════════════════
with tab_listings:
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        s_filter = st.selectbox("Status Filter", ["All","available","requested","in_transit","delivered"])
    with col_f2:
        ft_filter = st.selectbox("Food Type Filter", ["All","Bakery","Prepared Meals","Produce","Dairy","Mixed"])

    filtered_l = listings
    if s_filter != "All":
        filtered_l = [l for l in filtered_l if l.get("status") == s_filter]
    if ft_filter != "All":
        filtered_l = [l for l in filtered_l if l.get("food_type","") == ft_filter]

    st.markdown(f"**Showing {len(filtered_l)} listings**")

    if filtered_l:
        df_l = pd.DataFrame([{
            "ID":          l["listing_id"][:8] + "…",
            "Food":        l.get("food_name",""),
            "Type":        l.get("food_type",""),
            "Qty (kg)":    l.get("quantity_kg",0),
            "Donor":       l.get("donor_name",""),
            "Status":      l.get("status",""),
            "Address":     l.get("address","")[:35],
            "Created":     str(l.get("created_at",""))[:16],
        } for l in filtered_l])
        st.dataframe(df_l, use_container_width=True, hide_index=True,
                     column_config={
                         "Qty (kg)": st.column_config.NumberColumn(format="%.1f kg"),
                         "Status": st.column_config.TextColumn(),
                     })

    # Quick admin actions
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("**⚡ Quick Admin Actions**")
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        lid_input = st.text_input("Listing ID (partial)", key="admin_lid")
    with col_a2:
        new_status = st.selectbox("New Status", ["available","requested","in_transit","delivered"])
    with col_a3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✏️ Update Status", use_container_width=True):
            # Find matching listing
            matches = [l for l in listings if l["listing_id"].startswith(lid_input)]
            if matches:
                update_listing_status(matches[0]["listing_id"], new_status)
                st.success(f"✅ Updated {matches[0]['food_name']} → {new_status}")
                st.rerun()
            else:
                st.error("No listing found with that ID prefix.")


# ════════════════════════════════════════════════════════════
# TAB 3 — USERS
# ════════════════════════════════════════════════════════════
with tab_users:
    role_counts = {}
    for u in users:
        r = u.get("role","unknown")
        role_counts[r] = role_counts.get(r, 0) + 1

    col_rc, col_ut = st.columns([1, 2])
    with col_rc:
        fig_roles = go.Figure(go.Pie(
            labels=list(role_counts.keys()),
            values=list(role_counts.values()),
            hole=0.5,
            marker=dict(colors=["#34D399","#6366F1","#FB923C"]),
            textfont=dict(color="#E4EDFF", size=13),
        ))
        fig_roles.update_layout(
            title=dict(text="Users by Role", font=dict(color="#E4EDFF", size=14)),
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(font=dict(color="#E4EDFF")),
            margin=dict(t=40,b=10,l=10,r=10),
            height=300,
        )
        st.plotly_chart(fig_roles, use_container_width=True)

    with col_ut:
        df_u = pd.DataFrame([{
            "Name":  u.get("name",""),
            "Email": u.get("email",""),
            "Role":  u.get("role",""),
            "Tier":  u.get("subscription_tier","basic"),
        } for u in users])
        st.dataframe(df_u, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════
# TAB 4 — REVENUE
# ════════════════════════════════════════════════════════════
with tab_revenue:
    # Revenue over time (simulated timeline from transactions)
    if txs:
        df_tx = pd.DataFrame([{
            "date":   str(t.get("timestamp",""))[:10],
            "amount": t.get("amount",0),
            "type":   t.get("type",""),
        } for t in txs])
        df_tx["date"] = pd.to_datetime(df_tx["date"], errors="coerce")
        df_agg = df_tx.groupby(["date","type"])["amount"].sum().reset_index()

        fig_line = px.line(
            df_agg, x="date", y="amount", color="type",
            color_discrete_map={
                "subscription":  "#34D399",
                "logistics_fee": "#818CF8",
                "csr_credit":    "#FB923C",
            },
            markers=True,
            labels={"amount":"Revenue ($)", "date":"Date", "type":"Stream"},
        )
        fig_line.update_layout(
            title=dict(text="Revenue Over Time by Stream", font=dict(color="#E4EDFF", size=14)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(color="#E4EDFF", gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(color="#E4EDFF", gridcolor="rgba(255,255,255,0.06)"),
            legend=dict(font=dict(color="#E4EDFF")),
            margin=dict(t=40,b=10,l=10,r=10),
            height=360,
        )
        st.plotly_chart(fig_line, use_container_width=True)

        # Transaction log table
        st.markdown("**📋 Transaction Log**")
        df_tx_disp = pd.DataFrame([{
            "TX ID":    t.get("tx_id","")[:8]+"…",
            "Amount":   f"${t.get('amount',0):.2f}",
            "Type":     t.get("type",""),
            "User":     t.get("user_id","")[:12]+"…",
            "Timestamp": str(t.get("timestamp",""))[:16],
        } for t in txs])
        st.dataframe(df_tx_disp, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions recorded yet.", icon="💳")


# ════════════════════════════════════════════════════════════
# TAB 5 — IMPACT
# ════════════════════════════════════════════════════════════
with tab_impact:
    total_kg = stats["total_kg"]

    imp1, imp2, imp3, imp4 = st.columns(4)
    with imp1:
        st.markdown(render_kpi("🥗 Total Food", f"{total_kg:.1f} kg", "Submitted to platform"), unsafe_allow_html=True)
    with imp2:
        st.markdown(render_kpi("🍽️ Meals Saved", f"{stats['meals_saved']:,}", "Est. @ 0.4 kg/meal"), unsafe_allow_html=True)
    with imp3:
        st.markdown(render_kpi("🌿 CO₂ Offset", f"{stats['co2_offset_kg']} kg", "Carbon equivalent"), unsafe_allow_html=True)
    with imp4:
        trees = round(stats["co2_offset_kg"] / 21, 1)
        st.markdown(render_kpi("🌳 Tree Equiv.", f"{trees}", "Trees planted equiv."), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Impact gauge
    target_kg = 1000.0
    pct = min(100, round((total_kg / target_kg) * 100, 1))

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=total_kg,
        delta={"reference": target_kg * 0.5, "valueformat": ".1f"},
        title={"text": "Platform Food Redistributed (kg)", "font": {"color": "#E4EDFF", "size": 14}},
        number={"suffix": " kg", "font": {"color": "#34D399", "size": 30}},
        gauge={
            "axis": {"range": [0, target_kg], "tickfont": {"color": "#E4EDFF"}},
            "bar":  {"color": "#34D399"},
            "bgcolor": "rgba(255,255,255,0.05)",
            "bordercolor": "rgba(255,255,255,0.1)",
            "steps": [
                {"range": [0, target_kg*0.33], "color": "rgba(248,113,113,0.2)"},
                {"range": [target_kg*0.33, target_kg*0.66], "color": "rgba(251,146,60,0.2)"},
                {"range": [target_kg*0.66, target_kg], "color": "rgba(52,211,153,0.2)"},
            ],
            "threshold": {"line": {"color": "#6366F1","width": 4}, "value": target_kg*0.8},
        }
    ))
    fig_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        height=320,
        margin=dict(t=40,b=10,l=40,r=40),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown(f"""
    <div class="glass-card" style="text-align:center;padding:1.5rem;margin-top:1rem;">
        <div style="font-size:0.85rem;color:rgba(228,237,255,0.5);">Progress toward 1,000 kg redistribution goal</div>
        <div class="conf-bar" style="margin:0.8rem auto;max-width:400px;">
            <div class="conf-fill" style="width:{pct}%;"></div>
        </div>
        <div style="font-size:1.1rem;font-weight:700;color:#34D399;">{pct}% of target achieved</div>
    </div>
    """, unsafe_allow_html=True)
