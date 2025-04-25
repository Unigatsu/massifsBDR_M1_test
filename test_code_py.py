import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
from shapely.geometry import Polygon

# Configuration de la page
st.set_page_config(layout="wide")
st.title("Dashboard de la Végétation des Massifs des Bouches-du-Rhône")

# Sidebar
with st.sidebar:
    st.header("Options")
    st.markdown("Cliquez sur un massif pour voir sa répartition de végétation.")

# Chargement des données
@st.cache_data
def load_data():
    gdf_massifs = gpd.read_file("massifs_13_mrs/massifs_13_mrs.shp")
    gdf_vegetation = gpd.read_file("veg_massifs_mrs/veg_massifs_mrs.shp")
    return gdf_massifs, gdf_vegetation

gdf_massifs, gdf_vegetation = load_data()

# Centrage carte
m = folium.Map(location=[43.5, 5.5], zoom_start=9)

# Couleurs végétation
couleurs_vegetation = {
    "Forêt": "#228B22",
    "Garrigue": "#ADFF2F",
    "Maquis": "#7FFF00",
    "Pelouse": "#32CD32",
    "Autre": "#808080"
}

# Ajout des massifs à la carte
def style_function(feature):
    return {
        'fillColor': 'lightblue',
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.6
    }

# Stocker le massif sélectionné
selected_nom_massif = None

# Ajout des massifs avec clic
def on_click_handler(feature, **kwargs):
    global selected_nom_massif
    selected_nom_massif = feature["properties"]["nom_maf"]

for _, row in gdf_massifs.iterrows():
    geo_json = folium.GeoJson(
        data=row["geometry"],
        style_function=style_function,
        tooltip=folium.Tooltip(row["nom_maf"]),
    )
    geo_json.add_to(m)

# Affichage carte
st.subheader("Carte interactive")
map_data = st_folium(m, height=500, width="100%")

# Vérification de sélection par carte
selected_nom_massif = None
if map_data and map_data.get("last_active_drawing"):
    clicked_geometry = map_data["last_active_drawing"]["geometry"]
    point = gpd.GeoSeries.from_geojson(clicked_geometry).centroid[0]
    for _, row in gdf_massifs.iterrows():
        if row.geometry.contains(point):
            selected_nom_massif = row["nom_maf"]
            break

# Affichage des infos du massif
if selected_nom_massif:
    st.subheader(f"Répartition de la végétation dans le massif : {selected_nom_massif}")
    gdf_sel = gdf_vegetation[gdf_vegetation["nom_maf"] == selected_nom_massif]

    if not gdf_sel.empty:
        df_pie = gdf_sel.groupby("NATURE")["surface_ve"].sum().reset_index()
        df_pie["%"] = df_pie["surface_ve"] / df_pie["surface_ve"].sum() * 100

        # Camembert
        fig, ax = plt.subplots()
        wedges, texts, autotexts = ax.pie(
            df_pie["%"],
            labels=df_pie["NATURE"],
            autopct="%1.1f%%",
            colors=[couleurs_vegetation.get(v, "#CCCCCC") for v in df_pie["NATURE"]],
            startangle=90
        )
        ax.axis("equal")
        st.pyplot(fig)
    else:
        st.warning("Aucune donnée de végétation pour ce massif.")
else:
    st.info("Cliquez sur un massif pour afficher les informations.")

