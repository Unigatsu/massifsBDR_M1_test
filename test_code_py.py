# --- Imports ---
import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium

--- Configuration de la page Streamlit ---
st.set_page_config(layout="wide")
st.title("Dashboard de la Végétation des Massifs des Bouches-du-Rhône")
st.markdown("Visualisation interactive de la végétation à partir de shapefiles locaux.")

--- Sidebar pour les instructions ---
with st.sidebar:
    st.header("Options d'affichage")
    option_affichage = st.radio("Afficher :", ("Massifs", "Végétation"))
    st.header("Instructions")
    st.markdown("""
    
Les fichiers shapefiles doivent être présents dans les bons dossiers.
Les fichiers doivent contenir les colonnes suivantes :
nom_maf (nom du massif)
NATURE (type de végétation)
Cliquez sur un massif pour voir les types de végétation associés.""")

--- Chargement des données (sans dbf/shx/prj explicites) ---
@st.cache_data

def load_data():
    try:
        gdf_massifs = gpd.read_file("massifs_13_mrs/massifs_13_mrs.shp")
        gdf_vegetation = gpd.read_file("veg_massifs_mrs/veg_massifs_mrs.shp")
        return gdf_massifs, gdf_vegetation
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        return None, None

--- Données ---
gdf_massifs, gdf_vegetation = load_data()

if gdf_massifs is None or gdf_vegetation is None:
    st.stop()

--- Affichage carte et informations ---
col_map, col_info = st.columns([1, 1])

with col_map:
    st.subheader("Carte Interactive")
    m = folium.Map(location=[43.5, 5.5], zoom_start=9)

    def on_click_feature(feature, kwargs):
        return {"nom_maf": feature["properties"].get("nom_maf", None), "NATURE": feature["properties"].get("NATURE", None)}

    if option_affichage == "Massifs":
        gj = folium.GeoJson(
            gdf_massifs,
            name="Massifs",
            tooltip=folium.GeoJsonTooltip(fields=["nom_maf"], aliases=["Massif :"]),
            style_function=lambda x: {'fillColor': 'lightblue', 'color': 'black', 'weight': 1, 'fillOpacity': 0.5},
        )
        gj.add_to(m)

    elif option_affichage == "Végétation":
        gj = folium.GeoJson(
            gdf_vegetation,
            name="Végétation",
            tooltip=folium.GeoJsonTooltip(fields=["NATURE"], aliases=["Type :"]),
            style_function=lambda x: {'fillColor': 'lightgreen', 'color': 'darkgreen', 'weight': 0.5, 'fillOpacity': 0.7},
        )
        gj.add_to(m)

    folium.LayerControl().add_to(m)
    st_data = st_folium(m, height=500, width='100%')

with col_info:
    st.subheader("Informations")
    if st_data and st_data.get("last_active_drawing", None):
        props = st_data["last_active_drawing"]["properties"]
        if option_affichage == "Massifs":
            nom_massif = props.get("nom_maf", "Inconnu")
            st.write(f"Massif sélectionné : {nom_massif}")
            veg_data = gdf_vegetation[gdf_vegetation["nom_maf"] == nom_massif]
            types = veg_data["NATURE"].unique()
            if len(types) > 0:
                st.write("Types de végétation :")
                for t in types:
                    st.write(f"- {t}")
            else:
                st.write("Aucune donnée de végétation trouvée.")

        elif option_affichage == "Végétation":
            nature = props.get("NATURE", "Inconnu")
            st.write(f"Type de végétation sélectionné :** {nature}")
    else:
        st.info("Cliquez sur un élément de la carte pour voir les détails.")
