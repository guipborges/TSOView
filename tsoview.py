import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
from shapely.geometry import shape, Point
from shapely.validation import make_valid

# Function to get the center of the selected country
def get_country_center(selected_country_iso, geojson):
    for feature in geojson["features"]:
        if feature["properties"]["ISO2"] == selected_country_iso:
            geometry = shape(feature["geometry"])
            if geometry.is_valid:
                return geometry.centroid.y, geometry.centroid.x
    return [48, 16]  # Fallback center

# Load and validate GeoJSON
def load_valid_geojson(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)
        for feature in geojson_data["features"]:
            geometry = shape(feature["geometry"])
            if not geometry.is_valid:
                feature["geometry"] = make_valid(geometry).__geo_interface__
    return geojson_data

# Function to load JSON file as pandas DataFrame
def load_json_as_dataframe(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return pd.json_normalize(json.load(f))

# Function to get neighboring countries from tso_data_cleaned.json
def get_neighbors(selected_country_iso, data):
    row = data[data["Acronym"] == selected_country_iso]
    if not row.empty:
        return row.iloc[0].get("neighbors", [])
    return []

# Load data
geojson_data = load_valid_geojson("europe.geojson")
data = load_json_as_dataframe("tso_data_cleaned.json")

# Initialize states
if "selected_country" not in st.session_state:
    st.session_state["selected_country"] = data["Country"].iloc[0]
if "selected_acronym" not in st.session_state:
    st.session_state["selected_acronym"] = data["Acronym"].iloc[0]
if "selected_tso" not in st.session_state:
    st.session_state["selected_tso"] = data["Company"].iloc[0]

# Synchronize selectors
def sync_selections():
    if st.session_state["country_select"] != st.session_state["selected_country"]:
        row = data[data["Country"] == st.session_state["country_select"]].iloc[0]
    elif st.session_state["acronym_select"] != st.session_state["selected_acronym"]:
        row = data[data["Acronym"] == st.session_state["acronym_select"]].iloc[0]
    else:
        row = data[data["Company"] == st.session_state["tso_select"]].iloc[0]

    st.session_state["selected_country"] = row["Country"]
    st.session_state["selected_acronym"] = row["Acronym"]
    st.session_state["selected_tso"] = row["Company"]

# UI Selectors
st.title("Interactive TSO Map in Europe")
col1, col2, col3 = st.columns(3)

with col1:
    st.selectbox("Select Country:", data["Country"].unique(), 
                 index=data["Country"].tolist().index(st.session_state["selected_country"]), 
                 key="country_select", on_change=sync_selections)

with col2:
    st.selectbox("Select Acronym:", data["Acronym"].unique(), 
                 index=data["Acronym"].tolist().index(st.session_state["selected_acronym"]), 
                 key="acronym_select", on_change=sync_selections)

with col3:
    st.selectbox("Select TSO Name:", data["Company"].unique(), 
                 index=data["Company"].tolist().index(st.session_state["selected_tso"]), 
                 key="tso_select", on_change=sync_selections)

# Update and get neighbors
country_iso = st.session_state["selected_acronym"]
neighbors = get_neighbors(country_iso, data)
center_coords = get_country_center(country_iso, geojson_data)

# Map visualization
m = folium.Map(location=center_coords, zoom_start=6, tiles="CartoDB positron")
for feature in geojson_data["features"]:
    iso_code = feature["properties"]["ISO2"]
    color = "red" if iso_code in neighbors else "blue" if iso_code == country_iso else "lightgray"
    folium.GeoJson(
        feature,
        style_function=lambda x, color=color: {
            "fillColor": color,
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.7 if color != "lightgray" else 0.4,
        },
        tooltip=feature["properties"]["ISO2"]
    ).add_to(m)

st_folium(m, width=700, height=500)

# Display Information
# Display Information
st.write(f"**Country:** {st.session_state['selected_country']}")
st.write(f"**Acronym:** {st.session_state['selected_acronym']}")
st.write(f"**TSO Name:** {st.session_state['selected_tso']}")
st.write("**Neighboring Countries and TSOs:**")

# Combine neighboring acronyms with country names and TSO names
neighboring_info = []
for acronym in neighbors:
    row = data[data["Acronym"] == acronym]
    if not row.empty:
        country_name = row.iloc[0]["Country"]
        tso_name = row.iloc[0]["Company"]
        neighboring_info.append(f"{acronym} - {country_name} ({tso_name})")

# Display neighboring countries with details
if neighboring_info:
    for info in neighboring_info:
        st.write(f"- {info}")
else:
    st.write("No neighboring countries found.")

