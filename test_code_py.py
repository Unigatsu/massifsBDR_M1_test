import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.colors as mcolors
import random

# --- Configuration de la page Streamlit ---
st.set_page_config(layout="wide")
st.title("Dashboard de la Végétation des Massifs des Bouches-du-Rhône")
st.markdown("Visualisation interactive de la végétation à partir de données Shapefile.")

# --- Sidebar pour les instructions ---
with st.sidebar:
    st.header("Options d'affichage")
    option_affichage = st.radio(
        "Afficher :",
        ("Massifs", "Végétation")
    )

# --- Chargement des fichiers shapefiles ---
@st.cache_data

def load_data():
    gdf_massifs = gpd.read_file("massifs_13_mrs/massifs_13_mrs.shp")
    gdf_vegetation = gpd.read_file("veg_massifs_mrs/veg_massifs_mrs.shp")
    return gdf_massifs, gdf_vegetation

gdf_massifs, gdf_vegetation = load_data()

# --- Colonnes de référence ---
colonne_id_massif = 'nom_maf'
colonne_nom_massif = 'nom_maf'
colonne_type_vegetation = 'NATURE'
colonne_surface = 'surface_ve'

# --- Création des couleurs pour la légende de végétation ---
types_vegetation = gdf_vegetation[colonne_type_vegetation].unique()
color_list = list(mcolors.CSS4_COLORS.values())
random.shuffle(color_list)
couleurs_vegetation = {veg_type: color_list[i % len(color_list)] for i, veg_type in enumerate(types_vegetation)}

# --- Carte interactive ---
col_map, col_info = st.columns([2, 1])

with col_map:
    m = folium.Map(location=[43.5, 5.5], zoom_start=9)

    if option_affichage == "Massifs":
        folium.GeoJson(
            gdf_massifs,
            name="Massifs",
            style_function=lambda x: {
                'fillColor': 'lightblue',
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.5
            },
            tooltip=folium.GeoJsonTooltip(fields=[colonne_nom_massif], aliases=["Massif :"])
        ).add_to(m)

    elif option_affichage == "Végétation":
        def style_function(feature):
            veg = feature['properties'][colonne_type_vegetation]
            return {
                'fillColor': couleurs_vegetation.get(veg, 'gray'),
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': 0.6
            }

        folium.GeoJson(
            gdf_vegetation,
            name="Végétation",
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(fields=[colonne_type_vegetation], aliases=["Type :"])
        ).add_to(m)

        # Légende personnalisée
        legend_html = """
        <div style='position: fixed; bottom: 50px; left: 50px; width: 250px; z-index:9999; font-size:14px;
                    background-color:white; border:2px solid grey; padding: 10px;'>
        <b>Légende Végétation</b><br>
        """
        for veg_type, color in couleurs_vegetation.items():
            legend_html += f"<i style='background:{color};width:12px;height:12px;float:left;margin-right:8px;'></i>{veg_type}<br>"
        legend_html += "</div>"
        m.get_root().html.add_child(folium.Element(legend_html))

    st_folium(m, height=600, width='100%')

with col_info:
    st.subheader("Détails du massif")
    nom_massif_selectionne = st.selectbox("Choisissez un massif :", gdf_massifs[colonne_nom_massif].unique())
    st.write(f"Massif sélectionné : **{nom_massif_selectionne}**")
    
    veg_massif = gdf_vegetation[gdf_vegetation[colonne_nom_massif] == nom_massif_selectionne]
    if not veg_massif.empty:
        surface_totale = veg_massif[colonne_surface].sum()
        repartition = veg_massif.groupby(colonne_type_vegetation)[colonne_surface].sum()
        repartition_percent = repartition / surface_totale * 100
        st.write("### Répartition de la végétation (%)")
        st.dataframe(repartition_percent.round(2).reset_index().rename(columns={colonne_surface: "% Surface"}))

        # Graphique camembert
        st.pyplot(repartition_percent.plot.pie(y=colonne_surface, autopct='%1.1f%%', figsize=(5, 5), legend=False).get_figure())
    else:
        st.warning("Aucune donnée de végétation pour ce massif.")

