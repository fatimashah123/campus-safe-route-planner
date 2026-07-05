import networkx as nx
import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2

def haversine(coord1, coord2):
    R = 6371000
    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def point_to_segment_distance(p, a, b):
    """Shortest distance from point p to line segment a-b (all lat/lon tuples), in meters."""
    # convert to a local flat approx (fine at campus scale)
    def to_xy(pt, origin):
        R = 6371000
        lat, lon = radians(pt[0]), radians(pt[1])
        lat0, lon0 = radians(origin[0]), radians(origin[1])
        x = R * (lon - lon0) * cos(lat0)
        y = R * (lat - lat0)
        return np.array([x, y])

    origin = a
    P, A, B = to_xy(p, origin), to_xy(a, origin), to_xy(b, origin)
    AB = B - A
    t = np.dot(P - A, AB) / (np.dot(AB, AB) + 1e-9)
    t = max(0, min(1, t))
    closest = A + t * AB
    return np.linalg.norm(P - closest)

def load_graph(path="data/processed/campus_graph.graphml"):
    return nx.read_graphml(path)

def assign_risk_to_edges(G, incidents_df, buffer_m=40):
    """
    For each incident, find the nearest edge (within buffer_m meters) and
    accumulate severity onto it. Edges with no nearby incidents get risk 0.
    """
    for u, v, data in G.edges(data=True):
        data["incident_count"] = 0
        data["risk_raw"] = 0.0

    for _, row in incidents_df.iterrows():
        p = (row["latitude"], row["longitude"])
        best_edge = None
        best_dist = float("inf")

        for u, v, data in G.edges(data=True):
            a = (float(G.nodes[u]["y"]), float(G.nodes[u]["x"]))
            b = (float(G.nodes[v]["y"]), float(G.nodes[v]["x"]))
            d = point_to_segment_distance(p, a, b)
            if d < best_dist:
                best_dist = d
                best_edge = (u, v)

        if best_edge and best_dist <= buffer_m:
            u, v = best_edge
            G.edges[u, v]["incident_count"] += 1
            G.edges[u, v]["risk_raw"] += row["severity"]

    # normalize risk_raw to 0-1 range across all edges
    all_risk = [d["risk_raw"] for _, _, d in G.edges(data=True)]
    max_risk = max(all_risk) if max(all_risk) > 0 else 1
    for u, v, data in G.edges(data=True):
        data["risk_score"] = data["risk_raw"] / max_risk

    return G

if __name__ == "__main__":
    G = load_graph()
    incidents = pd.read_csv("data/raw/incidents.csv")

    G = assign_risk_to_edges(G, incidents, buffer_m=60)

    print("Edge risk scores:\n")
    for u, v, d in G.edges(data=True):
        print(f"{u:30s} -- {v:30s} | incidents: {d['incident_count']:3d} | risk_score: {d['risk_score']:.2f}")

    nx.write_graphml(G, "data/processed/campus_graph_scored.graphml")
    print("\nSaved scored graph to data/processed/campus_graph_scored.graphml")