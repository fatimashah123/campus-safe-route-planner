import streamlit as st
import folium
from streamlit_folium import st_folium

from risk_score import load_graph
from router import set_edge_costs, get_route

st.set_page_config(
    page_title="Campus Safe Route Planner",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .hero {
        padding: 1.6rem 2rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 1px solid #2d3748;
        margin-bottom: 1.2rem;
    }
    .hero h1 {
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        color: #f9fafb;
    }
    .hero p {
        color: #9ca3af;
        margin-top: 0.4rem;
        font-size: 0.95rem;
    }
    .card {
        background: #161b22;
        border: 1px solid #2d3748;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
    }
    .card h4 {
        margin-top: 0;
        color: #e5e7eb;
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #9ca3af;
    }
    .metric-row {
        display: flex;
        gap: 1rem;
    }
    .metric-box {
        flex: 1;
        background: #0d1117;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 0.9rem 1rem;
        text-align: center;
    }
    .metric-box .value {
        font-size: 1.6rem;
        font-weight: 800;
        color: #f9fafb;
    }
    .metric-box .label {
        font-size: 0.75rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 0.2rem;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .badge-fastest { background: #f59e0b33; color: #f59e0b; }
    .badge-safest { background: #10b98133; color: #10b981; }
    .badge-balanced { background: #8b5cf633; color: #8b5cf6; }
    .legend-swatch {
        display: inline-block;
        width: 14px;
        height: 14px;
        border-radius: 3px;
        margin-right: 6px;
        vertical-align: middle;
    }
    .compare-row {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid #2d3748;
        font-size: 0.9rem;
    }
    .compare-row:last-child { border-bottom: none; }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: 700;
        padding: 0.6rem 0;
        background: #6366f1;
        border: none;
    }
    .stButton>button:hover {
        background: #4f46e5;
    }
</style>
""", unsafe_allow_html=True)

MODE_COLORS = {"Fastest": "#f59e0b", "Safest": "#10b981", "Balanced": "#8b5cf6"}
MODE_BADGE_CLASS = {"Fastest": "badge-fastest", "Safest": "badge-safest", "Balanced": "badge-balanced"}
MODE_WEIGHTS = {"Fastest": (1.0, 0.0), "Safest": (0.2, 0.8), "Balanced": (0.5, 0.5)}


@st.cache_resource
def get_graph():
    return load_graph("data/processed/campus_graph_scored.graphml")


G_BASE = get_graph()
locations = sorted(G_BASE.nodes)

if "route_result" not in st.session_state:
    st.session_state.route_result = None
if "route_error" not in st.session_state:
    st.session_state.route_error = None

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>Campus Safe Walking Route Planner</h1>
    <p>PAF-IAST edition. Like Google Maps, but it actually clocks whether the path is sketchy.
    Routes are weighted using simulated safety-incident data, not vibes.</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### plan the route")
    st.caption("pick your start, pick your destination, let the algorithm do the worrying")

    default_source_idx = locations.index("main_executive_block") if "main_executive_block" in locations else 0
    default_target_idx = locations.index("suites_foreign_faculty") if "suites_foreign_faculty" in locations else min(1, len(locations)-1)

    source = st.selectbox("starting from", locations, index=default_source_idx, key="source_select")
    target = st.selectbox("heading to", locations, index=default_target_idx, key="target_select")

    mode = st.radio(
        "what's the vibe today",
        ["Fastest", "Safest", "Balanced"],
        index=2,
        key="mode_radio",
        help="Fastest = shortest distance, no cap. Safest = avoids sketchy zones even if it takes longer. Balanced = a bit of both.",
    )

    same_place = source == target
    if same_place:
        st.warning("start and destination are literally the same place.")

    find_clicked = st.button("find my route", disabled=same_place)

    st.divider()
    st.markdown("**risk legend**")
    st.markdown(
        '<span class="legend-swatch" style="background:#10b100;"></span> low risk &nbsp;&nbsp;'
        '<span class="legend-swatch" style="background:#b1b100;"></span> medium &nbsp;&nbsp;'
        '<span class="legend-swatch" style="background:#e00000;"></span> high risk',
        unsafe_allow_html=True,
    )
    st.caption(
        "risk scores are simulated for this project (no real incident reports were used) — "
        "read the map colors as a demo of the algorithm, not an actual safety audit."
    )

# ---------------------------------------------------------------------------
# Compute route on click (stored in session_state so it survives map reruns)
# ---------------------------------------------------------------------------
if find_clicked and not same_place:
    try:
        G = get_graph()
        alpha, beta = MODE_WEIGHTS[mode]
        G = set_edge_costs(G, alpha=alpha, beta=beta)
        path, length, risk = get_route(G, source, target)
        coords = [(float(G.nodes[n]["y"]), float(G.nodes[n]["x"])) for n in path]

        comparisons = {}
        for label, (a_w, b_w) in MODE_WEIGHTS.items():
            Gm = set_edge_costs(get_graph(), alpha=a_w, beta=b_w)
            p, l, r = get_route(Gm, source, target)
            comparisons[label] = (l, r)

        st.session_state.route_result = {
            "mode": mode,
            "source": source,
            "target": target,
            "path": path,
            "length": length,
            "risk": risk,
            "coords": coords,
            "comparisons": comparisons,
        }
        st.session_state.route_error = None
    except Exception as e:
        st.session_state.route_error = str(e)
        st.session_state.route_result = None

# ---------------------------------------------------------------------------
# Map builder
# ---------------------------------------------------------------------------
def build_map(highlight_coords=None, highlight_mode=None):
    G = get_graph()
    center_lat = sum(float(G.nodes[n]["y"]) for n in G.nodes) / len(G.nodes)
    center_lon = sum(float(G.nodes[n]["x"]) for n in G.nodes) / len(G.nodes)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=17, tiles="CartoDB dark_matter")

    for u, v, data in G.edges(data=True):
        a = (float(G.nodes[u]["y"]), float(G.nodes[u]["x"]))
        b = (float(G.nodes[v]["y"]), float(G.nodes[v]["x"]))
        risk = float(data.get("risk_score", 0))
        color = f"#{int(255 * risk):02x}{int(255 * (1 - risk)):02x}00"
        folium.PolyLine(
            [a, b], color=color, weight=4, opacity=0.65,
            tooltip=f"{u} - {v} | risk: {risk:.2f}"
        ).add_to(m)

    for n, data in G.nodes(data=True):
        folium.CircleMarker(
            location=(float(data["y"]), float(data["x"])),
            radius=5, color="#60a5fa", fill=True, fill_color="#60a5fa", fill_opacity=0.9,
            tooltip=n
        ).add_to(m)

    if highlight_coords:
        folium.PolyLine(
            highlight_coords, color=MODE_COLORS.get(highlight_mode, "#ffffff"),
            weight=7, opacity=0.95, tooltip=highlight_mode
        ).add_to(m)
        folium.Marker(highlight_coords[0], popup="START",
                       icon=folium.Icon(color="green", icon="play")).add_to(m)
        folium.Marker(highlight_coords[-1], popup="END",
                       icon=folium.Icon(color="red", icon="flag")).add_to(m)

    return m


# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------
col_map, col_info = st.columns([2, 1], gap="medium")

result = st.session_state.route_result

with col_map:
    if result:
        m = build_map(result["coords"], result["mode"])
    else:
        m = build_map()
    st_folium(m, width=None, height=560, key="main_map", returned_objects=[])

with col_info:
    if st.session_state.route_error:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.error(f"couldn't compute a route: {st.session_state.route_error}")
        st.markdown('</div>', unsafe_allow_html=True)

    elif result:
        badge_class = MODE_BADGE_CLASS[result["mode"]]
        st.markdown(f"""
        <div class="card">
            <h4>route locked in</h4>
            <span class="badge {badge_class}">{result['mode']}</span>
            <p style="color:#e5e7eb; margin-top:0.8rem; font-size:0.9rem;">
                {result['source']} &rarr; {result['target']}
            </p>
            <div class="metric-row">
                <div class="metric-box">
                    <div class="value">{result['length']:.0f} m</div>
                    <div class="label">distance</div>
                </div>
                <div class="metric-box">
                    <div class="value">{result['risk']:.2f}</div>
                    <div class="label">risk score</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="card"><h4>the path</h4>', unsafe_allow_html=True)
        st.write(" &rarr; ".join(result["path"]))
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card"><h4>how the modes compare</h4>', unsafe_allow_html=True)
        for label, (l, r) in result["comparisons"].items():
            tag = " (selected)" if label == result["mode"] else ""
            dot_color = MODE_COLORS[label]
            st.markdown(
                f'<div class="compare-row">'
                f'<span><span class="legend-swatch" style="background:{dot_color};"></span>{label}{tag}</span>'
                f'<span>{l:.0f} m &middot; risk {r:.2f}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="card">
            <h4>no route yet</h4>
            <p style="color:#9ca3af; font-size:0.9rem;">
                pick a start and destination in the sidebar, choose your vibe,
                then hit <b>find my route</b>. the map updates instantly.
            </p>
        </div>
        """, unsafe_allow_html=True)