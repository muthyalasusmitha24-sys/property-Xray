# Property X-Ray - Methodology

## 1. What the three scores are

Property X-Ray reports three scores on the same 0-100 scale (100 = best) and with the same method:
**Trust Score** (legal, structural and compliance confidence), **Wellness Score** (wellness and livability, 9 factors) and **Future Readiness Score** (long-term value potential).
Each score is built from a hierarchy **Factor -> Sub-factor -> Parameter**. Score bands: **Excellent** (>= 80), **Good** (>= 65), **Moderate** (>= 50), **Below average** (>= 35), **Poor** (>= 0).

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


# Parameter hierarchies

## Trust Score
Legal, structural and compliance confidence in the property.

**6 factors, 54 parameters.**

### Title & Documentation (TIT)
- **Title Chain:** Verified chain length; Breaks in chain (lower is better); Parent documents available
- **Document Completeness:** Document checklist completeness; Registered sale deed; Revenue records (patta / chitta)
- **Nature of Title:** Freehold / clear title; Succession settled; Power-of-attorney dependence (lower is better)

### Encumbrance & Litigation (ENC)
- **Encumbrance Certificate:** EC coverage; EC entries closed / explained; EC verification
- **Mortgage & Liens:** Active mortgage (share of value) (lower is better); Lender NOC / release available; Charges or liens (lower is better)
- **Litigation:** Pending cases on property (lower is better); Title-related cases (lower is better); Litigation severity (lower is better)

### Statutory Approvals & RERA (APP)
- **RERA Compliance:** RERA registration; RERA complaints on project (lower is better); Delay vs RERA timeline (lower is better)
- **Plan & Layout Approvals:** Building plan approval; Deviation from sanctioned plan (lower is better); Layout approval (CMDA / DTCP)
- **Completion & NOCs:** Occupancy / completion certificate; Fire NOC; Environmental & other NOCs

### Developer Credibility (DEV)
- **Track Record:** Years in business; Projects delivered; On-time delivery rate
- **Customer Record:** Complaints per 100 units (lower is better); Consumer-forum cases (lower is better); Customer satisfaction
- **Financial Standing:** Credit rating; Debt-to-equity ratio (lower is better); Escrow / funding discipline

### Structural & MEP Integrity (STR)
- **Structural Soundness:** Structural audit; Measured / design concrete strength; Seismic code compliance
- **MEP Systems:** Electrical systems condition; Plumbing & drainage condition; Lifts, HVAC & STP condition
- **Safety & Condition:** Fire-safety compliance; Visible defects per 100 sq m (lower is better); Building age (lower is better)

### Plot-Level Risks (PLT)
- **Geotechnical:** Safe bearing capacity; Geotechnical report; Ground-condition suitability
- **Boundary & Encroachment:** Encroachment severity (lower is better); Area variance (record vs measured) (lower is better); Boundary survey match
- **Land Use & Zoning:** Land-use conformity; Water-body / CRZ buffer compliance; Land-conversion status

*Structural & MEP Integrity applies to apartments and villas; for plots leave the STR columns blank and the factor is left out of that property's score.*
*Categorical evidence (approval status, litigation, audits ...) is entered as a 0-100 score; see the data dictionary.*

## Wellness Score
Wellness and livability of the property and its surroundings (9 wellness factors).

**9 factors, 142 parameters.**

### Emotional Wellness (EMO)
- **Stress Reduction Environment:** Green views; Noise levels (lower is better); Natural light
- **Aesthetic Pleasure:** Visual appeal; Architecture quality; Interior design
- **Sense of Safety & Security:** Security features; Safe surroundings; Gated / access control

### Physical Wellness (PHY)
- **Physical Activity Support:** Proximity to parks; Sports facilities; Gyms / fitness centers
- **Walkability:** Walk score; Sidewalk quality; Pedestrian friendliness
- **Safety Features:** Lighting quality; Traffic safety; Crossings & signs
- **Environmental Quality:** Air quality index (lower is better); Water quality; Clean surroundings
- **Accessibility:** Universal design; Ramps & lifts; Senior/disabled access
- **Healthcare Access:** Distance to hospitals (lower is better); Clinics availability; Emergency access
- **Transportation:** Public transport access; Frequency & reliability; Connectivity
- **Ergonomics:** Space planning; Ventilation; Comfort design

### Social Wellness (SOC)
- **Community Engagement:** Social events; Community organizations; Volunteer opportunities
- **Neighbourhood Safety:** Crime rate (lower is better); Perception of safety; Emergency services access
- **Social Connectivity:** Public spaces; Transportation links; Digital connectivity
- **Inclusivity & Diversity:** Demographic diversity; Cultural activities
- **Community Support Networks:** Support groups; Local resources; Mutual help
- **Work-Life Balance:** Proximity to workplaces; Leisure facilities

### Occupational Wellness (OCC)
- **Work-Life Balance:** Flexible workspace; Work hours balance; Personal time
- **Commute Efficiency:** Commute time (lower is better); Traffic conditions (lower is better); Transport options
- **Coworking Availability:** Coworking spaces; Shared offices; Business centers
- **Employment Density:** Job opportunities; Employment rate; Business ecosystem
- **Job Opportunities:** Career growth; Industry presence; Skill demand

### Environmental Wellness (ENV)
- **Air Quality:** AQI value (lower is better); Pollutant levels (lower is better); Ventilation quality
- **Water Quality:** Drinking water quality; Water source; Contamination levels (lower is better)
- **Waste Management:** Waste segregation; Collection systems; Recycling facilities
- **Noise Pollution:** Noise levels (dB) (lower is better); Traffic noise (lower is better); Industrial noise (lower is better)
- **Green Cover:** % Green cover; Trees / vegetation; Open spaces
- **Energy Efficiency:** Energy star rating; Renewable energy; Efficiency systems

### Intellectual Wellness (INT)
- **Educational Resources:** Schools proximity; Colleges proximity; Quality of education
- **Library Access:** Public libraries; Digital resources; Reading spaces
- **Skill Development:** Training centers; Workshops; Online learning access
- **Cultural & Creative Engagement:** Cultural events; Museums / galleries; Creative spaces
- **Innovation & Learning Ecosystem:** Hackathons / forums; Community learning; Knowledge networks

### Spiritual Wellness (SPI)
- **Places of Worship:** Temples / Churches; Mosques / Gurudwaras; Distance & access
- **Meditation Spaces:** Quiet zones; Meditation centers; Yoga facilities
- **Tranquility & Peace:** Calm environment; Low noise; Stress-free zones
- **Cultural Heritage:** Heritage sites; Historical places; Traditions & art
- **Mind-Body Balance:** Wellness centers; Yoga / fitness; Holistic activities

### Financial Wellness (FIN)
- **Financial Performance Metrics:** Cap Rate; Rent to Cost Ratio; ROI
- **Investment Viability:** NPV; IRR; Break-even (lower is better)
- **Cost & Affordability:** Property price (lower is better); Maintenance cost (lower is better); Utility cost (lower is better)
- **Cash Flow Stability:** Rental income; Occupancy rate; Debt coverage
- **Market & Growth Potential:** Market trend; Appreciation; Future demand

### Statutory Wellness (STA)
- **Legal Compliance:** RERA registration; Building approvals; Land use compliance
- **Title & Ownership Documents:** Title deed; Encumbrance certificate; Sale agreement
- **Building & Safety Certifications:** Occupancy certificate; Fire safety NOC; Structural safety
- **Tax & Financial Documents:** Property tax receipt; Utility bills; Financial statements
- **Government Verifications:** Aadhaar / PAN; KYC documents; Other clearances


## Future Readiness Score
Long-term value potential from transaction trends, infrastructure, environmental risk and market growth.

**4 factors, 39 parameters.**

### Historical Transaction Trends (HST)
- **Price Growth:** 5-year price CAGR; 3-year price CAGR; Price vs micro-market average (lower is better)
- **Price Stability:** Price volatility (lower is better); Worst-year price fall (lower is better); Price-growth consistency
- **Market Liquidity:** Transactions per year; Transaction volume trend; Days on market (lower is better)

### Planned Infrastructure (INF)
- **Transit & Rail:** Metro / rail influence; Distance to nearest planned transit (lower is better); Delivery confidence of transit projects
- **Roads & Airport:** Road / expressway influence; Distance to nearest road project (lower is better); Airport / bus-terminus influence
- **Business & Civic Projects:** Business-park / SEZ influence; Healthcare & education influence; Water, drainage & public-realm influence
- **Execution Risk:** Stalled projects within 3 km (lower is better); Nuisance projects within 3 km (lower is better); Average delay of nearby projects (lower is better)

### Environmental Risk Resilience (ENR)
- **Flood & Water:** Flood hazard (lower is better); Waterlogging events (10 yrs) (lower is better); Water-stress index (lower is better)
- **Coastal & Terrain:** Elevation above sea level; Distance to coast; Storm-surge exposure (lower is better)
- **Seismic & Climate:** Seismic zone (lower is better); Heat-stress days (above 38 C) (lower is better); PM2.5 trend (lower is better)

### Market Growth Patterns (MKT)
- **Demand Drivers:** Employment growth; Population growth; Rental demand
- **Supply Balance:** Unsold inventory (lower is better); Supply pipeline (share of stock) (lower is better); Absorption rate
- **Returns & Affordability:** Gross rental yield; Price-to-income ratio (lower is better); Rental growth

*Historical Transaction Trends and Planned Infrastructure parameters can be computed from an optional transactions file and an infrastructure-projects file (influence = impact x delivery probability x distance decay x time discount) in Data & Upload.*