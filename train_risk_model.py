import pandas as pd
import numpy as np
import networkx as nx
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, LeaveOneOut
from risk_score import load_graph

def build_edge_features(G, incidents_df):
    rows = []
    for u, v, data in G.edges(data=True):
        length = float(data["length"])
        incident_count = int(data.get("incident_count", 0))
        risk_raw = float(data.get("risk_raw", 0))
        avg_severity = risk_raw / incident_count if incident_count > 0 else 0

        deg_u = G.degree(u)
        deg_v = G.degree(v)
        avg_degree = (deg_u + deg_v) / 2

        rows.append({
            "u": u, "v": v,
            "length": length,
            "incident_count": incident_count,
            "avg_severity": avg_severity,
            "avg_degree": avg_degree,
            "risk_score": float(data.get("risk_score", 0))  # target
        })
    return pd.DataFrame(rows)

def train_model(df):
    feature_cols = ["length", "incident_count", "avg_severity", "avg_degree"]
    X = df[feature_cols]
    y = df["risk_score"]

    model = RandomForestRegressor(n_estimators=100, max_depth=4, random_state=42)

    # Leave-one-out cross validation since dataset is small
    loo = LeaveOneOut()
    scores = cross_val_score(model, X, y, cv=loo, scoring="neg_mean_absolute_error")
    print(f"Leave-One-Out CV Mean Absolute Error: {-scores.mean():.3f}")
    print("(Lower is better. Small dataset -> treat as a rough estimate, not a guarantee.)\n")

    # fit final model on all data
    model.fit(X, y)

    importances = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
    print("Feature importances:")
    print(importances, "\n")

    return model, feature_cols

def apply_model_to_graph(G, model, feature_cols, df):
    preds = model.predict(df[feature_cols])
    for (u, v), pred in zip(zip(df["u"], df["v"]), preds):
        G.edges[u, v]["ml_risk_score"] = float(pred)
    return G

if __name__ == "__main__":
    G = load_graph("data/processed/campus_graph_scored.graphml")
    incidents = pd.read_csv("data/raw/incidents.csv")

    df = build_edge_features(G, incidents)
    model, feature_cols = train_model(df)
    G = apply_model_to_graph(G, model, feature_cols, df)

    print("Original vs ML-predicted risk score per edge:\n")
    for u, v, data in G.edges(data=True):
        print(f"{u:28s} -- {v:28s} | original: {data['risk_score']:.2f} | ML predicted: {data['ml_risk_score']:.2f}")

    nx.write_graphml(G, "data/processed/campus_graph_ml.graphml")
    print("\nSaved ML-enhanced graph to data/processed/campus_graph_ml.graphml")