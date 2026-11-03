"""Parameter hierarchy for the three scores, all in the same format:
   Factor -> Sub-factor -> Parameter   (column name = "<factor code>: <parameter>").
Wellness is taken unchanged from the original Wellness Score project (9 factors, 142 parameters)."""
from __future__ import annotations

from dataclasses import dataclass, field

WELLNESS_HIERARCHY = {'EMO': {'name': 'Emotional Wellness',
         'subs': {'Stress Reduction Environment': ['Green views', 'Noise levels', 'Natural light'],
                  'Aesthetic Pleasure': ['Visual appeal', 'Architecture quality', 'Interior design'],
                  'Sense of Safety & Security': ['Security features', 'Safe surroundings', 'Gated / access control']}},
 'PHY': {'name': 'Physical Wellness',
         'subs': {'Physical Activity Support': ['Proximity to parks', 'Sports facilities', 'Gyms / fitness centers'],
                  'Walkability': ['Walk score', 'Sidewalk quality', 'Pedestrian friendliness'],
                  'Safety Features': ['Lighting quality', 'Traffic safety', 'Crossings & signs'],
                  'Environmental Quality': ['Air quality index', 'Water quality', 'Clean surroundings'],
                  'Accessibility': ['Universal design', 'Ramps & lifts', 'Senior/disabled access'],
                  'Healthcare Access': ['Distance to hospitals', 'Clinics availability', 'Emergency access'],
                  'Transportation': ['Public transport access', 'Frequency & reliability', 'Connectivity'],
                  'Ergonomics': ['Space planning', 'Ventilation', 'Comfort design']}},
 'SOC': {'name': 'Social Wellness',
         'subs': {'Community Engagement': ['Social events', 'Community organizations', 'Volunteer opportunities'],
                  'Neighbourhood Safety': ['Crime rate', 'Perception of safety', 'Emergency services access'],
                  'Social Connectivity': ['Public spaces', 'Transportation links', 'Digital connectivity'],
                  'Inclusivity & Diversity': ['Demographic diversity', 'Cultural activities'],
                  'Community Support Networks': ['Support groups', 'Local resources', 'Mutual help'],
                  'Work-Life Balance': ['Proximity to workplaces', 'Leisure facilities']}},
 'OCC': {'name': 'Occupational Wellness',
         'subs': {'Work-Life Balance': ['Flexible workspace', 'Work hours balance', 'Personal time'],
                  'Commute Efficiency': ['Commute time', 'Traffic conditions', 'Transport options'],
                  'Coworking Availability': ['Coworking spaces', 'Shared offices', 'Business centers'],
                  'Employment Density': ['Job opportunities', 'Employment rate', 'Business ecosystem'],
                  'Job Opportunities': ['Career growth', 'Industry presence', 'Skill demand']}},
 'ENV': {'name': 'Environmental Wellness',
         'subs': {'Air Quality': ['AQI value', 'Pollutant levels', 'Ventilation quality'],
                  'Water Quality': ['Drinking water quality', 'Water source', 'Contamination levels'],
                  'Waste Management': ['Waste segregation', 'Collection systems', 'Recycling facilities'],
                  'Noise Pollution': ['Noise levels (dB)', 'Traffic noise', 'Industrial noise'],
                  'Green Cover': ['% Green cover', 'Trees / vegetation', 'Open spaces'],
                  'Energy Efficiency': ['Energy star rating', 'Renewable energy', 'Efficiency systems']}},
 'INT': {'name': 'Intellectual Wellness',
         'subs': {'Educational Resources': ['Schools proximity', 'Colleges proximity', 'Quality of education'],
                  'Library Access': ['Public libraries', 'Digital resources', 'Reading spaces'],
                  'Skill Development': ['Training centers', 'Workshops', 'Online learning access'],
                  'Cultural & Creative Engagement': ['Cultural events', 'Museums / galleries', 'Creative spaces'],
                  'Innovation & Learning Ecosystem': ['Hackathons / forums', 'Community learning', 'Knowledge networks']}},
 'SPI': {'name': 'Spiritual Wellness',
         'subs': {'Places of Worship': ['Temples / Churches', 'Mosques / Gurudwaras', 'Distance & access'],
                  'Meditation Spaces': ['Quiet zones', 'Meditation centers', 'Yoga facilities'],
                  'Tranquility & Peace': ['Calm environment', 'Low noise', 'Stress-free zones'],
                  'Cultural Heritage': ['Heritage sites', 'Historical places', 'Traditions & art'],
                  'Mind-Body Balance': ['Wellness centers', 'Yoga / fitness', 'Holistic activities']}},
 'FIN': {'name': 'Financial Wellness',
         'subs': {'Financial Performance Metrics': ['Cap Rate', 'Rent to Cost Ratio', 'ROI'],
                  'Investment Viability': ['NPV', 'IRR', 'Break-even'],
                  'Cost & Affordability': ['Property price', 'Maintenance cost', 'Utility cost'],
                  'Cash Flow Stability': ['Rental income', 'Occupancy rate', 'Debt coverage'],
                  'Market & Growth Potential': ['Market trend', 'Appreciation', 'Future demand']}},
 'STA': {'name': 'Statutory Wellness',
         'subs': {'Legal Compliance': ['RERA registration', 'Building approvals', 'Land use compliance'],
                  'Title & Ownership Documents': ['Title deed', 'Encumbrance certificate', 'Sale agreement'],
                  'Building & Safety Certifications': ['Occupancy certificate', 'Fire safety NOC', 'Structural safety'],
                  'Tax & Financial Documents': ['Property tax receipt', 'Utility bills', 'Financial statements'],
                  'Government Verifications': ['Aadhaar / PAN', 'KYC documents', 'Other clearances']}}}
WELLNESS_LOWER = {'EMO': {'Noise levels'},
 'ENV': {'Noise levels (dB)', 'Contamination levels', 'Traffic noise', 'Industrial noise', 'Pollutant levels', 'AQI value'},
 'FIN': {'Maintenance cost', 'Utility cost', 'Break-even', 'Property price'},
 'OCC': {'Traffic conditions', 'Commute time'},
 'PHY': {'Distance to hospitals', 'Air quality index'},
 'SOC': {'Crime rate'}}
WELLNESS_RANGES = {'EMO: Noise levels': (35, 90),
 'ENV: % Green cover': (2, 60),
 'ENV: AQI value': (15, 300),
 'ENV: Contamination levels': (0, 10),
 'ENV: Energy star rating': (1, 5),
 'ENV: Industrial noise': (30, 85),
 'ENV: Noise levels (dB)': (35, 90),
 'ENV: Pollutant levels': (5, 150),
 'ENV: Traffic noise': (30, 85),
 'FIN: Appreciation': (1, 15),
 'FIN: Break-even': (3, 25),
 'FIN: Cap Rate': (1, 8),
 'FIN: Debt coverage': (0.8, 3),
 'FIN: IRR': (3, 20),
 'FIN: Maintenance cost': (1, 12),
 'FIN: NPV': (-5, 40),
 'FIN: Occupancy rate': (50, 100),
 'FIN: Property price': (4000, 25000),
 'FIN: ROI': (2, 18),
 'FIN: Rent to Cost Ratio': (0.2, 1.2),
 'FIN: Rental income': (10, 120),
 'FIN: Utility cost': (1, 8),
 'OCC: Commute time': (5, 90),
 'OCC: Traffic conditions': (10, 100),
 'PHY: Air quality index': (15, 300),
 'PHY: Distance to hospitals': (0.3, 15),
 'SOC: Crime rate': (0.5, 40)}


def P(label, unit, lo, hi, lower=False):
    return dict(label=label, unit=unit, lo=lo, hi=hi, lower=lower)


# ----------------------------------------------------------------------------------------------- TRUST
TRUST_SPEC = {
    "TIT": ("Title & Documentation", {
        "Title Chain": [P("Verified chain length", "years", 0, 30), P("Breaks in chain", "count", 0, 3, True), P("Parent documents available", "score", 0, 100)],
        "Document Completeness": [P("Document checklist completeness", "%", 40, 100), P("Registered sale deed", "score", 0, 100), P("Revenue records (patta / chitta)", "score", 0, 100)],
        "Nature of Title": [P("Freehold / clear title", "score", 0, 100), P("Succession settled", "score", 0, 100), P("Power-of-attorney dependence", "score", 0, 100, True)]}),
    "ENC": ("Encumbrance & Litigation", {
        "Encumbrance Certificate": [P("EC coverage", "years", 0, 30), P("EC entries closed / explained", "%", 0, 100), P("EC verification", "score", 0, 100)],
        "Mortgage & Liens": [P("Active mortgage (share of value)", "%", 0, 100, True), P("Lender NOC / release available", "score", 0, 100), P("Charges or liens", "count", 0, 5, True)],
        "Litigation": [P("Pending cases on property", "count", 0, 5, True), P("Title-related cases", "count", 0, 3, True), P("Litigation severity", "score", 0, 100, True)]}),
    "APP": ("Statutory Approvals & RERA", {
        "RERA Compliance": [P("RERA registration", "score", 0, 100), P("RERA complaints on project", "count", 0, 10, True), P("Delay vs RERA timeline", "%", 0, 50, True)],
        "Plan & Layout Approvals": [P("Building plan approval", "score", 0, 100), P("Deviation from sanctioned plan", "%", 0, 20, True), P("Layout approval (CMDA / DTCP)", "score", 0, 100)],
        "Completion & NOCs": [P("Occupancy / completion certificate", "score", 0, 100), P("Fire NOC", "score", 0, 100), P("Environmental & other NOCs", "score", 0, 100)]}),
    "DEV": ("Developer Credibility", {
        "Track Record": [P("Years in business", "years", 0, 30), P("Projects delivered", "count", 0, 25), P("On-time delivery rate", "%", 30, 100)],
        "Customer Record": [P("Complaints per 100 units", "count", 0, 10, True), P("Consumer-forum cases", "count", 0, 10, True), P("Customer satisfaction", "score", 0, 100)],
        "Financial Standing": [P("Credit rating", "score", 0, 100), P("Debt-to-equity ratio", "ratio", 0, 4, True), P("Escrow / funding discipline", "score", 0, 100)]}),
    "STR": ("Structural & MEP Integrity", {
        "Structural Soundness": [P("Structural audit", "score", 0, 100), P("Measured / design concrete strength", "ratio", 0.6, 1.2), P("Seismic code compliance", "score", 0, 100)],
        "MEP Systems": [P("Electrical systems condition", "score", 0, 100), P("Plumbing & drainage condition", "score", 0, 100), P("Lifts, HVAC & STP condition", "score", 0, 100)],
        "Safety & Condition": [P("Fire-safety compliance", "score", 0, 100), P("Visible defects per 100 sq m", "count", 0, 10, True), P("Building age", "years", 0, 60, True)]}),
    "PLT": ("Plot-Level Risks", {
        "Geotechnical": [P("Safe bearing capacity", "kN/m2", 50, 250), P("Geotechnical report", "score", 0, 100), P("Ground-condition suitability", "score", 0, 100)],
        "Boundary & Encroachment": [P("Encroachment severity", "score", 0, 100, True), P("Area variance (record vs measured)", "%", 0, 20, True), P("Boundary survey match", "score", 0, 100)],
        "Land Use & Zoning": [P("Land-use conformity", "score", 0, 100), P("Water-body / CRZ buffer compliance", "score", 0, 100), P("Land-conversion status", "score", 0, 100)]}),
}

# ----------------------------------------------------------------------------------------------- FUTURE READINESS
FUTURE_SPEC = {
    "HST": ("Historical Transaction Trends", {
        "Price Growth": [P("5-year price CAGR", "%/yr", 0, 15), P("3-year price CAGR", "%/yr", 0, 15), P("Price vs micro-market average", "ratio", 0.7, 1.4, True)],
        "Price Stability": [P("Price volatility", "%", 0, 18, True), P("Worst-year price fall", "%", 0, 20, True), P("Price-growth consistency", "score", 0, 100)],
        "Market Liquidity": [P("Transactions per year", "count", 50, 1500), P("Transaction volume trend", "%/yr", -20, 20), P("Days on market", "days", 20, 240, True)]}),
    "INF": ("Planned Infrastructure", {
        "Transit & Rail": [P("Metro / rail influence", "index", 0, 1.5), P("Distance to nearest planned transit", "km", 0, 15, True), P("Delivery confidence of transit projects", "%", 0, 100)],
        "Roads & Airport": [P("Road / expressway influence", "index", 0, 1.5), P("Distance to nearest road project", "km", 0, 15, True), P("Airport / bus-terminus influence", "index", 0, 1.5)],
        "Business & Civic Projects": [P("Business-park / SEZ influence", "index", 0, 1.5), P("Healthcare & education influence", "index", 0, 1.5), P("Water, drainage & public-realm influence", "index", 0, 1.5)],
        "Execution Risk": [P("Stalled projects within 3 km", "count", 0, 3, True), P("Nuisance projects within 3 km", "count", 0, 3, True), P("Average delay of nearby projects", "years", 0, 5, True)]}),
    "ENR": ("Environmental Risk Resilience", {
        "Flood & Water": [P("Flood hazard", "score", 0, 100, True), P("Waterlogging events (10 yrs)", "count", 0, 8, True), P("Water-stress index", "score", 0, 100, True)],
        "Coastal & Terrain": [P("Elevation above sea level", "m", 0, 40), P("Distance to coast", "km", 0, 15), P("Storm-surge exposure", "score", 0, 100, True)],
        "Seismic & Climate": [P("Seismic zone", "zone", 2, 5, True), P("Heat-stress days (above 38 C)", "days/yr", 0, 150, True), P("PM2.5 trend", "ug/m3 per yr", -3, 3, True)]}),
    "MKT": ("Market Growth Patterns", {
        "Demand Drivers": [P("Employment growth", "%/yr", -2, 9), P("Population growth", "%/yr", -1, 5), P("Rental demand", "score", 0, 100)],
        "Supply Balance": [P("Unsold inventory", "months", 6, 48, True), P("Supply pipeline (share of stock)", "%", 0, 40, True), P("Absorption rate", "%/qtr", 0, 15)],
        "Returns & Affordability": [P("Gross rental yield", "%", 1, 6), P("Price-to-income ratio", "x", 3, 18, True), P("Rental growth", "%/yr", -2, 10)]}),
}


@dataclass
class Model:
    key: str
    title: str
    short: str
    hierarchy: dict            # code -> {"name":..., "subs": {sub: [labels]}}
    lower: dict                # code -> set(labels where lower is better)
    ranges: dict               # column -> (lo, hi)
    units: dict                # column -> unit string
    describes: str = ""
    optional: set = field(default_factory=set)   # factor codes that may be entirely blank for a property (e.g. structural for plots)

    def columns(self):
        return [f"{c}: {l}" for c, f in self.hierarchy.items() for labs in f["subs"].values() for l in labs]


def _from_spec(spec):
    H, lower, rng, units = {}, {}, {}, {}
    for code, (name, subs) in spec.items():
        H[code] = {"name": name, "subs": {s: [p["label"] for p in ps] for s, ps in subs.items()}}
        lower[code] = {p["label"] for ps in subs.values() for p in ps if p["lower"]}
        for ps in subs.values():
            for p in ps:
                rng[f"{code}: {p['label']}"] = (p["lo"], p["hi"])
                units[f"{code}: {p['label']}"] = p["unit"]
    return H, lower, rng, units


def _wellness():
    rng = {}
    for code, f in WELLNESS_HIERARCHY.items():
        for labs in f["subs"].values():
            for l in labs:
                rng[f"{code}: {l}"] = WELLNESS_RANGES.get(f"{code}: {l}", (0, 100))
    units = {c: ("score" if r == (0, 100) else "") for c, r in rng.items()}
    unit_map = {"Noise levels": "dB", "Noise levels (dB)": "dB", "Air quality index": "AQI", "AQI value": "AQI", "Distance to hospitals": "km", "Crime rate": "per 1000",
                "Commute time": "min", "Pollutant levels": "ug/m3", "% Green cover": "%", "Energy star rating": "stars", "Cap Rate": "%", "ROI": "%", "IRR": "%",
                "Property price": "INR 000/sq ft", "Appreciation": "%/yr", "Occupancy rate": "%", "Break-even": "years"}
    for c in units:
        lab = c.split(": ", 1)[1]
        if lab in unit_map and units[c] != "score":
            units[c] = unit_map[lab]
    return rng, units


_wr, _wu = _wellness()
MODELS = {
    "trust": Model("trust", "Trust Score", "Trust", *_from_spec(TRUST_SPEC)[0:1], _from_spec(TRUST_SPEC)[1], _from_spec(TRUST_SPEC)[2], _from_spec(TRUST_SPEC)[3],
                   describes="Legal, structural and compliance confidence in the property.", optional={"STR"}),
    "wellness": Model("wellness", "Wellness Score", "Wellness", WELLNESS_HIERARCHY, WELLNESS_LOWER, _wr, _wu,
                      describes="Wellness and livability of the property and its surroundings (9 wellness factors)."),
    "future": Model("future", "Future Readiness Score", "Future Readiness", *_from_spec(FUTURE_SPEC)[0:1], _from_spec(FUTURE_SPEC)[1], _from_spec(FUTURE_SPEC)[2], _from_spec(FUTURE_SPEC)[3],
                    describes="Long-term value potential from transaction trends, infrastructure, environmental risk and market growth."),
}
ORDER = ["trust", "wellness", "future"]
ID_COLS = ["Property_ID", "Zone", "Property_type", "Project_status", "Lat", "Lon", "Price_psf"]
PROPERTY_TYPES = ["Apartment", "Villa", "Plot"]
BANDS = [(80, "Excellent"), (65, "Good"), (50, "Moderate"), (35, "Below average"), (0, "Poor")]
