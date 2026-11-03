"""Property X-Ray scoring engine (Trust | Wellness | Future Readiness).

Same pipeline as the original Wellness Score project, applied to every score:

  Raw parameters -> Data preprocessing (fill blanks, cap outliers, scale 0-100, flip direction)
  -> Correlation matrix -> PCA (Kaiser eigenvalue > 1) -> parameter weights (explained variance)
  -> Bootstrap (stability + confidence interval) -> Sub-factor scores -> Factor scores -> Overall score

Weighting options: Balanced (equal) | Data-driven (PCA explained variance) | Custom (user factor weights).
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

from .schema import BANDS, Model

warnings.filterwarnings("ignore")
MODES = ["Balanced", "Data-driven", "Custom"]


def band(score: float) -> str:
    if score is None or not np.isfinite(score):
        return "n/a"
    for thr, name in BANDS:
        if score >= thr:
            return name
    return "Poor"


def default_config(model: Model) -> pd.DataFrame:
    rows = []
    for code, f in model.hierarchy.items():
        lower = model.lower.get(code, set())
        for sub, labels in f["subs"].items():
            for lab in labels:
                col = f"{code}: {lab}"
                lo, hi = model.ranges.get(col, (0, 100))
                rows.append(dict(Code=code, Factor=f["name"], Subfactor=sub, Parameter=lab, Column=col, Unit=model.units.get(col, ""),
                                 Direction="lower" if lab in lower else "higher", Min=float(lo), Max=float(hi)))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------ statistics
def kmo_bartlett(R: np.ndarray, n: int) -> dict:
    p = R.shape[0]
    try:
        inv = np.linalg.pinv(R)
        d = np.sqrt(np.outer(np.diag(inv), np.diag(inv)))
        P = -inv / d
        np.fill_diagonal(P, 0)
        R0 = R.copy()
        np.fill_diagonal(R0, 0)
        kmo = float((R0 ** 2).sum() / ((R0 ** 2).sum() + (P ** 2).sum()))
        sign, logdet = np.linalg.slogdet(R)
        chi2 = float(-(n - 1 - (2 * p + 5) / 6) * logdet) if sign > 0 else np.nan
        pval = float(stats.chi2.sf(chi2, p * (p - 1) / 2)) if np.isfinite(chi2) else np.nan
    except Exception:
        kmo, chi2, pval = np.nan, np.nan, np.nan
    return dict(kmo=kmo, bartlett_chi2=chi2, bartlett_p=pval)


def kmo_label(k: float) -> str:
    if not np.isfinite(k):
        return "n/a"
    return ("marvellous" if k >= .9 else "meritorious" if k >= .8 else "middling" if k >= .7 else "mediocre" if k >= .6 else "poor" if k >= .5 else "unacceptable")


def pca_weights(X: np.ndarray) -> dict:
    """PCA explained-variance weights: correlation matrix -> eigen-decomposition -> keep components with eigenvalue > 1 (Kaiser)
    -> weight_j proportional to sum_k (explained variance ratio_k x loading_jk^2)."""
    n, m = X.shape
    w = np.zeros(m)
    sd = X.std(axis=0, ddof=1) if n > 1 else np.zeros(m)
    act = sd > 1e-9
    if m == 1 or act.sum() < 2 or n < 3:
        w[:] = 1 / m
        return dict(w=w, eig=np.ones(max(int(act.sum()), 1)), k=1, L=np.zeros((m, 1)), active=act)
    Z = (X[:, act] - X[:, act].mean(0)) / sd[act]
    R = np.nan_to_num(np.corrcoef(Z, rowvar=False))
    evals, evecs = np.linalg.eigh(R)
    order = np.argsort(evals)[::-1]
    evals, evecs = evals[order], evecs[:, order]
    k = max(1, int((evals > 1).sum()))
    evr = evals / evals.sum()
    wt = (evecs[:, :k] ** 2 * evr[:k]).sum(axis=1)
    w[act] = wt / wt.sum()
    L = np.zeros((m, k))
    L[act] = evecs[:, :k] * np.sqrt(np.clip(evals[:k], 0, None))
    return dict(w=w, eig=evals, k=k, L=L, active=act)


def _ev(S: np.ndarray) -> np.ndarray:
    return pca_weights(S)["w"]


def _sub_scores(X: np.ndarray, w: np.ndarray, groups: list) -> np.ndarray:
    cols = []
    for g in groups:
        wg = w[g]
        tot = wg.sum()
        cols.append((X[:, g] * wg).sum(1) / tot if tot > 1e-12 else X[:, g].mean(1))
    return np.column_stack(cols)


def _ci(boot: np.ndarray, level: float):
    a = (1 - level) / 2 * 100
    return np.percentile(boot, a, axis=0), np.percentile(boot, 100 - a, axis=0)


# ------------------------------------------------------------------------------------------ factor result
@dataclass
class FactorResult:
    code: str
    name: str
    columns: list
    sub_map: dict
    clean_stats: pd.DataFrame
    norm_stats: pd.DataFrame
    raw: pd.DataFrame
    cleaned: pd.DataFrame
    Xn: pd.DataFrame
    avail: pd.Series
    corr: pd.DataFrame
    eigenvalues: np.ndarray
    n_components: int
    loadings: pd.DataFrame
    weights: pd.DataFrame
    sub_scores: pd.DataFrame
    sub_weights: pd.Series
    score: pd.Series
    boot_scores: np.ndarray
    boot_w: np.ndarray
    boot_subw: np.ndarray
    diagnostics: dict
    data_driven: bool
    flags: list = field(default_factory=list)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess NEW rows with the fitted statistics."""
        num = df.reindex(columns=self.columns).apply(pd.to_numeric, errors="coerce")
        num = num.fillna(self.clean_stats["median"].reindex(self.columns))
        arr = np.clip(num.values, self.clean_stats["lo"].reindex(self.columns).values, self.clean_stats["hi"].reindex(self.columns).values)
        lo, hi = self.norm_stats["min"].reindex(self.columns).values, self.norm_stats["max"].reindex(self.columns).values
        rng = np.where(hi - lo == 0, np.nan, hi - lo)
        x = np.clip(np.nan_to_num((arr - lo) / rng * 100, nan=50.0), 0, 100)
        lower = (self.norm_stats["direction"].reindex(self.columns) == "lower").values
        x[:, lower] = 100 - x[:, lower]
        return pd.DataFrame(x, columns=self.columns, index=df.index)

    def apply(self, Xn: pd.DataFrame) -> dict:
        groups = [np.array([self.columns.index(c) for c in cols]) for cols in self.sub_map.values()]
        X = Xn[self.columns].values
        S = _sub_scores(X, self.weights["final_weight"].values, groups)
        score = S @ self.sub_weights.values
        boot = np.array([_sub_scores(X, self.boot_w[b], groups) @ self.boot_subw[b] for b in range(len(self.boot_w))]) if len(self.boot_w) else np.zeros((0, len(X)))
        return dict(sub_scores=pd.DataFrame(S, columns=list(self.sub_map), index=Xn.index), score=pd.Series(score, index=Xn.index), boot=boot)

    def ci(self, level=0.95):
        if len(self.boot_scores) == 0:
            return self.score.copy(), self.score.copy()
        lo, hi = _ci(self.boot_scores, level)
        return pd.Series(np.minimum(lo, self.score), index=self.score.index), pd.Series(np.maximum(hi, self.score), index=self.score.index)


def fit_factor(df: pd.DataFrame, model: Model, code: str, config: pd.DataFrame, boot_idx: np.ndarray, data_driven: bool):
    f = model.hierarchy[code]
    cfg = config[(config["Code"] == code) & (config["Column"].isin(df.columns))]
    if len(cfg) < 3:
        return None
    columns = list(cfg["Column"])
    sub_map = {sub: list(cfg.loc[cfg["Subfactor"] == sub, "Column"]) for sub in f["subs"] if (cfg["Subfactor"] == sub).any()}
    n = len(df)
    raw = df[columns].apply(pd.to_numeric, errors="coerce")
    avail = raw.notna().any(axis=1)
    if avail.sum() < 3 or raw.notna().sum().sum() == 0:
        return None

    # ---- Stage 1: data preprocessing (blank -> median, IQR cap, scale 0-100, flip direction)
    q1, q3 = raw.quantile(.25), raw.quantile(.75)
    iqr = q3 - q1
    fence_lo = np.where(iqr > 0, q1 - 1.5 * iqr, raw.min())
    fence_hi = np.where(iqr > 0, q3 + 1.5 * iqr, raw.max())
    clean_stats = pd.DataFrame({"median": raw.median(), "lo": fence_lo, "hi": fence_hi, "missing": raw.isna().sum(), "missing_pct": raw.isna().mean() * 100,
                                "outliers_clipped": ((raw < fence_lo) | (raw > fence_hi)).sum()}, index=columns)
    cleaned = raw.fillna(clean_stats["median"])
    cleaned = pd.DataFrame(np.clip(cleaned.values, fence_lo, fence_hi), columns=columns, index=df.index)
    cfg_i = cfg.set_index("Column")
    mn, mx = cfg_i["Min"].reindex(columns).astype(float), cfg_i["Max"].reindex(columns).astype(float)
    nmin, nmax = mn.fillna(cleaned.min()), mx.fillna(cleaned.max())
    norm_stats = pd.DataFrame({"min": nmin, "max": nmax, "direction": cfg_i["Direction"].reindex(columns),
                               "bounds": np.where(mn.notna() | mx.notna(), "benchmark", "data")}, index=columns)
    Xn = ((cleaned - nmin) / (nmax - nmin).replace(0, np.nan) * 100).fillna(50).clip(0, 100)
    lower_cols = [c for c in columns if norm_stats.loc[c, "direction"] == "lower"]
    Xn[lower_cols] = 100 - Xn[lower_cols]

    X = Xn.values
    p = X.shape[1]
    groups = [np.array([columns.index(c) for c in cols]) for cols in sub_map.values()]
    av = avail.values
    Xfit = X[av]

    # ---- Stage 2: correlation + PCA (always computed so diagnostics are visible)
    base = pca_weights(Xfit)
    corr = pd.DataFrame(np.nan_to_num(np.corrcoef(Xfit, rowvar=False)), index=columns, columns=columns)
    diag = kmo_bartlett(corr.values[np.ix_(base["active"], base["active"])], len(Xfit)) if base["active"].sum() > 1 else dict(kmo=np.nan, bartlett_chi2=np.nan, bartlett_p=np.nan)

    B = len(boot_idx) if data_driven else 0
    boot_w, boot_subw, boot_scores = np.zeros((B, p)), np.zeros((B, len(groups))), np.zeros((B, n))
    if data_driven:
        base_S = _sub_scores(Xfit, base["w"], groups)
        base_sw = _ev(base_S)
        for b in range(B):
            ix = boot_idx[b]
            ix = ix[av[ix]]
            try:
                Xb = X[ix]
                wb = pca_weights(Xb)["w"]
                swb = _ev(_sub_scores(Xb, wb, groups))
            except Exception:
                wb, swb = base["w"], base_sw
            boot_w[b], boot_subw[b] = wb, swb
            boot_scores[b] = _sub_scores(X, wb, groups) @ swb
        w_final = boot_w.mean(0)
        w_final = w_final / w_final.sum()
        wlo, whi, wstd = np.percentile(boot_w, 2.5, axis=0), np.percentile(boot_w, 97.5, axis=0), boot_w.std(0)
        S = _sub_scores(X, w_final, groups)
        sw_final = _ev(_sub_scores(Xfit, w_final, groups))
    else:
        w_final = np.full(p, 1 / p)
        wlo = whi = w_final
        wstd = np.zeros(p)
        S = _sub_scores(X, w_final, groups)
        sw_final = np.full(len(groups), 1 / len(groups))
    score = S @ sw_final
    score[~av] = np.nan
    S[~av] = np.nan

    short = [c.split(": ", 1)[1] for c in columns]
    weights = pd.DataFrame({"parameter": short, "subfactor": [next(s for s, cs in sub_map.items() if c in cs) for c in columns],
                            "direction": norm_stats["direction"].values, "pca_weight": base["w"], "bootstrap_std": wstd, "ci_lo": wlo, "ci_hi": whi,
                            "cv": np.where(w_final > 0, wstd / np.maximum(w_final, 1e-12), np.nan), "final_weight": w_final}, index=columns)
    k = base["k"]
    loadings = pd.DataFrame(base["L"], index=columns, columns=[f"PC{i + 1}" for i in range(k)])
    res = FactorResult(code=code, name=f["name"], columns=columns, sub_map=sub_map, clean_stats=clean_stats, norm_stats=norm_stats, raw=raw, cleaned=cleaned, Xn=Xn,
                       avail=avail, corr=corr, eigenvalues=base["eig"], n_components=k, loadings=loadings, weights=weights,
                       sub_scores=pd.DataFrame(S, columns=list(sub_map), index=df.index), sub_weights=pd.Series(sw_final, index=list(sub_map)),
                       score=pd.Series(score, index=df.index), boot_scores=boot_scores, boot_w=boot_w, boot_subw=boot_subw, diagnostics=diag, data_driven=data_driven)
    res.flags = diagnose(res, int(av.sum()))
    return res


def diagnose(r: FactorResult, n: int) -> list:
    flags, p = [], len(r.columns)
    cs = r.clean_stats
    for c in cs.index[cs["missing_pct"] > 10]:
        flags.append(("medium", f"'{c}' has {cs.loc[c, 'missing_pct']:.0f}% missing values (median-filled)."))
    for c in cs.index[cs["outliers_clipped"] > max(3, 0.05 * n)]:
        flags.append(("medium", f"'{c}' had {int(cs.loc[c, 'outliers_clipped'])} outliers capped (more than 5% of rows)."))
    zero = [c for c in r.columns if r.Xn[c].std() < 1e-9]
    if zero:
        flags.append(("high", f"Constant parameters (carry no information): {', '.join(zero[:6])}"))
    if not r.data_driven:
        return flags
    if n < 5 * p:
        flags.append(("high", f"Sample size is small for PCA (n={n}, p={p}, n/p={n / p:.1f}; rule of thumb 5-10 or more). Weights may be unstable."))
    k = r.diagnostics.get("kmo")
    if k is not None and np.isfinite(k):
        if k < 0.5:
            flags.append(("high", f"KMO = {k:.2f} (below 0.50): the parameters are not suitable for PCA."))
        elif k < 0.6:
            flags.append(("medium", f"KMO = {k:.2f}: only mediocre sampling adequacy."))
    bp = r.diagnostics.get("bartlett_p")
    if bp is not None and np.isfinite(bp) and bp > 0.05:
        flags.append(("high", f"Bartlett's test p = {bp:.3f}: the correlation matrix is not different from an identity matrix."))
    cm = r.corr.values
    for i, j in zip(*np.triu_indices(p, 1)):
        if abs(cm[i, j]) > 0.9:
            flags.append(("medium", f"Near-duplicate parameters (r={cm[i, j]:.2f}): '{r.columns[i]}' and '{r.columns[j]}'."))
    w = r.weights["final_weight"]
    if w.max() > 0.15:
        flags.append(("medium", f"Weight dominance: '{w.idxmax()}' carries {w.max() * 100:.1f}% of the factor weight."))
    unstable = int(((r.weights["cv"] > 0.6) & (r.weights["final_weight"] > 0)).sum())
    if unstable:
        flags.append(("medium", f"{unstable} parameter weights are unstable under bootstrap (variation above 60% of the weight)."))
    for sub, cols in r.sub_map.items():
        if len(cols) > 1:
            sc = r.corr.loc[cols, cols].values
            for i, c in enumerate(cols):
                m = (sc[i].sum() - 1) / (len(cols) - 1)
                if m < -0.1:
                    flags.append(("medium", f"'{c}' correlates NEGATIVELY with its sub-factor peers (mean r={m:.2f}); check its direction (higher / lower is better)."))
    return flags


# ------------------------------------------------------------------------------------------ run one model
@dataclass
class Run:
    model: Model
    mode: str
    results: dict
    F: pd.DataFrame            # factor scores (n x m, NaN where not applicable)
    fw: pd.Series              # factor weights (global)
    W: pd.DataFrame            # effective factor weights per property (n x m)
    overall: pd.Series
    lo: pd.Series
    hi: pd.Series
    level: float
    has_ci: bool
    factor_eig: np.ndarray | None = None

    @property
    def data_driven_flag(self):
        return self.mode == "Data-driven"


def _row_weights(w: np.ndarray, avail: np.ndarray) -> np.ndarray:
    W = w[None, :] * avail
    tot = W.sum(1, keepdims=True)
    return np.where(tot > 0, W / np.where(tot == 0, 1, tot), 0)


def run_model(df: pd.DataFrame, model: Model, config: pd.DataFrame, mode: str = "Balanced", custom: dict | None = None, B: int = 100, level: float = 0.95, seed: int = 7) -> Run:
    rng = np.random.default_rng(seed)
    data_driven = mode == "Data-driven"
    boot_idx = rng.integers(0, len(df), size=(B, len(df)))
    results = {}
    for code in model.hierarchy:
        r = fit_factor(df, model, code, config, boot_idx, data_driven)
        if r is not None:
            results[code] = r
    if not results:
        return None
    codes = list(results)
    F = pd.DataFrame({c: results[c].score for c in codes})
    av = F.notna().values.astype(float)
    Fi = F.apply(lambda s: s.fillna(s.mean()))
    if mode == "Data-driven":
        w = _ev(Fi.values)
    elif mode == "Custom" and custom:
        w = np.array([max(float(custom.get(c, 0)), 0) for c in codes])
        w = w / w.sum() if w.sum() > 0 else np.full(len(codes), 1 / len(codes))
    else:
        w = np.full(len(codes), 1 / len(codes))
    Wr = _row_weights(w, av)
    overall = pd.Series(np.nansum(F.values * Wr, axis=1), index=F.index, name=model.title)
    lo = hi = overall.copy()
    has_ci = False
    if data_driven and B > 0:
        boots = np.stack([results[c].boot_scores for c in codes], axis=2)       # B x n x m
        ob = np.zeros((B, len(F)))
        for b in range(B):
            Fb = boots[b]
            wb = _ev(np.where(np.isnan(Fb), np.nanmean(Fb, axis=0), Fb))
            ob[b] = np.nansum(Fb * _row_weights(wb, av), axis=1)
        l_, h_ = _ci(ob, level)
        lo, hi = pd.Series(np.minimum(l_, overall.values), index=F.index), pd.Series(np.maximum(h_, overall.values), index=F.index)
        has_ci = True
    return Run(model, mode, results, F, pd.Series(w, index=codes), pd.DataFrame(Wr, index=F.index, columns=codes), overall, lo, hi, level, has_ci)


# ------------------------------------------------------------------------------------------ traces (every number shown comes from here)
def parameter_trace(r: FactorResult, row, col: str) -> pd.DataFrame:
    raw = r.raw.loc[row, col]
    cs, ns = r.clean_stats.loc[col], r.norm_stats.loc[col]
    missing = bool(pd.isna(raw))
    filled = float(cs["median"]) if missing else float(raw)
    cleaned = float(np.clip(filled, cs["lo"], cs["hi"]))
    capped = (not missing) and abs(cleaned - filled) > 1e-12
    span = float(ns["max"] - ns["min"])
    scaled = 50.0 if span == 0 else float(np.clip((cleaned - ns["min"]) / span * 100, 0, 100))
    lower = ns["direction"] == "lower"
    final = 100 - scaled if lower else scaled
    rows = [
        ("1  Raw value", "The value as it appears in the data.", "blank (missing)" if missing else f"{raw:,.2f}", "blank" if missing else f"{raw:,.2f}"),
        ("2  Fill blank", "A missing value is replaced by the median of this parameter over all properties.", f"median = {cs['median']:,.2f}" if missing else "not needed", f"{filled:,.2f}"),
        ("3  Cap outliers", "Values outside the IQR limits (Q1 - 1.5 x IQR, Q3 + 1.5 x IQR) are pulled back to the nearest limit.",
         f"allowed range {cs['lo']:,.2f} to {cs['hi']:,.2f}" + ("  ->  capped" if capped else "  ->  within range"), f"{cleaned:,.2f}"),
        ("4  Scale to 0-100", "(value - min) / (max - min) x 100 using " + ("the benchmark min / max." if ns["bounds"] == "benchmark" else "the smallest / largest cleaned values in the data."),
         f"({cleaned:,.2f} - {ns['min']:,.2f}) / ({ns['max']:,.2f} - {ns['min']:,.2f}) x 100" if span else "min = max, so 50 is used", f"{scaled:.1f}"),
        ("5  Flip if lower is better", "Where a LOWER value is better the score is turned around so 100 is always best.", f"100 - {scaled:.1f}" if lower else "not needed", f"{final:.1f}")]
    return pd.DataFrame(rows, columns=["Step", "What happens", "Calculation", "Result"])


def subfactor_trace(r: FactorResult, row, sub: str) -> pd.DataFrame:
    cols = r.sub_map[sub]
    x = r.Xn.loc[row, cols].values.astype(float)
    w = r.weights.loc[cols, "final_weight"].values.astype(float)
    wn = w / w.sum() if w.sum() > 1e-12 else np.full(len(cols), 1 / len(cols))
    df = pd.DataFrame({"Parameter": [c.split(": ", 1)[1] for c in cols], "Score (0-100)": x, "Weight in factor (%)": w * 100, "Weight in sub-factor (%)": wn * 100, "Score x weight": x * wn})
    df.loc[len(df)] = ["Sub-factor score", np.nan, np.nan, 100.0, float((x * wn).sum())]
    return df


def factor_trace(r: FactorResult, row) -> pd.DataFrame:
    subs = list(r.sub_map)
    s_, w = r.sub_scores.loc[row, subs].values.astype(float), r.sub_weights.loc[subs].values.astype(float)
    df = pd.DataFrame({"Sub-factor": subs, "Score (0-100)": s_, "Weight (%)": w * 100, "Score x weight": s_ * w})
    df.loc[len(df)] = [f"{r.name} score", np.nan, 100.0, float(np.nansum(s_ * w))]
    return df


def overall_trace(run: Run, row) -> pd.DataFrame:
    names = {c: run.model.hierarchy[c]["name"] for c in run.F.columns}
    sc, w = run.F.loc[row].values.astype(float), run.W.loc[row].values.astype(float)
    df = pd.DataFrame({"Factor": [names[c] for c in run.F.columns], "Score (0-100)": sc, "Weight (%)": w * 100, "Score x weight": np.nan_to_num(sc) * w})
    df.loc[len(df)] = [run.model.title, np.nan, 100.0, float(np.nansum(sc * w))]
    return df


def weight_trace(r: FactorResult, col: str) -> pd.DataFrame:
    k = r.n_components
    ev = r.eigenvalues
    evr = ev / ev.sum()
    L = r.loadings.loc[col].values
    rows = [("Components kept (eigenvalue > 1)", f"{k}", "Kaiser rule: components that explain more than one parameter's worth of variance."),
            ("Eigenvalues of kept components", ", ".join(f"{v:.2f}" for v in ev[:k]), "From the correlation matrix of this factor's parameters."),
            ("Explained variance ratio", ", ".join(f"{v * 100:.1f}%" for v in evr[:k]), "Eigenvalue / total variance."),
            ("Loadings of this parameter", ", ".join(f"{v:.2f}" for v in L), "Correlation of the parameter with each kept component."),
            ("Weight (PCA) = sum of EVR x squared eigenvector, rescaled", f"{r.weights.loc[col, 'pca_weight'] * 100:.2f}%", "Share of the factor's weight from the full data."),
            (f"Bootstrap average (FINAL weight)", f"{r.weights.loc[col, 'final_weight'] * 100:.2f}%", f"Average over {len(r.boot_w)} resamples; spread = {r.weights.loc[col, 'bootstrap_std'] * 100:.2f} points." if len(r.boot_w) else "Equal weights (Balanced / Custom).")]
    return pd.DataFrame(rows, columns=["Step", "Value", "Meaning"])


def find_interesting(r: FactorResult):
    na = r.raw.isna()
    if na.values.any():
        i, j = np.argwhere(na.values)[0]
        return r.raw.index[i], r.raw.columns[j]
    capped = r.raw.notna() & ((r.raw - r.cleaned).abs() > 1e-12)
    if capped.values.any():
        i, j = np.argwhere(capped.values)[0]
        return r.raw.index[i], r.raw.columns[j]
    return r.raw.index[0], r.raw.columns[0]


def drags(run: Run, row, top=5):
    """Biggest parameter drags: points lost out of 100 (exact: effective weight x (100 - score))."""
    out = []
    for c, r in run.results.items():
        wf = run.W.loc[row, c]
        if wf == 0:
            continue
        for sub, cols in r.sub_map.items():
            wsub = r.weights.loc[cols, "final_weight"].values
            share = wsub / wsub.sum() if wsub.sum() > 1e-12 else np.full(len(cols), 1 / len(cols))
            for col, sh in zip(cols, share):
                x = r.Xn.loc[row, col]
                out.append((col, r.sub_weights[sub] * sh * wf * (100 - x), x, r.name))
    out.sort(key=lambda t: -t[1])
    return out[:top], sum(o[1] for o in out)


# ------------------------------------------------------------------------------------------ explanations
def explain_factor(r: FactorResult, run: Run) -> str:
    n, p = r.Xn.shape
    cs, w = r.clean_stats, r.weights.sort_values("final_weight", ascending=False)
    lo, hi = r.ci(run.level)
    var_k = r.eigenvalues[:r.n_components].sum() / r.eigenvalues.sum() * 100
    kmo = r.diagnostics["kmo"]
    n_low = int((r.norm_stats["direction"] == "lower").sum())
    n_bench = int((r.norm_stats["bounds"] == "benchmark").sum())
    L = [f"### {r.name}: how the score was derived", f"**The data.** {n} properties x {p} parameters, grouped into {len(r.sub_map)} sub-factors.",
         "#### Stage 1 - Data preprocessing",
         f"**Missing values:** {int(cs['missing'].sum())} blank cells were filled with the median of their parameter.",
         f"**Outliers:** {int(cs['outliers_clipped'].sum())} values outside the IQR limits (Q1 - 1.5 x IQR to Q3 + 1.5 x IQR) were pulled back to the nearest limit.",
         f"**Scaling:** every parameter was converted to a 0-100 score with (value - min) / (max - min) x 100; {n_bench} parameter(s) use benchmark min / max, the rest use the data. "
         f"{n_low} parameter(s) are 'lower is better' and were flipped (100 - score), so 100 always means best.", "#### Stage 2 - Weights"]
    if r.data_driven:
        L += [f"**Suitability.** KMO = {kmo:.2f} ({kmo_label(kmo)}); Bartlett's test p = {r.diagnostics['bartlett_p']:.3g}.",
              f"**PCA.** {r.n_components} component(s) with eigenvalue above 1 were kept, explaining about {var_k:.0f}% of the variation. A parameter's weight is the sum over kept components of "
              "(explained variance ratio x squared eigenvector value), rescaled to 100%.",
              f"**Bootstrap.** The PCA was repeated on {len(r.boot_w)} random resamples of the properties; the final weight is the average and the spread gives the confidence interval.",
              "**Largest final weights:** " + "; ".join(f"{i.split(': ', 1)[1]} {v * 100:.1f}%" for i, v in w["final_weight"].head(5).items())]
    else:
        L += [f"Weighting mode is **{run.mode}**: every parameter has the same weight inside its sub-factor and every sub-factor the same weight inside the factor."]
    L += ["#### Stage 3 - Building the scores",
          "**Sub-factor score** = weighted average of its parameters' scores. **Factor score** = sum of sub-factor weight x sub-factor score. "
          f"Mean {r.score.mean():.1f} (lowest {r.score.min():.1f}, highest {r.score.max():.1f}); average {run.level * 100:.0f}% confidence-interval width {(hi - lo).mean():.1f} points."]
    L.append("**Possible problems detected:**\n" + "\n".join(f"- ({s}) {m}" for s, m in r.flags) if r.flags else "**No automatic data-quality flags were raised.**")
    return "\n\n".join(L)


def explain_property(run: Run, row) -> str:
    o = run.overall[row]
    head = f"### Property {row}: {run.model.title} **{o:.1f}** ({band(o)})"
    if run.has_ci:
        head += f", {run.level * 100:.0f}% confidence interval [{run.lo[row]:.1f}, {run.hi[row]:.1f}]"
    L = [head, f"Weighting used: **{run.mode}**.", "**Factor scores (score x weight):**"]
    for c in run.F.columns:
        v = run.F.loc[row, c]
        L.append(f"- {run.model.hierarchy[c]['name']}: " + ("not applicable / no data" if pd.isna(v) else f"{v:.1f} x {run.W.loc[row, c] * 100:.1f}% = {v * run.W.loc[row, c]:.1f} points"))
    subs = [(r.name, s_, r.sub_scores.loc[row, s_]) for r in run.results.values() for s_ in r.sub_map if pd.notna(r.sub_scores.loc[row, s_])]
    subs.sort(key=lambda t: t[2])
    L.append("**Weakest sub-factors:** " + "; ".join(f"{a} / {b} {v:.0f}" for a, b, v in subs[:3]))
    L.append("**Strongest sub-factors:** " + "; ".join(f"{a} / {b} {v:.0f}" for a, b, v in subs[-3:][::-1]))
    dr, tot = drags(run, row)
    L.append("**Biggest drags (points lost out of 100):** " + "; ".join(f"{c} ({pts:.2f} points, scored {v:.0f}/100)" for c, pts, v, _ in dr))
    L.append(f"*Check: all parameters together lose {tot:.1f} points, and 100 - {o:.1f} = {100 - o:.1f}.*")
    return "\n\n".join(L)


# ------------------------------------------------------------------------------------------ new properties
def score_new(run: Run, df_new: pd.DataFrame):
    codes = list(run.results)
    F, boots, subs = {}, [], {}
    for c in codes:
        r = run.results[c]
        has = df_new.reindex(columns=r.columns).apply(pd.to_numeric, errors="coerce").notna().any(axis=1)
        a = r.apply(r.transform(df_new))
        sc = a["score"].copy()
        sc[~has] = np.nan
        F[c] = sc
        boots.append(a["boot"])
        subs[c] = a["sub_scores"]
    F = pd.DataFrame(F)
    av = F.notna().values.astype(float)
    Wr = _row_weights(run.fw.reindex(codes).values, av)
    overall = pd.Series(np.nansum(F.values * Wr, axis=1), index=F.index, name=run.model.title)
    lo = hi = overall.copy()
    if run.has_ci and boots and boots[0].shape[0]:
        ob = np.stack(boots, axis=2) @ run.fw.reindex(codes).values
        l_, h_ = _ci(ob, run.level)
        lo, hi = pd.Series(np.minimum(l_, overall.values), index=F.index), pd.Series(np.maximum(h_, overall.values), index=F.index)
    return F, overall, lo, hi, subs
