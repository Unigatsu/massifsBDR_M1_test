import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# --- Chargement des données ---
gdf_massifs = gpd.read_file("data/massifs_forestiers.shp")
gdf_vegetation = gpd.read_file("data/vegetation_par_massif.shp")

# --- Colonnes utilisées ---
colonne_nom_massif = "nom_massif"
colonne_type_vegetation = "NATURE"
colonne_surface_vegetation = "surface_ve"
colonne_lien_vegetation_massif = "nom_massif"

# --- Interface ---
st.set_page_config(layout="wide")
st.title("Répartition de la végétation par massif forestier")

# --- Colonnes pour mise en page ---
col_map, col_info = st.columns([2, 1])

# --- Carte interactive avec sélection de massif ---
with col_map:
    st.subheader("Carte Interactive")
    m = folium.Map(location=[43.5, 5.5], zoom_start=9)

    folium.GeoJson(
        gdf_massifs,
        name="Massifs",
        tooltip=folium.GeoJsonTooltip(fields=[colonne_nom_massif], aliases=["Massif :"]),
    ).add_to(m)

    folium.LayerControl().add_to(m)

    map_data = st_folium(m, height=500, width='100%', returned_objects=["last_active_drawing"])

# --- Informations et graphique camembert ---
with col_info:
    st.subheader("Informations")

    selected_feature = map_data.get("last_active_drawing")
    if selected_feature and "properties" in selected_feature:
        selected_nom_massif = selected_feature["properties"].get(colonne_nom_massif)

        st.write(f"**Massif sélectionné :** {selected_nom_massif}")

        # Filtrage des données de végétation
        vegetation_massif = gdf_vegetation[gdf_vegetation[colonne_lien_vegetation_massif] == selected_nom_massif]

        if not vegetation_massif.empty:
            # Groupement des surfaces par type de végétation
            surface_par_type = vegetation_massif.groupby(colonne_type_vegetation)[colonne_surface_vegetation].sum()
            pourcentages = surface_par_type / surface_par_type.sum() * 100

            # Affichage du camembert
            fig, ax = plt.subplots()
            ax.pie(pourcentages, labels=pourcentages.index, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            st.pyplot(fig)
        else:
            st.info("Aucune donnée de végétation pour ce massif.")
    else:
        st.info("Cliquez sur un massif dans la carte pour afficher les informations.")

