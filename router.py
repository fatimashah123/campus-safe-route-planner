import networkx as nx
from risk_score import load_graph

def set_edge_costs(G, alpha=0.5, beta=0.5):
    """
    alpha = weight given to distance (shorter route preferred)
    beta  = weight given to risk (safer route preferred)
    Both should sum to 1 for interpretability, but not required.
    """
    lengths = [float(d["length"]) for _, _, d in G.edges(data=True)]
    max_len = max(lengths) if lengths else 1

    for u, v, data in G.edges(data=True):
        norm_len = float(data["length"]) / max_len       # 0-1 scaled distance
        risk = float(data.get("risk_score", 0))           # already 0-1
        data["cost"] = alpha * norm_len + beta * risk

    return G

def get_route(G, source, target, weight="cost"):
    path = nx.shortest_path(G, source=source, target=target, weight=weight)
    total_length = sum(float(G[path[i]][path[i+1]]["length"]) for i in range(len(path)-1))
    total_risk = sum(float(G[path[i]][path[i+1]]["risk_score"]) for i in range(len(path)-1))
    return path, total_length, total_risk

if __name__ == "__main__":
    G = load_graph("data/processed/campus_graph_scored.graphml")

    source = "main_executive_block"
    target = "suites_foreign_faculty"

    print(f"Route from {source} to {target}\n")

    # Fastest route (ignore risk)
    G = set_edge_costs(G, alpha=1.0, beta=0.0)
    fast_path, fast_len, fast_risk = get_route(G, source, target)
    print("FASTEST route:")
    print(" -> ".join(fast_path))
    print(f"Distance: {fast_len:.1f} m | Total risk: {fast_risk:.2f}\n")

    # Safest route (heavily prioritize risk)
    G = set_edge_costs(G, alpha=0.2, beta=0.8)
    safe_path, safe_len, safe_risk = get_route(G, source, target)
    print("SAFEST route:")
    print(" -> ".join(safe_path))
    print(f"Distance: {safe_len:.1f} m | Total risk: {safe_risk:.2f}\n")

    # Balanced route
    G = set_edge_costs(G, alpha=0.5, beta=0.5)
    bal_path, bal_len, bal_risk = get_route(G, source, target)
    print("BALANCED route:")
    print(" -> ".join(bal_path))
    print(f"Distance: {bal_len:.1f} m | Total risk: {bal_risk:.2f}")