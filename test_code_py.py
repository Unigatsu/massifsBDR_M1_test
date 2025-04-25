import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Dashboard de la Végétation des Massifs des Bouches-du-Rhône réalisé par Augustin DUPUIS")

# --- Sidebar ---
with st.sidebar:
    st.header("Options d'affichage")
    option_affichage = st.radio("Afficher :", ("Massifs", "Végétation"))
    st.markdown("Cliquez sur un massif pour afficher la répartition de la végétation.")

# --- Chargement des données ---
@st.cache_data
def load_data():
    gdf_massifs = gpd.read_file("massifs_13_mrs/massifs_13_mrs.shp")
    gdf_vegetation = gpd.read_file("veg_massifs_mrs/veg_massifs_mrs.shp")
    return gdf_massifs, gdf_vegetation

gdf_massifs, gdf_vegetation = load_data()

# --- Noms de colonnes ---
colonne_id_massif = 'nom_maf'
colonne_type_vegetation = 'NATURE'
colonne_surface = 'surface_ve'

# --- Carte Folium ---
col_map, col_info = st.columns([1, 1])

with col_map:
    st.subheader("Carte interactive")
    m = folium.Map(location=[43.5, 5.5], zoom_start=9)

    if option_affichage == "Massifs":
        folium.GeoJson(
            gdf_massifs,
            name="Massifs",
            tooltip=folium.GeoJsonTooltip(fields=[colonne_id_massif], aliases=["Massif :"])
        ).add_to(m)
    elif option_affichage == "Végétation":
        folium.GeoJson(
            gdf_vegetation,
            name="Végétation",
            tooltip=folium.GeoJsonTooltip(fields=[colonne_type_vegetation], aliases=["Type :"])
        ).add_to(m)

    st_data = st_folium(m, height=500, width='100%')

with col_info:
    st.subheader("Informations")

    # Récupérer l'objet cliqué
    if st_data and st_data.get("last_active_drawing"):
        feature = st_data["last_active_drawing"]
        props = feature["properties"]
        massif_nom = props.get(colonne_id_massif)

        if option_affichage == "Massifs" and massif_nom:
            st.markdown(f"### Massif sélectionné : `{massif_nom}`")
            veg_massif = gdf_vegetation[gdf_vegetation[colonne_id_massif] == massif_nom]

            if not veg_massif.empty:
                grouped = veg_massif.groupby(colonne_type_vegetation)[colonne_surface].sum()
                grouped_percent = grouped / grouped.sum() * 100

                st.markdown("**Répartition des types de végétation (% surface)**")
                fig, ax = plt.subplots()
                ax.pie(grouped_percent, labels=grouped_percent.index, autopct='%1.1f%%', startangle=90)
                ax.axis("equal")
                st.pyplot(fig)
            else:
                st.info("Aucune donnée de végétation pour ce massif.")
        else:
            st.info("Sélectionnez un massif pour afficher ses informations.")
    else:
        st.info("Cliquez sur un élément de la carte pour voir les détails.")

# --- Menu déroulant des types de végétation ---
st.subheader("Analyse par type de végétation")

# Liste des types de végétation uniques
types_vegetation = gdf_vegetation[colonne_type_vegetation].dropna().unique()
type_selectionne = st.selectbox("Choisissez un type de végétation :", sorted(types_vegetation))

# Filtrer les données selon le type sélectionné
veg_type = gdf_vegetation[gdf_vegetation[colonne_type_vegetation] == type_selectionne]

if not veg_type.empty:
    # Calcul de la surface par massif pour ce type
    surface_par_massif = veg_type.groupby(colonne_id_massif)[colonne_surface].sum()

    # Surface totale de chaque massif
    surface_totale_massif = gdf_vegetation.groupby(colonne_id_massif)[colonne_surface].sum()

    # Calcul du pourcentage
    df_percent = (surface_par_massif / surface_totale_massif * 100).reset_index()
    df_percent.columns = ["Massif", f"% de {type_selectionne}"]

    st.dataframe(df_percent.style.format({f"% de {type_selectionne}": "{:.2f}%"}))
else:
    st.info("Aucune donnée disponible pour ce type de végétation.")

