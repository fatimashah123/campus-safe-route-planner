import numpy as np
import pandas as pd

np.random.seed(42)  # so results are reproducible

# same coordinates as your campus nodes
nodes = {
    "sino_pak_centre_ai": (33.91032862256931, 72.9213952435269),
    "stc_cafe": (33.909442045505806, 72.92258221365968),
    "open_gym": (33.90894128957056, 72.9228690647751),
    "school_of_computing": (33.90888382558654, 72.91939717713674),
    "suites_foreign_faculty": (33.91025830249714, 72.92413406738025),
    "academic_block_a": (33.90898470336545, 72.91905375044657),
    "dept_electrical_mechanical": (33.90915345511278, 72.9190619937154),
    "nanogen": (33.90965058669684, 72.92040015102229),
    "main_executive_block": (33.90875940438815, 72.91798354194209),
    "football_ground": (33.90814287890393, 72.91978369427744),
    "academic_block_c1": (33.91018100577292, 72.92113360939288),
    "vizta_labs": (33.91069283901439, 72.92313036644451),
    "sus_spot": (33.908686582587315, 72.92302709907285),
}

INCIDENT_TYPES = ["theft", "harassment", "poor_lighting_report", "suspicious_activity", "eve_teasing"]
SEVERITY_MAP = {"theft": 2, "harassment": 3, "poor_lighting_report": 1, "suspicious_activity": 2, "eve_teasing": 3}

# assign a relative "risk multiplier" per location — EDIT these based on real judgment
# e.g. isolated/less-lit spots get higher risk, busy central areas get lower risk
location_risk_weight = {
    "sino_pak_centre_ai": 1.0,
    "stc_cafe": 0.6,             # busy, well-lit
    "open_gym": 1.2,             # often isolated in evening
    "school_of_computing": 0.8,
    "suites_foreign_faculty": 0.7,
    "academic_block_a": 0.8,
    "dept_electrical_mechanical": 0.9,
    "nanogen": 0.9,
    "main_executive_block": 0.5,  # high security presence
    "football_ground": 1.3,      # open, isolated at night
    "academic_block_c1": 0.8,
    "vizta_labs": 0.9,
    "sus_spot": 1.4,             # remote-sounding spot, higher weight
}

def generate_incidents(n=300):
    rows = []
    names = list(nodes.keys())
    weights = np.array([location_risk_weight[n_] for n_ in names])
    probs = weights / weights.sum()

    for _ in range(n):
        loc_name = np.random.choice(names, p=probs)
        lat, lon = nodes[loc_name]

        # jitter the point slightly so incidents aren't exactly on the node
        lat_jitter = lat + np.random.normal(0, 0.0003)
        lon_jitter = lon + np.random.normal(0, 0.0003)

        incident_type = np.random.choice(INCIDENT_TYPES)
        severity = SEVERITY_MAP[incident_type]
        hour = int(np.random.choice(
            range(24),
            p=_hourly_distribution()
        ))

        rows.append({
            "latitude": lat_jitter,
            "longitude": lon_jitter,
            "nearest_location": loc_name,
            "incident_type": incident_type,
            "severity": severity,
            "hour": hour
        })

    return pd.DataFrame(rows)

def _hourly_distribution():
    # higher probability of incidents at night (7pm-11pm) and early morning (5am-7am)
    hours = np.arange(24)
    weights = np.ones(24)
    weights[19:24] = 3.0   # 7pm - 11:59pm
    weights[0:6] = 2.0     # midnight - 6am
    weights[6:17] = 0.5    # daytime, safer
    return weights / weights.sum()

if __name__ == "__main__":
    df = generate_incidents(n=300)
    df.to_csv("data/raw/incidents.csv", index=False)
    print(f"Generated {len(df)} synthetic incidents")
    print(df.head(10))
    print("\nIncident counts by location:")
    print(df["nearest_location"].value_counts())