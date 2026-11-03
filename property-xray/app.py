"""Property X-Ray - Trust Score | Wellness Score | Future Readiness Score."""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from xray import data as D  # noqa: E402
from xray import engine as E  # noqa: E402
from xray import method as M  # noqa: E402
from xray import schema as S  # noqa: E402
from xray import theme as T  # noqa: E402

st.set_page_config(page_title="Property X-Ray", page_icon="🏠", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"<style>{T.CSS}</style>", unsafe_allow_html=True)

PAGES = ["Overview", "Trust Score", "Wellness Score", "Future Readiness Score", "Data & Upload", "Method"]
KEY_OF = {"Trust Score": "trust", "Wellness Score": "wellness", "Future Readiness Score": "future"}
PAGE_OF = {v: k for k, v in KEY_OF.items()}
TABS = ["Data & settings", "Factor pipeline", "Overall score", "Score a new property", "Explanation", "Method"]


# ------------------------------------------------------------------------------------------ state
@st.cache_data(show_spinner=False)
def demo(n=100, seed=42, messy=True):
    return dict(df=D.generate_sample_data(n, seed, messy), tx=D.synthetic_transactions(), infra=D.synthetic_infra())


@st.cache_data(show_spinner="Fitting the model ...", max_entries=24)
def fit(key, df, cfg, mode, custom_t, B, level):
    return E.run_model(df, S.MODELS[key], cfg, mode, dict(custom_t) if custom_t else None, B, level)


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = D.normalise_columns(df)
    if "Property_ID" not in df.columns:
        df.insert(0, "Property_ID", [f"P{i + 1:03d}" for i in range(len(df))])
    df["Property_ID"] = df["Property_ID"].astype(str)
    for c in ("Zone", "Property_type", "Project_status"):
        if c not in df.columns:
            df[c] = "-"
    for c in ("Lat", "Lon"):
        df[c] = pd.to_numeric(df[c], errors="coerce") if c in df.columns else np.nan
    return df.set_index("Property_ID", drop=False)


def set_data(df, tx, infra, source):
    st.session_state.data = dict(df=prepare(df), tx=tx, infra=infra, source=source)
    st.session_state.cfg = {k: E.default_config(S.MODELS[k]) for k in S.ORDER}
    st.session_state.pop("pid", None)


if "data" not in st.session_state:
    b = demo()
    set_data(b["df"].copy(), b["tx"].copy(), b["infra"].copy(), "Synthetic sample")
st.session_state.setdefault("page", PAGES[0])
st.session_state.setdefault("scheme", "Balanced")


def goto(p):
    st.session_state.page = p


DATA = st.session_state.data
df, tx, infra = DATA["df"], DATA["tx"], DATA["infra"]
CFG = st.session_state.cfg

# ------------------------------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown("<div class='brand'><div class='logo'>▣</div>Property X-Ray</div><div class='brand-sub'>Built-asset intelligence</div>", unsafe_allow_html=True)
    st.radio("Navigate", PAGES, key="page", label_visibility="collapsed")
    st.divider()
    pid = st.selectbox("Property", list(df.index), format_func=lambda i: f"{i} · {df.loc[i, 'Property_type']} · {df.loc[i, 'Zone']}", key="pid")
    st.divider()
    st.markdown("**Weighting**")
    mode = st.radio("How should the factors be weighted?", E.MODES, key="scheme", label_visibility="collapsed",
                    help="Balanced: equal weights.  Data-driven: PCA explained variance computed from the data.  Custom: your own factor weights.")
    st.caption({"Balanced": "Equal weights at every level.", "Data-driven": "PCA explained-variance weights learned from the data.", "Custom": "You choose the factor weights (0-3)."}[mode])
    custom = {}
    if mode == "Custom":
        for k in S.ORDER:
            with st.expander(S.MODELS[k].title, expanded=False):
                custom[k] = {c: st.slider(f["name"], 0.0, 3.0, 1.0, 0.1, key=f"cw_{k}_{c}") for c, f in S.MODELS[k].hierarchy.items()}
    with st.expander("Advanced"):
        B = st.slider("Bootstrap resamples", 20, 300, 100, 20, key="B")
        level = st.selectbox("Confidence level", [0.90, 0.95, 0.99], index=1, format_func=lambda v: f"{v:.0%}", key="level")
    st.divider()
    st.caption(f"{DATA['source']} · {len(df)} properties")

RUNS = {k: fit(k, df, CFG[k], mode, tuple(sorted(custom.get(k, {}).items())) if mode == "Custom" else None, B, level) for k in S.ORDER}


# ------------------------------------------------------------------------------------------ helpers
def hero(title, sub="", eyebrow="Property X-Ray", chips=()):
    ch = "".join(f"<span class='chip'>{c}</span>" for c in chips if c and str(c) != "-")
    st.markdown(f"<div class='hero'><div class='eyebrow'>{eyebrow}</div><h1>{title}</h1><p>{sub}</p>{ch}</div>", unsafe_allow_html=True)


def prop_chips():
    r = df.loc[pid]
    price = r.get("Price_psf")
    return [r.get("Property_type"), r.get("Project_status"), f"Zone {r.get('Zone')}", f"₹{price:,.0f} / sq ft" if pd.notna(price) else None]


def pct_rank(run):
    return float((run.overall < run.overall[pid]).mean() * 100)


def ci_text(run):
    return f"{run.level:.0%} interval {run.lo[pid]:.0f}–{run.hi[pid]:.0f}" if run.has_ci else "no interval (fixed weights)"


def portfolio(run):
    d = pd.DataFrame({"score": run.overall, "lo": run.lo, "hi": run.hi}, index=run.overall.index)
    d["band"] = d["score"].map(E.band)
    for c in ("Zone", "Property_type", "Lat", "Lon"):
        d[c] = df[c]
    return d


def names_of(run):
    return {c: run.model.hierarchy[c]["name"] for c in run.F.columns}


def need_data(key):
    st.warning(f"No factor of the {S.MODELS[key].title} has enough parameter columns (at least 3 per factor) in the loaded data. Add them in **Data & Upload** or use the sample data.")


# ------------------------------------------------------------------------------------------ overview
def page_overview():
    hero(f"Property {pid}", "Three scores on one 0–100 scale, built with the same method: Factor → Sub-factor → Parameter.", f"Overview · weighting: {mode}", prop_chips())
    cols = st.columns(3)
    for col, k in zip(cols, S.ORDER):
        run = RUNS[k]
        with col:
            if run is None:
                st.info(f"{S.MODELS[k].title}: no data."); continue
            sc = run.overall[pid]
            T.show(T.gauge(sc, S.MODELS[k].title, E.band(sc)), f"ov_g_{k}")
            st.markdown(f"{T.badge(E.band(sc))} &nbsp;<small>{ci_text(run)} · top {max(100 - pct_rank(run), 1):.0f}% of {len(df)}</small>", unsafe_allow_html=True)
            st.button(f"Open {S.MODELS[k].title}", key=f"open_{k}", on_click=goto, args=(PAGE_OF[k],), width="stretch")
    st.markdown(T.section("Factor scores", "Bars = this property · black tick = portfolio mean. Colour follows the score (green = strong)"), unsafe_allow_html=True)
    cols = st.columns(3)
    for col, k in zip(cols, S.ORDER):
        run = RUNS[k]
        if run is None:
            continue
        nm = names_of(run)
        v = run.F.loc[pid].dropna()
        with col:
            st.markdown(f"**{S.MODELS[k].title}**")
            T.show(T.factor_bars([nm[c] for c in v.index], list(v.values), {nm[c]: run.F[c].mean() for c in v.index}), f"ov_f_{k}")
    st.markdown(T.section("Biggest drags", "Parameters that cost this property the most points (weight × shortfall)"), unsafe_allow_html=True)
    cols = st.columns(3)
    for col, k in zip(cols, S.ORDER):
        run = RUNS[k]
        if run is None:
            continue
        top, tot = E.drags(run, pid, 5)
        with col:
            st.markdown(f"**{S.MODELS[k].title}**")
            for c, pts, v, fn in top:
                st.markdown(f"<div class='warn'><b>{c.split(': ', 1)[1]}</b> · {fn}<br>{pts:.2f} points lost · scored {v:.0f}/100</div>", unsafe_allow_html=True)
    st.markdown(T.section("Portfolio", "All properties scored with the same model"), unsafe_allow_html=True)
    tab = pd.DataFrame({"Zone": df["Zone"], "Type": df["Property_type"]})
    for k in S.ORDER:
        if RUNS[k] is not None:
            tab[S.MODELS[k].short] = RUNS[k].overall
    f1, f2 = st.columns(2)
    ty = f1.multiselect("Property type", S.PROPERTY_TYPES, default=[t for t in S.PROPERTY_TYPES if t in set(tab["Type"])] or None)
    zn = f2.multiselect("Zone", sorted(tab["Zone"].astype(str).unique()))
    v = tab[tab["Type"].isin(ty)] if ty else tab
    if zn:
        v = v[v["Zone"].astype(str).isin(zn)]
    pc = lambda lab: st.column_config.ProgressColumn(lab, min_value=0, max_value=100, format="%.0f")
    st.dataframe(v, width="stretch", height=300, column_config={S.MODELS[k].short: pc(S.MODELS[k].short) for k in S.ORDER if S.MODELS[k].short in v.columns})
    a, b = st.columns(2)
    ks = [k for k in S.ORDER if RUNS[k] is not None]
    if len(ks) >= 2 and len(v):
        with a:
            st.markdown("**Trust vs Wellness** (bubble = Future Readiness)" if len(ks) == 3 else "**Score comparison**")
            sz = v[S.MODELS["future"].short].clip(lower=5) if "Future Readiness" in v.columns else None
            fig = px.scatter(v.reset_index(), x=S.MODELS[ks[0]].short, y=S.MODELS[ks[1]].short, size=sz.values if sz is not None else None, color="Type", hover_name="Property_ID",
                             size_max=18, range_x=[0, 100], range_y=[0, 100])
            T.show(fig, "ov_sc", 380)
        with b:
            st.markdown("**Average score by zone**")
            z = v.groupby("Zone")[[S.MODELS[k].short for k in ks]].mean().round(0)
            T.show(T.heat(z.T, 0, 100, 380, T.SCALE), "ov_zone")


# ------------------------------------------------------------------------------------------ score page tabs
def tab_data(key, run):
    m = S.MODELS[key]
    cfg = CFG[key]
    st.markdown(T.section("Data coverage", f"{len(df)} properties loaded from: {DATA['source']}"), unsafe_allow_html=True)
    rows = []
    for code, f in m.hierarchy.items():
        exp = [c for c in m.columns() if c.startswith(f"{code}: ")]
        have = [c for c in exp if c in df.columns]
        filled = df[have].notna().mean().mean() * 100 if have else 0
        rows.append(dict(Factor=f["name"], Code=code, Subfactors=len(f["subs"]), Parameters=len(exp), Present=len(have), **{"Filled %": round(filled, 1)},
                         Status="fitted" if run is not None and code in run.results else "needs 3+ parameters"))
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", column_config={"Filled %": st.column_config.ProgressColumn("Filled %", min_value=0, max_value=100, format="%.0f")})
    st.markdown("<div class='note'>Load or generate data in <b>Data & Upload</b>. A factor is fitted when at least three of its parameter columns are present; blank cells are filled with the median.</div>", unsafe_allow_html=True)
    st.markdown(T.section("Data preview"), unsafe_allow_html=True)
    cols = [c for c in m.columns() if c in df.columns]
    st.dataframe(df[["Zone", "Property_type"] + cols].head(100), width="stretch", height=260)
    st.markdown(T.section("Parameter configuration", "Direction and benchmark Min / Max used for scaling. Leave Min / Max blank to use the smallest / largest value in the data."), unsafe_allow_html=True)
    view = cfg[["Factor", "Subfactor", "Parameter", "Unit", "Direction", "Min", "Max"]]
    ed = st.data_editor(view, hide_index=True, width="stretch", height=380, key=f"cfg_{key}", disabled=["Factor", "Subfactor", "Parameter", "Unit"],
                        column_config={"Direction": st.column_config.SelectboxColumn("Direction (better is…)", options=["higher", "lower"], required=True)})
    c1, c2, _ = st.columns([1, 1, 3])
    if c1.button("Apply configuration", key=f"apply_{key}", type="primary"):
        new = cfg.copy()
        for c in ("Direction", "Min", "Max"):
            new[c] = ed[c].values
        st.session_state.cfg[key] = new
        st.rerun()
    if c2.button("Reset to default", key=f"reset_{key}"):
        st.session_state.cfg[key] = E.default_config(m)
        st.rerun()


def tab_pipeline(key, run):
    codes = list(run.results)
    nm = names_of(run)
    code = st.selectbox("Factor to inspect", codes, format_func=lambda c: f"{nm[c]}  ({c})", key=f"fp_{key}")
    r = run.results[code]
    kmo = r.diagnostics["kmo"]
    c = st.columns(5)
    c[0].markdown(T.kpi("Properties used", f"{int(r.avail.sum())}", f"of {len(r.avail)}"), unsafe_allow_html=True)
    c[1].markdown(T.kpi("Parameters", f"{len(r.columns)}", f"{len(r.sub_map)} sub-factors"), unsafe_allow_html=True)
    c[2].markdown(T.kpi("KMO", f"{kmo:.2f}" if np.isfinite(kmo) else "n/a", E.kmo_label(kmo)), unsafe_allow_html=True)
    c[3].markdown(T.kpi("PCA components", f"{r.n_components}", "eigenvalue > 1"), unsafe_allow_html=True)
    c[4].markdown(T.kpi("Mean factor score", f"{r.score.mean():.1f}", f"range {r.score.min():.0f}–{r.score.max():.0f}", T.TEAL), unsafe_allow_html=True)
    for sev, msg in r.flags[:6]:
        st.markdown(f"<div class='{'flag' if sev == 'high' else 'warn'}'>{msg}</div>", unsafe_allow_html=True)
    st.caption("Read top to bottom: Stage 1 prepares the numbers, Stage 2 decides how much each parameter counts, Stage 3 builds the scores.")

    st.markdown(T.section("Stage 1 · Data preprocessing", "Fill blanks → cap outliers → scale 0–100 → flip where lower is better"), unsafe_allow_html=True)
    tb = r.clean_stats.join(r.norm_stats)
    tb.insert(0, "Parameter", [x.split(": ", 1)[1] for x in tb.index])
    st.dataframe(tb[["Parameter", "direction", "min", "max", "bounds", "median", "missing_pct", "outliers_clipped"]].rename(columns={"direction": "Better is", "min": "Min", "max": "Max", "bounds": "Bounds from",
                 "median": "Median", "missing_pct": "Missing %", "outliers_clipped": "Outliers capped"}).round(2), hide_index=True, width="stretch", height=260)
    c1, c2 = st.columns(2)
    p_ = c1.selectbox("Parameter", r.columns, format_func=lambda x: x.split(": ", 1)[1], key=f"fpp_{key}_{code}")
    ri, rj = E.find_interesting(r)
    row_ = c2.selectbox("Property", list(r.raw.index), index=list(r.raw.index).index(pid) if pid in r.raw.index else 0, key=f"fpr_{key}_{code}")
    g1, g2 = T.before_after(r.raw[p_].dropna(), r.cleaned[p_], r.Xn[p_], p_.split(": ", 1)[1])
    a, b = st.columns(2)
    with a:
        T.show(g1, f"ba1_{key}_{code}")
    with b:
        T.show(g2, f"ba2_{key}_{code}")
    st.dataframe(E.parameter_trace(r, row_, p_), hide_index=True, width="stretch")

    st.markdown(T.section("Stage 2 · Correlation, PCA and weights", "Weights come from PCA explained variance" if run.data_driven_flag else f"Mode is {run.mode}: equal weights are used. The PCA below is shown for reference; select Data-driven in the sidebar to use it."),
                unsafe_allow_html=True)
    short = [x.split(": ", 1)[1][:22] for x in r.columns]
    a, b = st.columns([1.2, 1])
    with a:
        st.markdown("**Correlation matrix**")
        cm = r.corr.copy(); cm.index = short; cm.columns = short
        T.show(T.heat(cm, -1, 1, max(320, 22 * len(short))), f"corr_{key}_{code}")
    with b:
        st.markdown("**Eigenvalues (scree plot)**")
        T.show(T.scree(r.eigenvalues, r.n_components), f"scree_{key}_{code}")
        st.markdown("**PCA loadings**")
        ld = r.loadings.copy(); ld.index = short
        T.show(T.heat(ld, -1, 1, max(260, 20 * len(short))), f"load_{key}_{code}")
    if r.data_driven:
        st.markdown("**Final parameter weights** (bootstrap average, with interval)")
        T.show(T.weight_bars(r.weights), f"wb_{key}_{code}")
        wt = r.weights[["parameter", "subfactor", "pca_weight", "final_weight", "ci_lo", "ci_hi", "cv"]].copy()
        for cc in ("pca_weight", "final_weight", "ci_lo", "ci_hi"):
            wt[cc] = wt[cc] * 100
        st.dataframe(wt.rename(columns={"pca_weight": "PCA weight %", "final_weight": "FINAL weight %", "ci_lo": "Interval low %", "ci_hi": "Interval high %", "cv": "Variation (CV)"}).round(2), hide_index=True, width="stretch", height=260)
        pw = st.selectbox("Show the weight calculation for parameter", r.columns, format_func=lambda x: x.split(": ", 1)[1], key=f"wtp_{key}_{code}")
        st.dataframe(E.weight_trace(r, pw), hide_index=True, width="stretch")

    st.markdown(T.section("Stage 3 · Building the scores", "Parameters → sub-factor score → factor score"), unsafe_allow_html=True)
    a, b = st.columns(2)
    with a:
        st.markdown("**Sub-factor scores across properties**")
        fig = px.box(r.sub_scores.melt(var_name="Sub-factor", value_name="Score").dropna(), x="Score", y="Sub-factor", color_discrete_sequence=[T.TEAL], range_x=[0, 100])
        T.show(fig, f"sbox_{key}_{code}", max(260, 40 * len(r.sub_map) + 60))
    with b:
        st.markdown("**Sub-factor weights**")
        sw = r.sub_weights.sort_values()
        fig = px.bar(x=sw.values * 100, y=sw.index, orientation="h", color_discrete_sequence=[T.GOLD], labels={"x": "weight in factor (%)", "y": ""})
        T.show(fig, f"sw_{key}_{code}", max(260, 40 * len(r.sub_map) + 60))
    sub = st.selectbox("Show the calculation for sub-factor", list(r.sub_map), key=f"sub_{key}_{code}")
    st.markdown(f"**Sub-factor score for property {row_}**")
    st.dataframe(E.subfactor_trace(r, row_, sub).round(2), hide_index=True, width="stretch")
    st.markdown(f"**{r.name} score for property {row_}**")
    st.dataframe(E.factor_trace(r, row_).round(2), hide_index=True, width="stretch")


def tab_overall(key, run):
    m = S.MODELS[key]
    nm = names_of(run)
    sc = run.overall[pid]
    band = E.band(sc)
    a, b = st.columns([1, 1.4])
    with a:
        T.show(T.gauge(sc, f"{m.title} · {pid}", band), f"og_{key}")
        st.markdown(f"{T.badge(band)} &nbsp;<small>{ci_text(run)} · percentile {pct_rank(run):.0f}</small>", unsafe_allow_html=True)
    with b:
        v = run.F.loc[pid].dropna()
        ref = {nm[c]: run.F[c].mean() for c in v.index}
        T.show(T.factor_bars([nm[c] for c in v.index], list(v.values), ref), f"ofb_{key}")
    a, b = st.columns(2)
    with a:
        st.markdown("**Points lost by factor** (weight × shortfall)")
        loss = [run.W.loc[pid, c] * (100 - run.F.loc[pid, c]) for c in v.index]
        T.show(T.points_lost([nm[c] for c in v.index], loss, sc), f"opl_{key}")
    with b:
        if len(v) >= 3:
            st.markdown("**Profile vs portfolio mean**")
            T.show(T.radar([nm[c] for c in v.index], list(v.values), ref), f"orad_{key}")
    with st.expander("Weight map: factor → sub-factor → parameter (size = weight, colour = score)"):
        T.show(T.sunburst(run, pid), f"osun_{key}")
    st.markdown(T.section("How the overall score is calculated", "Factor score × factor weight"), unsafe_allow_html=True)
    st.dataframe(E.overall_trace(run, pid).round(2), hide_index=True, width="stretch")
    st.markdown(T.section("Portfolio view", f"Where property {pid} sits among {len(df)} properties"), unsafe_allow_html=True)
    pf = portfolio(run)
    a, b = st.columns(2)
    with a:
        st.markdown("**Distribution of scores**")
        T.show(T.distribution(pf["score"], sc, T.SCORE_COLORS[key], m.title), f"od_{key}")
    with b:
        st.markdown("**Average score by zone**")
        T.show(T.zone_bars(pf), f"oz_{key}")
    a, b = st.columns(2)
    with a:
        st.markdown("**Ranking**")
        sn = st.radio("Properties to show", ["Top 25", "Bottom 25"], horizontal=True, key=f"orank_{key}")
        T.show(T.ranking(pf, sn), f"orr_{key}")
    with b:
        st.markdown("**Score by property type**")
        T.show(px.box(pf.reset_index(), x="Property_type", y="score", color="Property_type", points="all", range_y=[0, 100], color_discrete_sequence=T.COLORWAY), f"obx_{key}", 300)
        if pf["Lat"].notna().any():
            st.markdown("**Map**")
            T.show(T.score_map(pf), f"omap_{key}")
    st.markdown(T.section("Factor weights used", f"Weighting: {run.mode}"), unsafe_allow_html=True)
    fw = pd.DataFrame({"Factor": [nm[c] for c in run.fw.index], "Weight %": run.fw.values * 100, "Mean score": [run.F[c].mean() for c in run.fw.index]})
    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.dataframe(fw.round(1), hide_index=True, width="stretch")
    with c2:
        if len(run.fw) > 1:
            st.markdown("**Correlation between factor scores**")
            cc = run.F.corr().fillna(0); cc.index = [nm[c][:22] for c in cc.index]; cc.columns = cc.index
            T.show(T.heat(cc, -1, 1, 340), f"ofc_{key}")
    st.download_button("Download all scores (CSV)", pd.concat([run.F.rename(columns=nm), run.overall.rename(m.title), run.lo.rename("CI low"), run.hi.rename("CI high")], axis=1).round(2).to_csv(),
                       f"{key}_scores.csv", "text/csv", key=f"dl_{key}")


def tab_new(key, run):
    m = S.MODELS[key]
    st.markdown("<div class='note'>The reference data you loaded is used to <b>learn</b> the cleaning limits, scaling, weights and bootstrap weights. Here a <b>new</b> property is scored with those fixed rules, so it does not change the model.</div>", unsafe_allow_html=True)
    how = st.radio("How do you want to provide the property?", ["Type values for one property", "Upload a file with new properties"], horizontal=True, key=f"nh_{key}")
    if how.startswith("Type"):
        vals = {}
        for code, r in run.results.items():
            with st.expander(f"{r.name}", expanded=False):
                use = st.checkbox("Provide values for this factor", value=True, key=f"nu_{key}_{code}")
                for sub, cols in r.sub_map.items():
                    st.markdown(f"**{sub}**")
                    cc = st.columns(3)
                    for i, col in enumerate(cols):
                        med = float(r.clean_stats.loc[col, "median"])
                        unit = m.units.get(col, "")
                        vals[col] = cc[i % 3].number_input(f"{col.split(': ', 1)[1]}" + (f" ({unit})" if unit else ""), value=round(med, 2), key=f"nv_{key}_{col}", disabled=not use) if use else np.nan
        if st.button("Score this property", type="primary", key=f"nb_{key}"):
            new = pd.DataFrame([vals], index=["New property"])
            F, ov, lo, hi, subs = E.score_new(run, new)
            sc = ov.iloc[0]
            a, b = st.columns([1, 1.4])
            with a:
                T.show(T.gauge(sc, m.title, E.band(sc)), f"ng_{key}")
                st.markdown(f"{T.badge(E.band(sc))} &nbsp;<small>{f'{run.level:.0%} interval {lo.iloc[0]:.0f}–{hi.iloc[0]:.0f}' if run.has_ci else ''}</small>", unsafe_allow_html=True)
            with b:
                v = F.iloc[0].dropna()
                T.show(T.factor_bars([names_of(run)[c] for c in v.index], list(v.values)), f"nf_{key}")
            st.dataframe(pd.concat({names_of(run)[c]: subs[c].T[ "New property"] for c in subs}, axis=0).rename("Score").reset_index().rename(columns={"level_0": "Factor", "level_1": "Sub-factor"}).round(1), hide_index=True, width="stretch")
    else:
        nf = st.file_uploader("New properties (same column names as the template)", type=["csv", "xlsx", "xls"], key=f"nfile_{key}")
        if nf is not None:
            nd = prepare(D.read_upload(nf))
            F, ov, lo, hi, subs = E.score_new(run, nd)
            out = pd.concat([F.rename(columns=names_of(run)), ov.rename(m.title), lo.rename("CI low"), hi.rename("CI high")], axis=1).round(1)
            out["Band"] = ov.map(E.band)
            st.dataframe(out, width="stretch")
            st.download_button("Download results (CSV)", out.to_csv(), f"{key}_new_scores.csv", "text/csv", key=f"ndl_{key}")


def tab_explain(key, run):
    scope = st.radio("What should be explained?", ["One factor (preprocessing, weights, scores)", f"The {S.MODELS[key].title} of one property"], horizontal=True, key=f"ex_{key}")
    if scope.startswith("One"):
        nm = names_of(run)
        c = st.selectbox("Factor", list(run.results), format_func=lambda x: nm[x], key=f"exf_{key}")
        st.markdown(E.explain_factor(run.results[c], run))
    else:
        p2 = st.selectbox("Property", list(df.index), index=list(df.index).index(pid), key=f"exp_{key}")
        st.markdown(E.explain_property(run, p2))
        st.dataframe(E.overall_trace(run, p2).round(2), hide_index=True, width="stretch")


def tab_method(key):
    st.markdown(M.model_text(key))
    with st.expander("Full method (applies to all three scores)", expanded=True):
        st.markdown(M.common())


def page_score(key):
    run = RUNS[key]
    m = S.MODELS[key]
    hero(m.title, m.describes, f"Property {pid} · weighting: {mode}", prop_chips())
    if run is None:
        need_data(key)
        tabs = st.tabs(TABS)
        with tabs[0]:
            tab_data(key, None)
        with tabs[5]:
            tab_method(key)
        return
    sc = run.overall[pid]
    k = st.columns(4)
    k[0].markdown(T.kpi(m.title, f"{sc:.0f}", E.band(sc), T.BAND_COLORS[E.band(sc)]), unsafe_allow_html=True)
    k[1].markdown(T.kpi("Confidence interval", f"{run.lo[pid]:.0f}–{run.hi[pid]:.0f}" if run.has_ci else "n/a", f"{run.level:.0%}" if run.has_ci else "Data-driven weights only"), unsafe_allow_html=True)
    k[2].markdown(T.kpi("Percentile", f"{pct_rank(run):.0f}", f"among {len(df)} properties"), unsafe_allow_html=True)
    k[3].markdown(T.kpi("Factors scored", f"{int(run.F.loc[pid].notna().sum())}", f"of {len(run.F.columns)}"), unsafe_allow_html=True)
    tabs = st.tabs(TABS)
    with tabs[0]:
        tab_data(key, run)
    with tabs[1]:
        tab_pipeline(key, run)
    with tabs[2]:
        tab_overall(key, run)
    with tabs[3]:
        tab_new(key, run)
    with tabs[4]:
        tab_explain(key, run)
    with tabs[5]:
        tab_method(key)


# ------------------------------------------------------------------------------------------ data & upload
def page_data():
    hero("Data & Upload", "Generate the synthetic sample or upload your own file. One row per property, one column per parameter, named exactly like the template (for example TIT: Verified chain length).")
    if st.session_state.get("flash"):
        st.success(st.session_state.pop("flash"))
    t1, t2, t3 = st.tabs(["Load data", "Templates", "View & dictionary"])
    with t1:
        src = st.radio("Data source", ["Synthetic sample", "Upload file"], horizontal=True)
        if src == "Synthetic sample":
            c = st.columns(3)
            n = c[0].slider("Properties", 30, 400, 100, 10)
            seed = c[1].number_input("Random seed", 0, 9999, 42)
            messy = c[2].checkbox("Include blanks and outliers", True)
            if st.button("Generate sample data", type="primary"):
                b = demo(n, int(seed), messy)
                set_data(b["df"].copy(), b["tx"].copy(), b["infra"].copy(), f"Synthetic sample (n={n})")
                st.session_state.flash = f"Generated {n} synthetic properties."
                st.rerun()
        else:
            up = st.file_uploader("Properties file (CSV or Excel)", type=["csv", "xlsx", "xls"])
            c1, c2 = st.columns(2)
            tup = c1.file_uploader("Optional: transactions file (locality, year, avg_psf, txn_count)", type=["csv"])
            iup = c2.file_uploader("Optional: infrastructure file (project_id, category, status, completion_year, lat, lon)", type=["csv"])
            if st.button("Validate & load", type="primary", disabled=up is None):
                try:
                    raw = D.normalise_columns(D.read_upload(up))
                    v = D.validate(raw)
                    for e in v["errors"]:
                        st.error(e)
                    for w in v["warnings"]:
                        st.warning(w)
                    if not v["errors"]:
                        t_ = pd.read_csv(tup) if tup else pd.DataFrame(columns=["locality", "year", "avg_psf", "txn_count"])
                        i_ = pd.read_csv(iup) if iup else pd.DataFrame(columns=["project_id", "category", "status", "completion_year", "lat", "lon"])
                        if tup or iup:
                            raw = D.apply_derived(raw, t_, i_, overwrite=False)
                        set_data(raw, t_, i_, f"Uploaded: {up.name}")
                        st.session_state.flash = f"Loaded {len(raw)} properties from {up.name}."
                        st.rerun()
                except Exception as ex:  # noqa: BLE001
                    st.error(f"Could not read the file: {ex}")
        st.markdown("<div class='note'>A score is computed for every factor that has at least three of its parameter columns. Blank cells are filled with the median. "
                    "Leave the STR columns blank for plots: the Structural &amp; MEP factor is then left out for those properties.</div>", unsafe_allow_html=True)
    with t2:
        b = demo()
        blank = pd.DataFrame(columns=S.ID_COLS + D.ALL_PARAM_COLS)
        a, c, d = st.columns(3)
        a.download_button("Properties - blank template (CSV)", blank.to_csv(index=False), "properties_template.csv", "text/csv", width="stretch")
        a.download_button("Properties - example (10 rows)", b["df"].head(10).to_csv(index=False), "properties_example.csv", "text/csv", width="stretch")
        c.download_button("Transactions - example", b["tx"].to_csv(index=False), "transactions_example.csv", "text/csv", width="stretch")
        d.download_button("Infrastructure - example", b["infra"].to_csv(index=False), "infrastructure_example.csv", "text/csv", width="stretch")
        st.markdown("Infrastructure categories: " + ", ".join(f"`{k}`" for k in D.INFRA_CATEGORIES) + "  \nStatuses: " + ", ".join(f"`{k}`" for k in D.INFRA_STATUS_P))
    with t3:
        st.dataframe(df, width="stretch", height=320)
        dd = D.data_dictionary()
        st.markdown(T.section("Data dictionary", "Every parameter, its unit, benchmark range and direction"), unsafe_allow_html=True)
        st.dataframe(dd, hide_index=True, width="stretch", height=380)
        st.download_button("Download data dictionary (CSV)", dd.to_csv(index=False), "data_dictionary.csv", "text/csv")


def page_method():
    hero("Method", "How every score is built: preprocessing → correlation → PCA weights → bootstrap → sub-factor, factor and overall scores")
    st.graphviz_chart(M.FLOW)
    t = st.tabs(["Pipeline & weighting", "Trust parameters", "Wellness parameters", "Future Readiness parameters"])
    with t[0]:
        st.markdown(M.common())
    for tab, k in zip(t[1:], S.ORDER):
        with tab:
            st.markdown(M.model_text(k))
    st.download_button("Download methodology (Markdown)", M.build(), "METHODOLOGY.md", "text/markdown")


page = st.session_state.page
if page == "Overview":
    page_overview()
elif page in KEY_OF:
    page_score(KEY_OF[page])
elif page == "Data & Upload":
    page_data()
else:
    page_method()
st.markdown("<div class='foot'>Property X-Ray · scores are data-dependent indices, not certified ratings · sample data is synthetic</div>", unsafe_allow_html=True)
