import folium
import networkx as nx
from risk_score import load_graph
from router import set_edge_costs, get_route

def plot_routes(G, source, target, output_path="data/processed/route_map.html"):
    # center map roughly on your campus
    center_lat = sum(float(G.nodes[n]["y"]) for n in G.nodes) / len(G.nodes)
    center_lon = sum(float(G.nodes[n]["x"]) for n in G.nodes) / len(G.nodes)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=17)

    # draw all edges lightly, colored by risk (green=low, red=high)
    for u, v, data in G.edges(data=True):
        a = (float(G.nodes[u]["y"]), float(G.nodes[u]["x"]))
        b = (float(G.nodes[v]["y"]), float(G.nodes[v]["x"]))
        risk = float(data.get("risk_score", 0))
        color = f"#{int(255*risk):02x}{int(255*(1-risk)):02x}00"  # red-green gradient
        folium.PolyLine([a, b], color=color, weight=3, opacity=0.5,
                         tooltip=f"{u} - {v} | risk: {risk:.2f}").add_to(m)

    # mark all nodes
    for n, data in G.nodes(data=True):
        folium.CircleMarker(
            location=(float(data["y"]), float(data["x"])),
            radius=4, color="blue", fill=True, fill_opacity=0.7,
            tooltip=n
        ).add_to(m)

    # compute and draw the three routes
    route_configs = [
        ("FASTEST", 1.0, 0.0, "orange"),
        ("SAFEST", 0.2, 0.8, "green"),
        ("BALANCED", 0.5, 0.5, "purple"),
    ]

    for label, alpha, beta, color in route_configs:
        G = set_edge_costs(G, alpha=alpha, beta=beta)
        path, length, risk = get_route(G, source, target)
        coords = [(float(G.nodes[n]["y"]), float(G.nodes[n]["x"])) for n in path]
        folium.PolyLine(
            coords, color=color, weight=6, opacity=0.9,
            tooltip=f"{label}: {length:.1f}m, risk {risk:.2f}"
        ).add_to(m)
        print(f"{label}: distance={length:.1f}m, risk={risk:.2f}")

    # mark source/target clearly
    folium.Marker((float(G.nodes[source]["y"]), float(G.nodes[source]["x"])),
                  popup="START", icon=folium.Icon(color="black")).add_to(m)
    folium.Marker((float(G.nodes[target]["y"]), float(G.nodes[target]["x"])),
                  popup="END", icon=folium.Icon(color="black")).add_to(m)

    m.save(output_path)
    print(f"\nMap saved to {output_path}")

if __name__ == "__main__":
    G = load_graph("data/processed/campus_graph_scored.graphml")
    plot_routes(G, source="main_executive_block", target="suites_foreign_faculty")