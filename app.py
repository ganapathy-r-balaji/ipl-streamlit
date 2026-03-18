import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IPL 2026 — Match Predictor",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "IPL 2026 Match Prediction Dashboard"},
)

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    path = Path(__file__).parent / "data" / "dashboard_data_v2.json"
    with open(path) as f:
        return json.load(f)

DATA = load_data()

# ── Constants ─────────────────────────────────────────────────────────────────
SHORT = {
    "Royal Challengers Bengaluru": "RCB",
    "Chennai Super Kings":         "CSK",
    "Mumbai Indians":              "MI",
    "Kolkata Knight Riders":       "KKR",
    "Sunrisers Hyderabad":         "SRH",
    "Delhi Capitals":              "DC",
    "Rajasthan Royals":            "RR",
    "Punjab Kings":                "PBKS",
    "Gujarat Titans":              "GT",
    "Lucknow Super Giants":        "LSG",
}
COLORS = {
    "Royal Challengers Bengaluru": "#EC1C24",
    "Chennai Super Kings":         "#F9CD05",
    "Mumbai Indians":              "#004BA0",
    "Kolkata Knight Riders":       "#3A225D",
    "Sunrisers Hyderabad":         "#F7A721",
    "Delhi Capitals":              "#17479E",
    "Rajasthan Royals":            "#EA1A85",
    "Punjab Kings":                "#AA4545",
    "Gujarat Titans":              "#C69A4C",
    "Lucknow Super Giants":        "#A72056",
}
TEAMS     = list(SHORT.keys())
TL        = {"cool": ("Cool", 22), "warm": ("Warm", 30), "hot": ("Hot", 38)}
HL        = {"dry": ("Dry", 40), "moderate": ("Moderate", 65), "humid": ("Humid", 82)}
PRE_NRR   = {r["team"]: r["nrr"] for r in DATA["points_table"]}

# ── Helpers ───────────────────────────────────────────────────────────────────
def hex_rgba(h, a=0.4):
    h = h.lstrip("#")
    return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

def team_from_short(s):
    return next((k for k, v in SHORT.items() if v == s), None)

# ── State management ──────────────────────────────────────────────────────────
def init_match(i):
    m  = DATA["matches"][i]
    wx = m["wx_defaults"]
    st.session_state.match_idx  = i
    st.session_state.toss_t1    = 0
    st.session_state.bats_first = 1
    st.session_state.pitch      = m.get("pitch_label", "balanced")
    st.session_state.temp       = wx.get("temp_level", "warm")
    st.session_state.hum        = wx.get("hum_level", "moderate")
    st.session_state.rain       = int(wx.get("rain_risk", 0))
    st.session_state.dew        = int(wx.get("dew_risk", 0))

if "match_idx" not in st.session_state:
    init_match(0)
    st.session_state.team_filter = "All Teams"

# ── Prediction helpers ────────────────────────────────────────────────────────
def get_key():
    t1b = (
        (st.session_state.toss_t1 == 0 and st.session_state.bats_first == 1) or
        (st.session_state.toss_t1 == 1 and st.session_state.bats_first == 0)
    )
    return (
        f"{'1' if t1b else '0'}|{st.session_state.pitch}|"
        f"{st.session_state.temp}|{st.session_state.hum}|"
        f"{st.session_state.rain}|{st.session_state.dew}"
    )

def get_prob():
    m   = DATA["matches"][st.session_state.match_idx]
    key = get_key()
    pr  = DATA["lookup"].get(str(m["match_id"]), {}).get(key, {})
    p   = pr.get("avg", m["p_t1_avg"])
    return p, pr, m

def live_table():
    sel = DATA["matches"][st.session_state.match_idx]
    key = get_key()
    pts = dict(DATA["base_extra_pts"])
    nrr = {t: PRE_NRR.get(t, 0) for t in pts}
    for m in DATA["matches"]:
        if str(m["match_id"]) == str(sel["match_id"]):
            pr = DATA["lookup"].get(str(m["match_id"]), {}).get(key, {})
            p  = pr.get("avg", m["p_t1_avg"])
        else:
            p = m["p_t1_avg"]
        pts[m["team1"]] = pts.get(m["team1"], 0) + 2 * p
        pts[m["team2"]] = pts.get(m["team2"], 0) + 2 * (1 - p)
    sorted_t = sorted(pts, key=lambda t: (-pts[t], -nrr.get(t, 0)))
    rows = []
    for i, team in enumerate(sorted_t):
        ew = pts[team] / 2
        rows.append({
            "Rank": i + 1,
            "Team": SHORT[team],
            "_full": team,
            "P":    14,
            "W":    round(ew),
            "L":    14 - round(ew),
            "Pts":  round(pts[team]),
            "NRR":  round(nrr.get(team, 0), 2),
            "Q":    i < 4,
        })
    return rows, sorted_t[:4]

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  section[data-testid="stSidebar"] { min-width: 260px !important; max-width: 300px !important; }
  div[data-testid="stRadio"] label { font-size: 12px !important; }
  .block-container { padding-top: 1rem !important; }
  div[data-testid="stSidebarContent"] { padding-top: 0.5rem; }
  .stSelectbox label, .stSlider label, .stRadio label { font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="background:#161b22;border-bottom:1px solid #30363d;padding:10px 18px;
         margin:-1rem -4rem 1rem -4rem;display:flex;align-items:center;gap:10px">
      <span style="font-size:22px;font-weight:800;color:#f97316">🏏 IPL 2026</span>
      <span style="font-size:13px;color:#8b949e">Live Match Prediction Simulator</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR: Team filter + Fixture list
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 📅 2026 Schedule")

    # Team filter dropdown
    filter_opts = ["All Teams"] + [f"{SHORT[t]} — {t}" for t in TEAMS]
    if st.session_state.team_filter not in filter_opts:
        st.session_state.team_filter = "All Teams"

    team_filter_sel = st.selectbox(
        "team_filter_label",
        filter_opts,
        index=filter_opts.index(st.session_state.team_filter),
        label_visibility="collapsed",
    )
    st.session_state.team_filter = team_filter_sel
    sel_team = None if team_filter_sel == "All Teams" else TEAMS[filter_opts.index(team_filter_sel) - 1]

    # Build filtered match list
    filtered = [
        (i, m) for i, m in enumerate(DATA["matches"])
        if not sel_team or m["team1"] == sel_team or m["team2"] == sel_team
    ]
    if not filtered:
        filtered = list(enumerate(DATA["matches"]))

    # If current match no longer in filter → switch to first
    if not any(i == st.session_state.match_idx for i, _ in filtered):
        init_match(filtered[0][0])

    cur_pos = next(
        (j for j, (i, _) in enumerate(filtered) if i == st.session_state.match_idx), 0
    )

    def fx_label(m):
        return f"{SHORT[m['team1']]} vs {SHORT[m['team2']]}  —  {m['date']}"

    fx_opts = [fx_label(m) for _, m in filtered]

    # Use a key that refreshes when the filter changes so the radio resets correctly
    radio_key = f"fx_radio_{team_filter_sel}"
    sel_pos = st.radio(
        "fixture_list",
        range(len(filtered)),
        index=cur_pos,
        format_func=lambda j: fx_opts[j],
        label_visibility="collapsed",
        key=radio_key,
    )

    new_idx = filtered[sel_pos][0]
    if new_idx != st.session_state.match_idx:
        init_match(new_idx)
        st.rerun()

# ── Current match shorthand ───────────────────────────────────────────────────
m  = DATA["matches"][st.session_state.match_idx]
t1 = m["team1"]
t2 = m["team2"]

# ══════════════════════════════════════════════════════════════════════════════
#  TOP ROW: Match Conditions (left)  +  Prediction Output (right)
# ══════════════════════════════════════════════════════════════════════════════
left, right = st.columns([1, 1], gap="large")

# ── LEFT: Match Conditions ────────────────────────────────────────────────────
with left:
    st.markdown("#### ⚙️ Match Conditions")

    # Toss winner
    toss_opts = [f"{SHORT[t1]} wins toss", f"{SHORT[t2]} wins toss"]
    toss_sel  = st.radio("**Toss Winner**", toss_opts,
                          index=st.session_state.toss_t1, horizontal=True)
    st.session_state.toss_t1 = toss_opts.index(toss_sel)

    # Toss decision — label reflects the toss winner
    tw = SHORT[t1] if st.session_state.toss_t1 == 0 else SHORT[t2]
    bat_opts = [f"{tw} bats first", f"{tw} bowls first"]
    bat_sel  = st.radio("**Toss Decision**", bat_opts,
                         index=0 if st.session_state.bats_first == 1 else 1,
                         horizontal=True)
    st.session_state.bats_first = 1 if bat_opts.index(bat_sel) == 0 else 0
    st.caption("Batting first sets a target; bowling first leverages dew & conditions.")

    # Pitch type
    pitch_opts = ["balanced", "flat", "spin", "pace"]
    pv = st.session_state.pitch if st.session_state.pitch in pitch_opts else "balanced"
    pitch_sel = st.select_slider("**Pitch Type**", options=pitch_opts, value=pv)
    st.session_state.pitch = pitch_sel
    st.caption("Flat pitches favour batters. Spin/Pace assist specialist bowlers.")

    # Temperature
    temp_opts = list(TL.keys())
    tv = st.session_state.temp if st.session_state.temp in temp_opts else "warm"
    temp_sel  = st.select_slider(
        "**Temperature**", options=temp_opts, value=tv,
        format_func=lambda t: f"{TL[t][0]} ({TL[t][1]}°C)",
    )
    st.session_state.temp = temp_sel
    st.caption(f"Currently: {TL[temp_sel][0]} · {TL[temp_sel][1]}°C")

    # Humidity
    hum_opts = list(HL.keys())
    hv = st.session_state.hum if st.session_state.hum in hum_opts else "moderate"
    hum_sel = st.select_slider(
        "**Humidity**", options=hum_opts, value=hv,
        format_func=lambda h: f"{HL[h][0]} ({HL[h][1]}%)",
    )
    st.session_state.hum = hum_sel
    st.caption(f"Currently: {HL[hum_sel][0]} · {HL[hum_sel][1]}%  ·  High humidity aids swing & dew risk.")

    # Rain risk
    rain_opts = ["☀ No Rain", "🌧 Rain Expected"]
    rain_sel  = st.radio("**Rain Risk**", rain_opts,
                          index=st.session_state.rain, horizontal=True)
    st.session_state.rain = rain_opts.index(rain_sel)

    # Dew risk
    dew_opts = ["🌙 No Dew", "💧 Heavy Dew"]
    dew_sel  = st.radio("**Dew Risk**", dew_opts,
                         index=st.session_state.dew, horizontal=True)
    st.session_state.dew = dew_opts.index(dew_sel)
    st.caption("Heavy dew makes the ball slippery — favours team batting second.")

    if st.button("↺  Reset to match defaults", use_container_width=True):
        init_match(st.session_state.match_idx)
        st.rerun()

# ── RIGHT: Prediction Output ──────────────────────────────────────────────────
with right:
    st.markdown("#### 🎯 Prediction Output")

    p, pr, _ = get_prob()
    p1 = p * 100
    p2 = 100 - p1

    # Semi-circle doughnut gauge
    fig_g = go.Figure(go.Pie(
        values=[p1 / 2, p2 / 2, 50],
        marker_colors=[COLORS[t1], COLORS[t2], "rgba(0,0,0,0)"],
        hole=0.72,
        rotation=90,
        direction="clockwise",
        textinfo="none",
        hoverinfo="none",
        showlegend=False,
    ))
    fig_g.add_annotation(
        text=(
            f"<b>{p1:.1f}%</b><br>"
            f"<span style='font-size:12px;color:#8b949e'>{SHORT[t1]} win chance</span>"
        ),
        x=0.5, y=0.1, xref="paper", yref="paper",
        showarrow=False, font=dict(size=28, color="#f97316"),
    )
    # T1 and T2 labels at ends of the arc
    fig_g.add_annotation(
        text=f"<b>{SHORT[t1]}</b><br><span style='color:#8b949e;font-size:10px'>{p1:.0f}%</span>",
        x=0.08, y=0.05, xref="paper", yref="paper",
        showarrow=False, font=dict(size=12, color=COLORS[t1]),
    )
    fig_g.add_annotation(
        text=f"<b>{SHORT[t2]}</b><br><span style='color:#8b949e;font-size:10px'>{p2:.0f}%</span>",
        x=0.92, y=0.05, xref="paper", yref="paper",
        showarrow=False, font=dict(size=12, color=COLORS[t2]),
    )
    fig_g.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=210,
        margin=dict(t=0, b=0, l=0, r=0),
    )
    st.plotly_chart(fig_g, use_container_width=True, config={"displayModeBar": False})

    # Model breakdown bars (HTML for precise styling)
    st.markdown("**Model Breakdown**")
    models = [
        ("xgb", "XGBoost",    "#6496ff"),
        ("lgb", "LightGBM",   "#ffc864"),
        ("rf",  "Rnd Forest", "#96d296"),
        ("mlp", "Neural Net", "#c896ff"),
    ]
    bars = '<div style="display:flex;flex-direction:column;gap:6px;margin-top:4px">'
    for mk, ml, mc in models:
        val = pr.get(mk, m.get(f"p_t1_{mk}", p)) * 100
        bars += (
            f'<div style="display:flex;align-items:center;gap:8px">'
            f'<div style="font-size:11px;color:#8b949e;width:72px;flex-shrink:0">{ml}</div>'
            f'<div style="flex:1;height:7px;background:#1c2128;border-radius:3px;overflow:hidden">'
            f'<div style="width:{val:.1f}%;height:100%;background:{mc};border-radius:3px"></div>'
            f'</div>'
            f'<div style="font-size:11px;color:#c9d1d9;width:38px;text-align:right">{val:.1f}%</div>'
            f'</div>'
        )
    bars += "</div>"
    st.markdown(bars, unsafe_allow_html=True)

    # Match Intel grid
    st.markdown("---")
    st.markdown("**Match Intel**")
    intel_items = [
        ("T1 ELO",     str(round(m["t1_elo"])),        SHORT[t1]),
        ("T2 ELO",     str(round(m["t2_elo"])),        SHORT[t2]),
        ("T1 Batting", f"{m['t1_batting']:.1f}",       "avg×SR/100"),
        ("T2 Batting", f"{m['t2_batting']:.1f}",       "avg×SR/100"),
        ("Flatness",   f"{m['flatness']:.2f}",         "pitch index"),
        ("Dew Factor", f"{m['dew_factor']:.3f}",       "venue avg"),
    ]
    ig = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:6px">'
    for lbl, val, sub in intel_items:
        ig += (
            f'<div style="background:#0d1117;border:1px solid #30363d;border-radius:7px;padding:8px 10px">'
            f'<div style="font-size:10px;color:#8b949e;text-transform:uppercase">{lbl}</div>'
            f'<div style="font-size:17px;font-weight:800;color:#f97316">{val}</div>'
            f'<div style="font-size:10px;color:#8b949e">{sub}</div>'
            f'</div>'
        )
    ig += "</div>"
    st.markdown(ig, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  BOTTOM ROW 1: League Table + Playoff Bracket
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
table_rows, top4 = live_table()
tab_col, brk_col = st.columns([1.15, 1], gap="large")

# ── Simulated League Table ────────────────────────────────────────────────────
with tab_col:
    st.markdown("#### 📊 Simulated League Table")
    tbl = (
        '<table style="width:100%;border-collapse:collapse;font-size:12px">'
        "<thead><tr style=\"color:#8b949e;border-bottom:1px solid #30363d\">"
        "<th style=\"padding:5px 8px;text-align:left\">#</th>"
        "<th style=\"padding:5px 8px;text-align:left\">Team</th>"
        "<th style=\"padding:5px 8px;text-align:center\">P</th>"
        "<th style=\"padding:5px 8px;text-align:center\">W</th>"
        "<th style=\"padding:5px 8px;text-align:center\">L</th>"
        "<th style=\"padding:5px 8px;text-align:center\">Pts</th>"
        "<th style=\"padding:5px 8px;text-align:center\">NRR</th>"
        "</tr></thead><tbody>"
    )
    for row in table_rows:
        c     = "#c9d1d9" if row["Q"] else "#8b949e"
        badge = (
            '<span style="font-size:9px;padding:1px 4px;border-radius:3px;'
            'background:#f9731622;color:#f97316;border:1px solid #f9731444;margin-left:4px">Q</span>'
            if row["Q"] else ""
        )
        dot_c = COLORS.get(row["_full"], "#888")
        tbl += (
            f'<tr style="border-bottom:1px solid #1c2128">'
            f'<td style="padding:5px 8px;color:{c}">{row["Rank"]}</td>'
            f'<td style="padding:5px 8px;color:{c}">'
            f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;'
            f'background:{dot_c};margin-right:5px;vertical-align:middle"></span>'
            f'{row["Team"]}{badge}</td>'
            f'<td style="padding:5px 8px;text-align:center;color:{c}">{row["P"]}</td>'
            f'<td style="padding:5px 8px;text-align:center;color:{c}">{row["W"]}</td>'
            f'<td style="padding:5px 8px;text-align:center;color:{c}">{row["L"]}</td>'
            f'<td style="padding:5px 8px;text-align:center;color:{c}"><strong>{row["Pts"]}</strong></td>'
            f'<td style="padding:5px 8px;text-align:center;color:{c}">{row["NRR"]:.2f}</td>'
            f'</tr>'
        )
    tbl += "</tbody></table>"
    st.markdown(tbl, unsafe_allow_html=True)
    st.caption("Expected-value table · updates live with condition changes · Q = playoff qualifier")

# ── Playoff Bracket ───────────────────────────────────────────────────────────
with brk_col:
    st.markdown("#### 🏆 Playoff Bracket")

    ab = lambda t: SHORT.get(t, t[:3].upper())

    def pill(name):
        if COLORS.get(name):
            return (
                f"<div style='background:{COLORS[name]};padding:5px 10px;border-radius:5px;"
                f"color:white;font-weight:700;text-align:center;font-size:12px'>{SHORT[name]}</div>"
            )
        return (
            f"<div style='background:#1c2128;border:1px solid #30363d;padding:5px 10px;"
            f"border-radius:5px;color:#8b949e;text-align:center;font-size:11px;line-height:1.4'>"
            f"{name}</div>"
        )

    bracket_data = [
        ("Qualifier 1", top4[0],                         top4[1],
         "1st vs 2nd — winner goes direct to Final"),
        ("Eliminator",  top4[2],                         top4[3],
         "3rd vs 4th — loser is eliminated"),
        ("Qualifier 2", f"Loser of Q1 ({ab(top4[1])})",  f"Winner of Elim ({ab(top4[2])})",
         "Last chance match — winner reaches Final"),
        ("Final",       f"Q1 Winner ({ab(top4[0])})",    "Q2 Winner",
         "IPL 2026 Champion crowned"),
    ]

    brk_html = ""
    for match_nm, ta, tb, note in bracket_data:
        brk_html += (
            f'<div style="margin-bottom:12px">'
            f'<div style="font-size:12px;font-weight:700;color:#f97316;margin-bottom:5px">{match_nm}</div>'
            f'<div style="display:grid;grid-template-columns:1fr auto 1fr;gap:6px;align-items:center">'
            f'{pill(ta)}'
            f'<div style="color:#8b949e;font-size:10px;text-align:center;padding:0 4px">vs</div>'
            f'{pill(tb)}'
            f'</div>'
            f'<div style="font-size:10px;color:#8b949e;margin-top:4px">{note}</div>'
            f'</div>'
        )
    st.markdown(brk_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  BOTTOM ROW 2: Tournament Win Probabilities
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("#### 🎲 Tournament Win Probabilities (Monte Carlo)")

mc_sorted = sorted(
    DATA["points_table"],
    key=lambda r: -(DATA["mc"].get(r["team"], {}).get("win_probability", 0)),
)
mc_teams  = [r["team"] for r in mc_sorted]
win_p     = [DATA["mc"].get(t, {}).get("win_probability",    0) * 100 for t in mc_teams]
playoff_p = [DATA["mc"].get(t, {}).get("playoff_probability", 0) * 100 for t in mc_teams]

fig_mc = go.Figure()
fig_mc.add_trace(go.Bar(
    y=[SHORT[t] for t in mc_teams], x=playoff_p, name="Playoff %",
    orientation="h", marker_color=[hex_rgba(COLORS[t], 0.4) for t in mc_teams],
    marker_line_width=0,
))
fig_mc.add_trace(go.Bar(
    y=[SHORT[t] for t in mc_teams], x=win_p, name="Win %",
    orientation="h", marker_color=[COLORS[t] for t in mc_teams],
    marker_line_width=0,
))
fig_mc.update_layout(
    barmode="overlay",
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#c9d1d9", size=12),
    height=300, margin=dict(t=0, b=10, l=0, r=0),
    xaxis=dict(color="#8b949e", gridcolor="#30363d", title="Probability (%)"),
    yaxis=dict(color="#8b949e", gridcolor="rgba(0,0,0,0)"),
    legend=dict(font=dict(color="#c9d1d9"), bgcolor="rgba(0,0,0,0)", orientation="h",
                yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig_mc, use_container_width=True, config={"displayModeBar": False})

# ══════════════════════════════════════════════════════════════════════════════
#  BOTTOM ROW 3: Model Performance
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("#### 📈 Model Performance")
metrics      = DATA.get("metrics", {})
metric_items = list(metrics.items())
cols_per_row = 3
for row_start in range(0, len(metric_items), cols_per_row):
    row_items = metric_items[row_start: row_start + cols_per_row]
    met_cols  = st.columns(cols_per_row)
    for col_i, (name, vals) in enumerate(row_items):
        with met_cols[col_i]:
            st.markdown(
                f"""
                <div style="background:#161b22;border:1px solid #30363d;border-radius:7px;padding:12px 14px;margin-bottom:8px">
                  <div style="font-size:10px;color:#8b949e;text-transform:uppercase;letter-spacing:.4px">{name}</div>
                  <div style="font-size:22px;font-weight:800;color:#f97316;margin:4px 0">{vals['accuracy']*100:.1f}%</div>
                  <div style="font-size:11px;color:#8b949e">AUC-ROC: {vals['auc_roc']:.4f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
