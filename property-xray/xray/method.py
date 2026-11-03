"""Methodology text. Terminology follows the original Wellness Score project:
Factor, Sub-factor, Parameter, preprocessing, scaling, correlation matrix, PCA, eigenvalue, explained variance, bootstrap, confidence interval."""
from __future__ import annotations

from .schema import BANDS, MODELS, ORDER

FLOW = """digraph G { rankdir=LR; bgcolor="transparent"; node [shape=box style="rounded,filled" fillcolor="#ECFDF5" color="#0F766E" fontname="Helvetica" fontsize=11 margin="0.14,0.09"]; edge [color="#6B7780"];
 a [label="1  Raw parameters\\n(one row per property)" fillcolor="#F7F5F0"]; b [label="2  Data preprocessing\\nfill blanks · cap outliers\\nscale 0-100 · flip direction"]; c [label="3  Correlation matrix\\n+ KMO / Bartlett"];
 d [label="4  PCA\\neigenvalue > 1"]; e [label="5  Parameter weights\\n(explained variance)"]; f [label="6  Bootstrap\\nstability + interval"]; g [label="7  Sub-factor scores"]; h [label="8  Factor scores"];
 i [label="9  Overall score\\n+ confidence interval" fillcolor="#134E4A" fontcolor="white"]; a -> b -> c -> d -> e -> f -> g -> h -> i; }"""


def common() -> str:
    return """## 1. What the three scores are

Property X-Ray reports three scores on the same 0-100 scale (100 = best) and with the same method:
**Trust Score** (legal, structural and compliance confidence), **Wellness Score** (wellness and livability, 9 factors) and **Future Readiness Score** (long-term value potential).
Each score is built from a hierarchy **Factor -> Sub-factor -> Parameter**. Score bands: """ + ", ".join(f"**{n}** (>= {t})" for t, n in BANDS) + r""".

## 2. The pipeline (identical for every score)

**Step 1 - Data preprocessing, per parameter**
1. *Fill blanks:* a missing value is replaced by the median of the parameter over all properties.
2. *Cap outliers:* values outside the IQR limits, lower = Q1 - 1.5 x IQR and upper = Q3 + 1.5 x IQR, are pulled back to the nearest limit.
3. *Scale to 0-100:* $x = \dfrac{v - \min}{\max - \min} \times 100$. *min* and *max* are benchmark values (editable in each score's Data & settings tab); if left blank the smallest and largest cleaned values in the data are used.
4. *Flip direction:* where a lower value is better (noise, flood hazard, price ratio, litigation ...) the score becomes $100 - x$, so 100 is always best.

**Step 2 - Correlation matrix and suitability.** For each factor the correlation matrix of its parameter scores is computed. KMO (sampling adequacy; 0.6 or higher is acceptable) and Bartlett's test of sphericity tell whether PCA can find a pattern.

**Step 3 - PCA weights (the single data-driven method).** Eigen-decomposition of the correlation matrix $R = V\Lambda V^T$. Components with eigenvalue above 1 are kept (Kaiser criterion).
With explained-variance ratio $\mathrm{EVR}_k = \lambda_k / \sum\lambda$, the weight of parameter *j* is
$$w_j \propto \sum_{k \le K} \mathrm{EVR}_k \, v_{jk}^2 \qquad (\textstyle\sum_j w_j = 1)$$
This is the standard PCA / explained-variance weighting used for composite indicators. The same rule is applied again to the sub-factor scores (to weight sub-factors inside a factor) and to the factor scores (to weight factors in the overall score).

**Step 4 - Bootstrap.** The whole weighting is repeated on random resamples of the properties. The final parameter weight is the bootstrap average; its spread shows how stable it is, and the resampled scores give the **confidence interval** of every score.

**Step 5 - Scores.**
- Sub-factor score = weighted average of its parameter scores (weights re-scaled to 100% inside the sub-factor).
- Factor score = $\sum$ sub-factor weight x sub-factor score.
- Overall score = $\sum$ factor weight x factor score. If a factor does not apply to a property (for example Structural & MEP for a plot, left blank) it is left out for that property and the remaining weights are re-scaled to 100%.

## 3. Weighting options

| Option | Parameters in a sub-factor | Sub-factors in a factor | Factors in the overall score |
|---|---|---|---|
| **Balanced** | equal | equal | equal |
| **Data-driven** | PCA explained variance (bootstrap average) | PCA explained variance | PCA explained variance |
| **Custom** | equal | equal | your weights (0-3 per factor, re-scaled to 100%) |

The confidence interval is shown for Data-driven weights, where it measures the uncertainty of the estimated weights.

## 4. Reading the results
- *Biggest drags* = effective weight of a parameter x (100 - its score). The drags of all parameters add up to exactly 100 - overall score.
- Data-quality flags (small sample, low KMO, near-duplicate parameters, negative correlation with peers, unstable weights ...) are reported automatically in each factor's pipeline.

## 5. Limitations
- Scores are indices that depend on the reference set of properties and on the benchmark min / max; they are not certified ratings or guarantees.
- Data-driven weights describe statistical variation in the data, not universal buyer priorities. Use Balanced or Custom weights for small samples.
- Bootstrap intervals reflect weight-estimation uncertainty only, not measurement error.
- The bundled sample data is **synthetic** and for software testing only.
"""


def model_text(key: str) -> str:
    m = MODELS[key]
    L = [f"## {m.title}", m.describes, "", f"**{len(m.hierarchy)} factors, {sum(len(s) for f in m.hierarchy.values() for s in f['subs'].values())} parameters.**", ""]
    for code, f in m.hierarchy.items():
        L.append(f"### {f['name']} ({code})")
        for sub, labs in f["subs"].items():
            L.append(f"- **{sub}:** " + "; ".join(l + (" (lower is better)" if l in m.lower.get(code, set()) else "") for l in labs))
        L.append("")
    if key == "trust":
        L += ["*Structural & MEP Integrity applies to apartments and villas; for plots leave the STR columns blank and the factor is left out of that property's score.*",
              "*Categorical evidence (approval status, litigation, audits ...) is entered as a 0-100 score; see the data dictionary.*"]
    if key == "future":
        L += ["*Historical Transaction Trends and Planned Infrastructure parameters can be computed from an optional transactions file and an infrastructure-projects file "
              "(influence = impact x delivery probability x distance decay x time discount) in Data & Upload.*"]
    return "\n".join(L)


def build() -> str:
    return "# Property X-Ray - Methodology\n\n" + common() + "\n\n# Parameter hierarchies\n\n" + "\n\n".join(model_text(k) for k in ORDER)
