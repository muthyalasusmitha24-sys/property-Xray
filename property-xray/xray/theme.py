"""Visual layer: styling and Plotly helpers (presentation only)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

TEAL, TEAL_DARK, CORAL, GOLD, INK, MUTED, LINE = "#0F766E", "#134E4A", "#D9684A", "#D9A441", "#1F2A2E", "#6B7780", "#E6E1D6"
NAVY = "#0f2a4a"
BAND_COLORS = {"Excellent": "#15803D", "Good": "#65A30D", "Moderate": "#C58B16", "Below average": "#D9684A", "Poor": "#B91C1C", "n/a": "#94a3b8"}
BAND_EDGES = [(0, 35, "Poor"), (35, 50, "Below average"), (50, 65, "Moderate"), (65, 80, "Good"), (80, 100, "Excellent")]
SCORE_COLORS = {"trust": "#0f2a4a", "wellness": "#0F766E", "future": "#7c3aed"}
SCALE = [[0, "#B91C1C"], [0.35, "#D9684A"], [0.5, "#E8C46A"], [0.65, "#A3C744"], [1, "#15803D"]]
DIVERGING = [[0, "#C2553A"], [0.25, "#EBB9A6"], [0.5, "#F7F5F0"], [0.75, "#8FCBC2"], [1, TEAL]]
COLORWAY = [TEAL, CORAL, GOLD, "#3B82A0", "#7A8F3C", "#8E5A9B", "#5B6770"]

pio.templates["xray"] = go.layout.Template(layout=dict(
    font=dict(family="Inter, system-ui, sans-serif", color=INK, size=12), colorway=COLORWAY, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=30, b=10), xaxis=dict(gridcolor="#EAE6DB", zeroline=False, linecolor=LINE, automargin=True), yaxis=dict(gridcolor="#EAE6DB", zeroline=False, linecolor=LINE, automargin=True),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title_text=""), hoverlabel=dict(bgcolor="white", bordercolor=LINE)))
pio.templates.default = "xray"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fraunces:wght@600;700&display=swap');
:root{--bg:#F7F5F0;--card:#fff;--line:#E6E1D6;--ink:#1F2A2E;--mut:#6B7780;--teal:#0F766E;--navy:#0f2a4a;--shadow:0 1px 2px rgba(15,23,42,.04),0 6px 18px rgba(15,23,42,.05);}
html,body,[class*="css"],.stApp{font-family:'Inter',system-ui,sans-serif;color:var(--ink);}
.stApp{background:var(--bg);} #MainMenu,footer{visibility:hidden;} header[data-testid="stHeader"]{background:transparent;}
.block-container{padding-top:1.3rem;padding-bottom:3rem;max-width:1300px;}
h1,h2,h3{font-family:'Fraunces',Georgia,serif;color:#134E4A;letter-spacing:-.01em;}
section[data-testid="stSidebar"]{background:#0f2a4a;}
section[data-testid="stSidebar"] *{color:#e2e8f0;}
section[data-testid="stSidebar"] .stRadio label p{font-size:.92rem;font-weight:500;}
section[data-testid="stSidebar"] [data-testid="stSelectbox"] div,section[data-testid="stSidebar"] [data-testid="stSelectbox"] input{background-color:#16365c!important;color:#f1f5f9!important;-webkit-text-fill-color:#f1f5f9!important;border-color:#2b4a73!important;}
section[data-testid="stSidebar"] [data-testid="stSelectbox"] svg{fill:#cbd5e1!important;}
section[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.12);}
section[data-testid="stSidebar"] .stCaption,section[data-testid="stSidebar"] small{color:#94a3b8!important;}
.brand{display:flex;align-items:center;gap:11px;font-weight:800;font-size:1.2rem;letter-spacing:-.02em;color:#fff;}
.brand .logo{width:34px;height:34px;border-radius:9px;display:grid;place-items:center;background:linear-gradient(135deg,#0F766E,#2dd4bf);color:#fff;font-size:1rem;}
.brand-sub{color:#94a3b8;font-size:.76rem;margin:2px 0 10px 45px;}
.hero{border-radius:16px;padding:20px 26px;margin-bottom:14px;color:#fff;background:linear-gradient(115deg,#0f2a4a 0%,#134E4A 70%,#0F766E 100%);box-shadow:var(--shadow);}
.hero .eyebrow{font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:#99f6e4;font-weight:700;}
.hero h1{color:#fff;font-size:1.7rem;font-weight:700;margin:.2rem 0 .1rem;padding:0;}
.hero p{color:#cbd5e1;margin:0;font-size:.93rem;}
.chip{display:inline-block;margin:8px 6px 0 0;padding:3px 11px;border-radius:999px;font-size:.73rem;font-weight:600;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);color:#ccfbf1;}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:11px 15px;box-shadow:var(--shadow);border-top:4px solid var(--c,#0F766E);}
.kpi .l{color:var(--mut);font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em}
.kpi .v{font-size:1.75rem;font-weight:800;line-height:1.15;color:var(--c,#0f2a4a)}
.kpi .s{color:#94a3b8;font-size:.73rem}
.badge{display:inline-block;padding:3px 11px;border-radius:999px;color:#fff;font-weight:700;font-size:.76rem}
.sec{margin:1.2rem 0 .1rem;font-size:1.08rem;font-weight:700;color:#134E4A;font-family:'Fraunces',Georgia,serif;}
.sec-sub{color:var(--mut);font-size:.85rem;margin-bottom:.5rem;}
.note{border-left:4px solid var(--teal);background:#ECFDF5;border-radius:8px;padding:9px 14px;margin:6px 0;font-size:.88rem;color:#134E4A;}
.flag,.good,.warn{border-radius:10px;padding:7px 12px;margin:4px 0;font-size:.86rem;border:1px solid;}
.flag{background:#fef2f2;border-color:#fecaca;color:#991b1b;}.good{background:#f0fdf4;border-color:#bbf7d0;color:#166534;}.warn{background:#fffbeb;border-color:#fde68a;color:#92400e;}
.stTabs [data-baseweb="tab-list"]{gap:2px;border-bottom:1px solid var(--line);flex-wrap:wrap;}
.stTabs [data-baseweb="tab"]{padding:8px 15px;font-weight:600;color:var(--mut);}
.stTabs [aria-selected="true"]{color:#134E4A!important;}
div[data-testid="stExpander"]{border:1px solid var(--line);border-radius:12px;background:#fff;}
section[data-testid="stSidebar"] div[data-testid="stExpander"]{background:transparent;border:1px solid rgba(255,255,255,.18);}
section[data-testid="stSidebar"] div[data-testid="stExpander"] *{color:#e2e8f0!important;}
.foot{color:#94a3b8;font-size:.75rem;text-align:center;margin-top:2rem;}
"""


def show(fig, key, height=None):
    if height:
        fig.update_layout(height=height)
    fig.update_layout(template="xray")
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False}, key=key)


def kpi(label, value, sub="", color=NAVY):
    return f"<div class='kpi' style='--c:{color}'><div class='l'>{label}</div><div class='v'>{value}</div><div class='s'>{sub}</div></div>"


def badge(band):
    return f"<span class='badge' style='background:{BAND_COLORS.get(band, '#64748b')}'>{band}</span>"


def section(title, sub=""):
    return f"<div class='sec'>{title}</div>" + (f"<div class='sec-sub'>{sub}</div>" if sub else "")


def tint(hex_color, a=.18):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{a})"


def _short(n):
    return n.replace(" Wellness", "").replace(" & ", " & ")


# ------------------------------------------------------------------------------------------ score charts
def gauge(score, title, band_name, lo=None, hi=None, height=240):
    steps = [dict(range=[a, b], color=tint(BAND_COLORS[n], .22)) for a, b, n in BAND_EDGES]
    fig = go.Figure(go.Indicator(mode="gauge+number", value=float(score), number=dict(font=dict(size=44, color=BAND_COLORS[band_name]), valueformat=".0f"),
                                 title=dict(text=title, font=dict(size=14, color=MUTED)),
                                 gauge=dict(axis=dict(range=[0, 100], tickwidth=1, tickcolor="#cbd5e1"), bar=dict(color=BAND_COLORS[band_name], thickness=.28), steps=steps, borderwidth=0)))
    fig.update_layout(height=height, margin=dict(l=30, r=30, t=50, b=5))
    return fig


def factor_bars(names, vals, ref=None, lo=None, hi=None):
    order = np.argsort(vals)
    n = [names[i] for i in order]
    v = [vals[i] for i in order]
    fig = go.Figure(go.Bar(x=v, y=n, orientation="h", name="This property", marker=dict(color=v, colorscale=SCALE, cmin=0, cmax=100), text=[f"{x:.0f}" for x in v], textposition="outside"))
    if ref is not None:
        fig.add_trace(go.Scatter(x=[ref[names[i]] for i in order], y=n, mode="markers", marker=dict(symbol="line-ns", size=16, color=INK, line=dict(width=2, color=INK)), name="Portfolio mean"))
    fig.update_xaxes(range=[0, 108], title="score (0-100)")
    fig.update_layout(height=max(240, 34 * len(n) + 60), showlegend=ref is not None)
    return fig


def radar(names, vals, ref=None):
    fig = go.Figure()
    full = names
    names = [n.replace(" Wellness", "").replace(" & ", " &<br>") for n in names]
    if ref is not None:
        ref = {a: ref[b] for a, b in zip(names, full)}
    fig.add_trace(go.Scatterpolar(r=list(vals) + [vals[0]], theta=names + [names[0]], fill="toself", name="This property", line=dict(color=TEAL, width=2.5), fillcolor=tint(TEAL, .2)))
    if ref is not None:
        r = [ref[x] for x in names]
        fig.add_trace(go.Scatterpolar(r=r + [r[0]], theta=names + [names[0]], name="Portfolio mean", line=dict(color="#94a3b8", dash="dot", width=2)))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100], tickfont=dict(size=9)), angularaxis=dict(tickfont=dict(size=10))), legend=dict(y=-0.1), height=380, margin=dict(l=80, r=80, t=20, b=30))
    return fig


def points_lost(names, losses, score):
    order = np.argsort(losses)[::-1]
    x = ["Ideal 100"] + [names[i] for i in order] + ["Score"]
    y = [100] + [-losses[i] for i in order] + [0]
    fig = go.Figure(go.Waterfall(x=x, y=y, measure=["absolute"] + ["relative"] * len(order) + ["total"], text=["100"] + [f"-{losses[i]:.1f}" for i in order] + [f"{score:.0f}"],
                                 textposition="outside", decreasing=dict(marker=dict(color=CORAL)), totals=dict(marker=dict(color=TEAL)), connector=dict(line=dict(color="#cbd5e1"))))
    fig.update_yaxes(range=[max(0, score - 15), 104], title="points")
    fig.update_xaxes(tickangle=-30)
    fig.update_layout(height=340, showlegend=False)
    return fig


def sunburst(run, row):
    ids, par, lab, val, col = [], [], [], [], []
    for c, r in run.results.items():
        wf = run.W.loc[row, c]
        if wf <= 0 or pd.isna(run.F.loc[row, c]):
            continue
        ids.append(c); par.append(""); lab.append(r.name); val.append(wf * 100); col.append(run.F.loc[row, c])
        for sub, cols in r.sub_map.items():
            sid = f"{c}|{sub}"
            ids.append(sid); par.append(c); lab.append(sub); val.append(wf * r.sub_weights[sub] * 100); col.append(r.sub_scores.loc[row, sub])
            wsub = r.weights.loc[cols, "final_weight"].values
            sh = wsub / wsub.sum() if wsub.sum() > 1e-12 else np.full(len(cols), 1 / len(cols))
            for cc, s_ in zip(cols, sh):
                ids.append(f"{sid}|{cc}"); par.append(sid); lab.append(cc.split(": ", 1)[1]); val.append(wf * r.sub_weights[sub] * s_ * 100); col.append(r.Xn.loc[row, cc])
    fig = go.Figure(go.Sunburst(ids=ids, parents=par, labels=lab, values=val, branchvalues="total", marker=dict(colors=col, colorscale=SCALE, cmin=0, cmax=100, line=dict(width=1, color="#fff")),
                                hovertemplate="%{label}<br>weight in score: %{value:.2f}%<extra></extra>", insidetextorientation="radial"))
    fig.update_layout(height=520, margin=dict(l=0, r=0, t=10, b=0))
    return fig


def distribution(vals, mine=None, color=TEAL, title="Score"):
    fig = go.Figure(go.Histogram(x=vals, nbinsx=20, marker=dict(color=tint(color, .45), line=dict(color=color, width=1))))
    for a, b, n in BAND_EDGES:
        fig.add_vrect(x0=a, x1=b, fillcolor=BAND_COLORS[n], opacity=.06, line_width=0)
    if mine is not None:
        fig.add_vline(x=mine, line=dict(color=INK, width=3), annotation_text=f"This property {mine:.0f}", annotation_position="top")
    fig.update_xaxes(range=[0, 100], title=title)
    fig.update_yaxes(title="properties")
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=30, b=10))
    return fig


def ranking(df, show_n="Top 25"):
    d = df.sort_values("score", ascending=(show_n == "Bottom 25")).head(25).iloc[::-1]
    fig = go.Figure()
    if (d["hi"] - d["lo"]).sum() > 0:
        fig.add_trace(go.Scatter(x=d["score"], y=d.index, mode="markers", error_x=dict(type="data", symmetric=False, array=d["hi"] - d["score"], arrayminus=d["score"] - d["lo"], color="#94a3b8"),
                                 marker=dict(size=8, color=[BAND_COLORS[b] for b in d["band"]]), showlegend=False))
    else:
        fig.add_trace(go.Bar(x=d["score"], y=d.index, orientation="h", marker=dict(color=[BAND_COLORS[b] for b in d["band"]])))
    fig.update_xaxes(range=[0, 100], title="score (bars = confidence interval when available)")
    fig.update_yaxes(type="category")
    fig.update_layout(height=620, showlegend=False)
    return fig


def zone_bars(df):
    z = df.groupby("Zone")["score"].agg(["mean", "min", "max"]).sort_values("mean")
    fig = go.Figure(go.Bar(x=z["mean"], y=z.index, orientation="h", marker=dict(color=z["mean"], colorscale=SCALE, cmin=0, cmax=100), text=[f"{v:.0f}" for v in z["mean"]], textposition="outside"))
    fig.update_xaxes(range=[0, 100], title="average score")
    fig.update_yaxes(type="category")
    fig.update_layout(height=max(280, 28 * len(z) + 60), showlegend=False)
    return fig


def heat(df: pd.DataFrame, zmin=-1, zmax=1, height=340, scale=None, fmt=".2f", mid=True):
    fig = go.Figure(go.Heatmap(z=df.values, x=list(df.columns), y=list(df.index), zmin=zmin, zmax=zmax, colorscale=scale or DIVERGING, text=np.round(df.values, 2),
                               texttemplate="%{text}", textfont=dict(size=9), hoverongaps=False))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(tickangle=-40, side="bottom")
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10))
    return fig


def scree(eig, k):
    x = np.arange(1, len(eig) + 1)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x, y=eig, marker_color=[TEAL if v > 1 else "#cbd5e1" for v in eig], name="Eigenvalue"))
    fig.add_trace(go.Scatter(x=x, y=np.cumsum(eig) / eig.sum() * 100, yaxis="y2", mode="lines+markers", line=dict(color=GOLD), name="Cumulative variance %"))
    fig.add_hline(y=1, line=dict(color=CORAL, dash="dash"), annotation_text="Kaiser: eigenvalue = 1")
    fig.update_layout(yaxis2=dict(overlaying="y", side="right", range=[0, 105], showgrid=False, title="%"), height=300)
    fig.update_xaxes(title="principal component", dtick=1 if len(eig) < 15 else 2)
    fig.update_yaxes(title="eigenvalue")
    return fig


def weight_bars(w: pd.DataFrame, title_col="parameter"):
    d = w.sort_values("final_weight")
    fig = go.Figure(go.Bar(x=d["final_weight"] * 100, y=d[title_col], orientation="h", marker_color=TEAL,
                           error_x=dict(type="data", symmetric=False, array=(d["ci_hi"] - d["final_weight"]).clip(lower=0) * 100, arrayminus=(d["final_weight"] - d["ci_lo"]).clip(lower=0) * 100, color=CORAL)))
    fig.update_xaxes(title="final weight in factor (%)  -  red whiskers = 95% bootstrap interval")
    fig.update_layout(height=max(300, 22 * len(d) + 60), showlegend=False)
    return fig


def before_after(raw, cleaned, scaled, label):
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=raw, name="Raw", marker_color=tint(CORAL, .6), nbinsx=20))
    fig.add_trace(go.Histogram(x=cleaned, name="Cleaned", marker_color=tint(TEAL, .6), nbinsx=20))
    fig.update_layout(barmode="overlay", height=260, xaxis_title=label)
    return fig, px.histogram(x=scaled, nbins=20, color_discrete_sequence=[TEAL]).update_layout(height=260, xaxis_title="Scaled score (0-100)", xaxis_range=[0, 100], showlegend=False)


def score_map(df, key_col="score"):
    d = df.dropna(subset=["Lat", "Lon"]).copy()
    d["Band"] = d["band"]
    fig = px.scatter_map(d, lat="Lat", lon="Lon", color="Band", color_discrete_map=BAND_COLORS, hover_name=d.index, hover_data={"score": ":.0f", "Zone": True, "Lat": False, "Lon": False, "Band": False},
                         zoom=9.5, map_style="open-street-map", category_orders={"Band": [b[2] for b in BAND_EDGES[::-1]]})
    fig.update_traces(marker=dict(size=11))
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=0, b=0))
    return fig
