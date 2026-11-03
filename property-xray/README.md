# Property X-Ray – Trust · Wellness · Future Readiness

Three scores on one 0–100 scale, all built with the **same method and the same layout** as the original Wellness Score project:
**Factor → Sub-factor → Parameter**, preprocessing → correlation → PCA → bootstrap → sub-factor, factor and overall score with a confidence interval.

| Score | Factors | Parameters |
|---|---|---|
| Trust Score | 6 (Title & Documentation, Encumbrance & Litigation, Statutory Approvals & RERA, Developer Credibility, Structural & MEP Integrity, Plot-Level Risks) | 54 |
| Wellness Score | 9 (Emotional, Physical, Social, Occupational, Environmental, Intellectual, Spiritual, Financial, Statutory) – unchanged | 142 |
| Future Readiness Score | 4 (Historical Transaction Trends, Planned Infrastructure, Environmental Risk Resilience, Market Growth Patterns) | 39 |

Every score page has the same six tabs: **Data & settings · Factor pipeline · Overall score · Score a new property · Explanation · Method**.

## Weighting (sidebar)
* **Balanced** – equal weights at every level.
* **Data-driven** – a single method: PCA explained-variance weights (Kaiser eigenvalue > 1), bootstrap-averaged, applied to parameters, sub-factors and factors.
* **Custom** – your own factor weights (0–3).

## Data
Sample data is synthetic and uses codes only (P001, zone L01). Upload CSV / Excel with one row per property and columns named like `TIT: Verified chain length`
(see *Data & Upload → Templates*). Optional transactions and infrastructure files fill the Historical Transaction and Planned Infrastructure parameters.
Leave `STR:` columns blank for plots.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
## Deploy
Push this folder to GitHub (keep `app.py` at the root) → share.streamlit.io → New app → `app.py`.

## Files
`app.py` UI · `xray/schema.py` factor / sub-factor / parameter hierarchies · `xray/engine.py` scoring engine · `xray/data.py` sample data, derived features, validation ·
`xray/theme.py` styling and charts · `xray/method.py` methodology text · `docs/METHODOLOGY.md` · `templates/` example files · `tests/` pytest.

> Scores are data-dependent indices, not certified ratings or guarantees. Sample data is synthetic and for software testing only.
