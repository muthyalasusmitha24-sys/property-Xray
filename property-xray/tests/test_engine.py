import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np, pandas as pd
from xray import data as D, engine as E, schema as S


def _df():
    return D.generate_sample_data(80, 1).set_index("Property_ID", drop=False)


def test_wellness_hierarchy_unchanged():
    m = S.MODELS["wellness"]
    assert len(m.hierarchy) == 9 and len(m.columns()) == 142


def test_all_scores_in_range_every_mode():
    df = _df()
    for k in S.ORDER:
        m = S.MODELS[k]
        for mode in E.MODES:
            r = E.run_model(df, m, E.default_config(m), mode, {c: 1 for c in m.hierarchy}, 30)
            assert r.overall.between(0, 100).all()
            assert abs(r.fw.sum() - 1) < 1e-9


def test_pca_weights_sum_to_one_and_eigenvalues():
    X = np.random.default_rng(0).normal(size=(60, 8))
    out = E.pca_weights(X)
    assert abs(out["w"].sum() - 1) < 1e-9 and abs(out["eig"].sum() - 8) < 1e-6


def test_drags_add_up_exactly():
    df = _df(); m = S.MODELS["wellness"]
    r = E.run_model(df, m, E.default_config(m), "Data-driven", None, 30)
    top, tot = E.drags(r, df.index[3], 3)
    assert abs(tot - (100 - r.overall[df.index[3]])) < 1e-6


def test_plot_leaves_structural_out():
    df = _df(); m = S.MODELS["trust"]
    r = E.run_model(df, m, E.default_config(m), "Balanced", None, 20)
    plot = df.index[df["Property_type"] == "Plot"][0]
    assert np.isnan(r.F.loc[plot, "STR"]) and r.W.loc[plot].sum() > 0.999 and r.W.loc[plot, "STR"] == 0


def test_direction_flip():
    df = _df(); m = S.MODELS["wellness"]
    r = E.run_model(df, m, E.default_config(m), "Balanced", None, 20)
    f = r.results["ENV"]
    assert f.norm_stats.loc["ENV: Noise levels (dB)", "direction"] == "lower"


def test_new_property_matches_reference_row():
    df = _df(); m = S.MODELS["trust"]
    r = E.run_model(df, m, E.default_config(m), "Data-driven", None, 20)
    F, ov, lo, hi, subs = E.score_new(r, df.iloc[[5]])
    assert abs(ov.iloc[0] - r.overall.iloc[5]) < 1e-6
