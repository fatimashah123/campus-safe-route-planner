import networkx as nx
from math import radians, sin, cos, sqrt, atan2

def haversine(coord1, coord2):
    """Distance in meters between two lat/long points"""
    R = 6371000
    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def build_campus_graph(k_nearest=3):
    G = nx.Graph()

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

    for name, coord in nodes.items():
        G.add_node(name, y=coord[0], x=coord[1])

    # auto-connect each node to its k nearest neighbors
    names = list(nodes.keys())
    for a in names:
        dists = []
        for b in names:
            if a != b:
                d = haversine(nodes[a], nodes[b])
                dists.append((d, b))
        dists.sort()
        for d, b in dists[:k_nearest]:
            if not G.has_edge(a, b):
                G.add_edge(a, b, length=d)

    nx.write_graphml(G, "data/processed/campus_graph.graphml")
    return G

if __name__ == "__main__":
    G = build_campus_graph()
    print(f"Nodes: {len(G.nodes)}, Edges: {len(G.edges)}\n")
    for u, v, d in G.edges(data=True):
        print(f"{u:30s} -- {v:30s} : {d['length']:.1f} m")