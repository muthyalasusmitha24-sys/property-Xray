"""Synthetic data (ids and codes only), derived features from transaction / infrastructure files, and upload validation."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
from scipy import stats

from .schema import ID_COLS, MODELS, ORDER, PROPERTY_TYPES

AS_OF_YEAR = dt.date.today().year
OFFSET = {"trust": 0.35, "wellness": 0.15, "future": 0.2}
ALL_PARAM_COLS = [c for k in ORDER for c in MODELS[k].columns()]

# zone code -> (lat, lon, price per sq ft, growth, services, jobs)   (illustrative, not real measurements)
ZONES = {
    "L01": (13.0067, 80.2570, 14500, .45, .85, .55), "L02": (13.0850, 80.2101, 13800, .40, .90, .55), "L03": (13.0418, 80.2341, 16500, .35, .95, .60),
    "L04": (13.0368, 80.2676, 17000, .40, .92, .55), "L05": (12.9815, 80.2180, 9800, .55, .80, .70), "L06": (13.0067, 80.2206, 10500, .45, .80, .75),
    "L07": (12.9010, 80.2279, 7600, .80, .65, .90), "L08": (12.9654, 80.2461, 8800, .65, .70, .85), "L09": (13.0382, 80.1565, 7900, .75, .70, .65),
    "L10": (12.9249, 80.1000, 6200, .65, .65, .50), "L11": (12.9200, 80.1920, 6400, .70, .55, .60), "L12": (12.8467, 80.2265, 5600, .85, .45, .80),
    "L13": (13.1143, 80.1548, 6800, .50, .65, .70)}

INFRA_CATEGORIES = {"Metro / rail": (9, 3.0, "transit"), "Expressway / ring road": (8, 5.0, "road"), "Arterial road / flyover": (5, 2.0, "road"), "Airport": (9, 12.0, "air"),
                    "Bus terminus / ISBT": (5, 4.0, "air"), "IT park / SEZ / business district": (8, 5.0, "biz"), "Industrial corridor": (6, 6.0, "biz"),
                    "Healthcare / education hub": (5, 3.0, "civic"), "Water / drainage / flood control": (6, 4.0, "water"), "Public realm / smart city": (4, 2.0, "water"),
                    "Nuisance (waste / power plant)": (-6, 3.0, "nuisance")}
INFRA_STATUS_P = {"Completed": 1.0, "Under construction": 0.90, "Approved - funded": 0.65, "Proposed": 0.30, "Stalled": 0.10}
INFRA_SEED = [("Metro / rail", "Under construction", 2027, 13.0382, 80.1565), ("Metro / rail", "Under construction", 2027, 13.0500, 80.2121),
              ("Metro / rail", "Under construction", 2028, 12.9010, 80.2279), ("Metro / rail", "Under construction", 2028, 12.9654, 80.2461),
              ("Metro / rail", "Approved - funded", 2030, 12.9249, 80.1000), ("Metro / rail", "Proposed", 2031, 12.9815, 80.2180), ("Metro / rail", "Stalled", 2026, 12.9900, 80.2200),
              ("Expressway / ring road", "Under construction", 2027, 12.9000, 80.0700), ("Expressway / ring road", "Approved - funded", 2029, 13.0700, 80.2000),
              ("Expressway / ring road", "Proposed", 2031, 12.9300, 80.2330), ("Airport", "Completed", 2024, 12.9941, 80.1709), ("Bus terminus / ISBT", "Completed", 2023, 12.8440, 80.0810),
              ("IT park / SEZ / business district", "Under construction", 2027, 12.8467, 80.2265), ("IT park / SEZ / business district", "Completed", 2022, 12.9650, 80.2500),
              ("Industrial corridor", "Under construction", 2026, 13.1143, 80.1548), ("Water / drainage / flood control", "Under construction", 2026, 13.0067, 80.2480),
              ("Water / drainage / flood control", "Under construction", 2027, 12.9815, 80.2200), ("Nuisance (waste / power plant)", "Completed", 2000, 12.9560, 80.2400),
              ("Public realm / smart city", "Completed", 2022, 13.0418, 80.2341), ("Healthcare / education hub", "Approved - funded", 2029, 13.0850, 80.2101)]


# ------------------------------------------------------------------------------------------ derived features
def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((np.radians(lon2) - np.radians(lon1)) / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def project_effects(lat, lon, infra: pd.DataFrame) -> pd.DataFrame:
    """Each project's contribution to one property: impact x P(delivery) x distance decay x time discount."""
    if infra is None or len(infra) == 0:
        return pd.DataFrame()
    d = infra[infra["category"].isin(INFRA_CATEGORIES) & infra["status"].isin(INFRA_STATUS_P)].copy()
    if d.empty:
        return pd.DataFrame()
    d["dist_km"] = haversine_km(lat, lon, d["lat"].astype(float).values, d["lon"].astype(float).values)
    d["group"] = d["category"].map(lambda c: INFRA_CATEGORIES[c][2])
    d["impact"] = d["category"].map(lambda c: INFRA_CATEGORIES[c][0])
    if "impact" in infra.columns:
        d["impact"] = pd.to_numeric(infra.loc[d.index, "impact"], errors="coerce").fillna(d["impact"])
    d["radius_km"] = d["category"].map(lambda c: INFRA_CATEGORIES[c][1])
    d["p_delivery"] = d["status"].map(INFRA_STATUS_P)
    d["decay"] = np.exp(-(d["dist_km"] / d["radius_km"]) ** 2)
    yrs = (pd.to_numeric(d["completion_year"], errors="coerce") - AS_OF_YEAR).clip(lower=0) if "completion_year" in d.columns else pd.Series(3.0, index=d.index)
    yrs = yrs.fillna(3)
    yrs[d["status"] == "Completed"] = 0
    d["time_disc"] = 1 / 1.08 ** yrs
    pos = d["impact"] > 0
    priced = np.where(pos & (d["status"] == "Completed"), 0.6, 1.0)
    c = d["impact"] / 10 * d["p_delivery"] * d["decay"] * d["time_disc"] * priced
    d["contribution"] = np.where(pos, c, c * 1.5)
    return d.sort_values("contribution", key=lambda s: s.abs(), ascending=False)


def _cagr(a, b, n):
    return np.nan if n <= 0 or not a or not b or a <= 0 or b <= 0 else ((b / a) ** (1 / n) - 1) * 100


def apply_derived(df: pd.DataFrame, tx: pd.DataFrame | None, infra: pd.DataFrame | None, overwrite=False) -> pd.DataFrame:
    """Fill Historical-Transaction and Planned-Infrastructure parameters from the transaction / infrastructure files."""
    out = df.copy()

    def put(col, i, v):
        if col in out.columns and (overwrite or pd.isna(out.at[i, col])):
            out.at[i, col] = v

    loc_stats = {}
    if tx is not None and len(tx) and {"locality", "year", "avg_psf", "txn_count"} <= set(tx.columns):
        t = tx.copy()
        for c in ("year", "avg_psf", "txn_count"):
            t[c] = pd.to_numeric(t[c], errors="coerce")
        for loc, g in t.dropna(subset=["year", "avg_psf"]).groupby("locality"):
            g = g.sort_values("year")
            psf, cnt = g["avg_psf"].values, g["txn_count"].values
            n5, n3 = min(5, len(g) - 1), min(3, len(g) - 1)
            if n3 < 2:
                continue
            yoy = np.diff(psf) / psf[:-1] * 100
            st = {"5-year price CAGR": _cagr(psf[-1 - n5], psf[-1], n5) if n5 >= 3 else np.nan, "3-year price CAGR": _cagr(psf[-1 - n3], psf[-1], n3),
                  "Price volatility": float(np.std(yoy[-5:], ddof=1)) if len(yoy) > 2 else np.nan, "Worst-year price fall": float(max(0, -yoy.min())),
                  "Price-growth consistency": float((yoy > 0).mean() * 100), "Transactions per year": float(cnt[-1]),
                  "Transaction volume trend": _cagr(cnt[-1 - n5], cnt[-1], n5) if n5 >= 3 else np.nan, "_psf": float(psf[-1])}
            loc_stats[loc] = st
    for i, r in out.iterrows():
        st = loc_stats.get(r.get("Zone"))
        if st:
            for k, v in st.items():
                if k != "_psf":
                    put(f"HST: {k}", i, v)
            if pd.notna(r.get("Price_psf")) and st["_psf"] > 0:
                put("HST: Price vs micro-market average", i, float(r["Price_psf"]) / st["_psf"])
        if infra is not None and len(infra) and pd.notna(r.get("Lat")) and pd.notna(r.get("Lon")):
            e = project_effects(float(r["Lat"]), float(r["Lon"]), infra)
            if e.empty:
                continue
            g = lambda grp: float(max(e.loc[e["group"] == grp, "contribution"].sum(), 0))
            tr = e[e["group"] == "transit"]
            rd = e[e["group"] == "road"]
            near = e[(e["dist_km"] <= 5) & (e["status"] != "Completed") & (e["impact"] > 0)]
            put("INF: Metro / rail influence", i, g("transit"))
            put("INF: Distance to nearest planned transit", i, float(tr["dist_km"].min()) if len(tr) else np.nan)
            put("INF: Delivery confidence of transit projects", i, float(tr.loc[tr["dist_km"] <= 10, "p_delivery"].mean() * 100) if (tr["dist_km"] <= 10).any() else np.nan)
            put("INF: Road / expressway influence", i, g("road"))
            put("INF: Distance to nearest road project", i, float(rd["dist_km"].min()) if len(rd) else np.nan)
            put("INF: Airport / bus-terminus influence", i, g("air"))
            put("INF: Business-park / SEZ influence", i, g("biz"))
            put("INF: Healthcare & education influence", i, g("civic"))
            put("INF: Water, drainage & public-realm influence", i, g("water"))
            put("INF: Stalled projects within 3 km", i, int(((e["status"] == "Stalled") & (e["dist_km"] <= 3) & (e["impact"] > 0)).sum()))
            put("INF: Nuisance projects within 3 km", i, int(((e["impact"] < 0) & (e["dist_km"] <= 3)).sum()))
            if len(near):
                yrs = (pd.to_numeric(near["completion_year"], errors="coerce") - AS_OF_YEAR).clip(lower=0)
                put("INF: Average delay of nearby projects", i, float(yrs.mean()) if yrs.notna().any() else np.nan)
    return out


# ------------------------------------------------------------------------------------------ synthetic data
def synthetic_infra() -> pd.DataFrame:
    df = pd.DataFrame(INFRA_SEED, columns=["category", "status", "completion_year", "lat", "lon"])
    df.insert(0, "project_id", [f"I{i + 1:02d}" for i in range(len(df))])
    return df


def synthetic_transactions(seed=11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for loc, (lat, lon, psf_now, growth, serv, jobs) in ZONES.items():
        g = 0.01 + 0.15 * growth
        psf = [psf_now]
        for y in range(2025, 2018, -1):
            psf.insert(0, psf[0] / (1 + g + rng.normal(0, .02 + .02 * (1 - serv)) - (0.07 if y == 2020 else 0)))
        vol0 = 150 + 1100 * (0.5 * serv + 0.5 * jobs)
        for y, p in zip(range(2018, 2026), psf):
            trend = 1 + 0.10 * growth * (y - 2018) - (0.30 if y == 2020 else 0)
            rows.append((loc, y, round(p), int(max(20, vol0 * trend * rng.normal(1, .08)))))
    return pd.DataFrame(rows, columns=["locality", "year", "avg_psf", "txn_count"])


def generate_sample_data(n=100, seed=42, messy=True) -> pd.DataFrame:
    """Synthetic properties with a latent structure (overall quality, zone effect, factor and sub-factor effects) so PCA finds real patterns."""
    rng = np.random.default_rng(seed)
    zones = list(ZONES)
    u_zone = {z: rng.normal() for z in zones}
    g = rng.normal(size=n)
    zone = rng.choice(zones, size=n)
    ptype = rng.choice(PROPERTY_TYPES, size=n, p=[.55, .20, .25])
    df = pd.DataFrame({"Property_ID": [f"P{i + 1:03d}" for i in range(n)], "Zone": zone, "Property_type": ptype,
                       "Project_status": np.where((ptype == "Plot") | (rng.random(n) < .6), "Ready", "Under construction"),
                       "Lat": [round(ZONES[z][0] + rng.normal(0, .008), 5) for z in zone], "Lon": [round(ZONES[z][1] + rng.normal(0, .008), 5) for z in zone],
                       "Price_psf": [round(ZONES[z][2] * rng.normal(1, .08) / 100) * 100 for z in zone]})
    uz = np.array([u_zone[z] for z in zone])
    cols = {}
    for k in ORDER:
        m = MODELS[k]
        for code, f in m.hierarchy.items():
            fl = rng.normal(size=n)
            for sub, labels in f["subs"].items():
                sl = rng.normal(size=n)
                for lab in labels:
                    c = f"{code}: {lab}"
                    z = 0.25 * g + 0.40 * uz + 0.35 * fl + 0.60 * sl + 0.55 * rng.normal(size=n)
                    z = (z - z.mean()) / z.std() + OFFSET[k]
                    q = stats.norm.cdf(z)
                    lo, hi = m.ranges[c]
                    raw = lo + (hi - lo) * ((1 - q) if lab in m.lower.get(code, set()) else q)
                    unit = m.units.get(c, "")
                    cols[c] = np.round(raw) if unit in ("count", "zone", "days", "months", "years") else np.round(raw, 2)
    df = pd.concat([df, pd.DataFrame(cols)], axis=1)
    df.loc[df["Property_type"] == "Plot", [c for c in df.columns if c.startswith("STR:")]] = np.nan       # structural & MEP not applicable to plots
    df.loc[df["Property_type"] == "Plot", "Project_status"] = "Ready"
    tx, infra = synthetic_transactions(), synthetic_infra()
    df = apply_derived(df, tx, infra, overwrite=True)
    if messy:
        for c in [c for c in df.columns if ": " in c]:
            miss = rng.random(n) < 0.015
            df.loc[miss, c] = np.nan
            out = (rng.random(n) < 0.007) & df[c].notna()
            for k in ORDER:
                if c in MODELS[k].ranges:
                    lo, hi = MODELS[k].ranges[c]
                    df.loc[out, c] = hi + 2 * (hi - lo)
    return df


def synthetic_bundle():
    return dict(df=generate_sample_data(), tx=synthetic_transactions(), infra=synthetic_infra())


# ------------------------------------------------------------------------------------------ validation
def read_upload(file) -> pd.DataFrame:
    name = getattr(file, "name", "").lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    return pd.read_csv(file)


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Trim names and accept 'Property ID' / 'property_id' style headers for the identity columns."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    alias = {"property_id": "Property_ID", "property id": "Property_ID", "id": "Property_ID", "zone": "Zone", "locality": "Zone", "property_type": "Property_type",
             "type": "Property_type", "project_status": "Project_status", "lat": "Lat", "latitude": "Lat", "lon": "Lon", "lng": "Lon", "longitude": "Lon", "price_psf": "Price_psf"}
    df = df.rename(columns={c: alias.get(c.lower(), c) for c in df.columns})
    return df


def validate(df: pd.DataFrame) -> dict:
    errors, warnings = [], []
    known = set(ID_COLS) | set(ALL_PARAM_COLS)
    if "Property_ID" not in df.columns:
        df.insert(0, "Property_ID", [f"P{i + 1:03d}" for i in range(len(df))])
        warnings.append("No Property_ID column: ids P001, P002 ... were created.")
    elif df["Property_ID"].duplicated().any():
        errors.append("Duplicate Property_ID values found.")
    if len(df) < 10:
        warnings.append(f"Only {len(df)} properties: data-driven weights need many more (rule of thumb 5-10 per parameter); use Balanced or Custom weights.")
    unknown = [c for c in df.columns if c not in known]
    if unknown:
        warnings.append(f"{len(unknown)} unrecognised column(s) ignored: {', '.join(unknown[:10])}")
    fitted = {}
    for k in ORDER:
        m = MODELS[k]
        fac = {}
        for code in m.hierarchy:
            cols = [c for c in df.columns if c.startswith(f"{code}: ") and c in m.ranges]
            fac[code] = len(cols)
        fitted[k] = fac
        if not any(v >= 3 for v in fac.values()):
            warnings.append(f"{m.title}: no factor has the 3+ parameter columns it needs, so this score will not be computed.")
    for c in df.columns:
        if c in ALL_PARAM_COLS:
            bad = pd.to_numeric(df[c], errors="coerce").isna() & df[c].notna()
            if bad.any():
                warnings.append(f"'{c}': {int(bad.sum())} non-numeric value(s) treated as missing.")
    if "Property_type" in df.columns:
        bad = set(df["Property_type"].dropna().astype(str)) - set(PROPERTY_TYPES)
        if bad:
            warnings.append(f"Property_type values not in {PROPERTY_TYPES}: {sorted(bad)}")
    return dict(errors=errors, warnings=warnings, fitted=fitted)


def data_dictionary() -> pd.DataFrame:
    rows = [("Property_ID", "Identity", "-", "-", "text", "Unique id, e.g. P001"), ("Zone", "Identity", "-", "-", "text", "Zone code, e.g. L01 (joins to the transactions file)"),
            ("Property_type", "Identity", "-", "-", "Apartment | Villa | Plot", "Optional"), ("Project_status", "Identity", "-", "-", "Ready | Under construction", "Optional"),
            ("Lat / Lon", "Identity", "-", "-", "decimal degrees", "Optional; used for the map and infrastructure distances"), ("Price_psf", "Identity", "-", "-", "INR per sq ft", "Optional")]
    for k in ORDER:
        m = MODELS[k]
        for code, f in m.hierarchy.items():
            for sub, labs in f["subs"].items():
                for l in labs:
                    c = f"{code}: {l}"
                    lo, hi = m.ranges[c]
                    rows.append((c, m.title, f["name"], sub, f"{m.units.get(c, '') or 'value'}  (benchmark {lo:g} to {hi:g}; {'lower' if l in m.lower.get(code, set()) else 'higher'} is better)", ""))
    return pd.DataFrame(rows, columns=["Column", "Score", "Factor", "Sub-factor", "Unit / range / direction", "Note"])
