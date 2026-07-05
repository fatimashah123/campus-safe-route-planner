# campus-safe-route-planner
# Campus Safe Walking Route Planner

An ML-based route planner that suggests the safest walking paths on a campus, instead of just the shortest ones — built for Pak-Austria Fachhochschule Institute of Applied Sciences and Technology (PAF-IAST).

## What it does
- Models the campus walking network as a graph
- Scores each path segment for risk using incident data (simulated for this project due to lack of public real-world data access)
- Uses a modified shortest-path algorithm (Dijkstra) that balances distance vs. safety
- Includes an experimental ML model (Random Forest) to predict risk scores from features
- Interactive Streamlit GUI to compare Fastest / Safest / Balanced routes visually on a live map

## Tech stack
Python, NetworkX, scikit-learn, Streamlit, Folium

## How to run
\`\`\`bash
pip install -r requirements.txt
streamlit run src/app.py
\`\`\`

## Note on data
Incident data used here is synthetically generated to demonstrate the algorithm, since no public campus-specific incident dataset was available. The methodology is designed to plug in real incident data (e.g. from city open-data portals) when available.
