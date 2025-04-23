import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import io
import zipfile

# --- Configuration de la page Streamlit ---
st.set_page_config(layout="wide")
st.title("Dashboard de la Végétation des Massifs des Bouches-du-Rhône")
st.markdown("Visualisation interactive de la végétation à partir de données Shapefile hébergées sur GitHub.")

# --- Sidebar pour les instructions ---
with st.sidebar:
    st.header("Instructions")
    st.markdown("1. Les données Shapefile doivent être zippées et contenir au minimum les fichiers `.shp`, `.dbf`, `.shx` et `.prj`.")
    st.markdown("2. Assurez-vous que les URL GitHub vers vos fichiers zippés sont correctes.")
    st.markdown("3. Le DataFrame GeoPandas résultant doit contenir une colonne géographique (geometry) et une ou plusieurs colonnes de données de végétation.")
    st.markdown("4. Sélectionnez un massif sur la carte pour afficher le graphique de sa végétation.")

# --- Fonction pour charger les données depuis GitHub ---
@st.cache_data
def load_data_from_github(github_url):
    try:
        response = st.connection("http", base_url=github_url.rsplit('/', 1)[0]).get(github_url.rsplit('/', 1)[1])
        response.raise_for_status()  # Raise an exception for HTTP errors
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            shp_file = [f for f in zf.namelist() if f.endswith(".shp")][0]
            with zf.open(shp_file) as shp:
                gdf = gpd.read_file(shp)
        return gdf
    except Exception as e:
        st.error(f"Erreur lors du chargement des données depuis {github_url}: {e}")
        return None

# --- URL de tes fichiers Shapefile zippés sur GitHub ---
# Remplacez ici par les URL réelles de vos fichiers .zip
url_massif_1 = "https://github.com/Unigatsu/massifsBDR_M1_test/blob/06e62f89053fe0f0eb6b589037d485de4cdae594/massifs_13_mrs.zip"
url_massif_2 = "https://github.com/Unigatsu/massifsBDR_M1_test/blob/1acf14818b78e9071744de78d0d0dddb096699c0/veg_massifs_mrs.zip"

# --- Chargement des données ---
gdf_massif_1 = load_data_from_github(url_massif_1)
gdf_massif_2 = load_data_from_github(url_massif_2)

# --- Vérification du chargement des données ---
if gdf_massif_1 is None or gdf_massif_2 is None:
    st.stop()

# --- Fusion des GeoDataFrames (si nécessaire) ---
# Si vos deux fichiers contiennent des informations similaires et que vous voulez les afficher ensemble sur la carte
# Assurez-vous qu'ils ont les mêmes noms de colonnes pour la fusion ou renommez-les.
gdf_all = pd.concat([gdf_massif_1, gdf_massif_2], ignore_index=True)

# --- Création de la carte interactive avec Folium ---
st.subheader("Carte Interactive des Massifs")
m = folium.Map(location=[43.5, 5.5], zoom_start=9)  # Centre approximatif des Bouches-du-Rhône

# Fonction pour ajouter des GeoJSON layers à la carte et stocker les informations
selected_massif = st.session_state.get("selected_massif")

def add_geojson_layer(gdf, name):
    folium.GeoJson(
        gdf,
        name=name,
        style_function=lambda x: {'fillColor': 'green', 'color': 'black', 'weight': 1, 'fillOpacity': 0.5},
        tooltip=folium.GeoJsonTooltip(fields=['nom_du_massif'] if 'nom_du_massif' in gdf.columns else gdf.columns[0], aliases=['Massif:'] if 'nom_du_massif' in gdf.columns else [f'ID:']),
        highlight_function=lambda x: {'fillColor': 'lime', 'color': 'black', 'weight': 3, 'fillOpacity': 0.7},
        # Ajouter un gestionnaire d'événements de clic pour stocker le massif sélectionné
        on_click="function(feature) { L.setOptions({fillColor: 'red'}); sessionStorage.setItem('selected_massif', feature.properties." + ('nom_du_massif' if 'nom_du_massif' in gdf.columns else gdf.columns[0]) + "); }"
    ).add_to(m)

if gdf_massif_1 is not None:
    add_geojson_layer(gdf_massif_1, "Massif 1")
if gdf_massif_2 is not None:
    add_geojson_layer(gdf_massif_2, "Massif 2")

folium.LayerControl().add_to(m)

# Affichage de la carte dans Streamlit
map_output = st_folium(m, height=500, width='100%')

# Récupérer le massif sélectionné depuis l'état de la session
clicked_massif = map_output.last_object_clicked
selected_massif_name = st.session_state.get("selected_massif")

st.subheader("Graphique de la Végétation")

if selected_massif_name:
    st.info(f"Massif sélectionné : {selected_massif_name}")
    # Filtrer le GeoDataFrame en fonction du massif sélectionné
    selected_gdf = gdf_all[gdf_all['nom_du_massif'] == selected_massif_name] if 'nom_du_massif' in gdf_all.columns else None
    if selected_gdf is None and gdf_all.shape[0] > 0:
        selected_gdf = gdf_all[gdf_all[gdf_all.columns[0]] == selected_massif_name]

    if selected_gdf is not None and not selected_gdf.empty:
        # Identifier les colonnes de végétation (adaptez ceci en fonction de vos données)
        vegetation_columns = [col for col in selected_gdf.columns if col not in ['geometry', 'nom_du_massif']] # Exemple
        if vegetation_columns:
            # Créer un DataFrame pour le graphique
            vegetation_data = selected_gdf[vegetation_columns].mean().sort_values(ascending=False)
            fig, ax = plt.subplots()
            vegetation_data.plot(kind='bar', ax=ax)
            ax.set_title(f"Répartition de la Végétation pour {selected_massif_name}")
            ax.set_xlabel("Type de Végétation")
            ax.set_ylabel("Moyenne (unité selon vos données)")
            st.pyplot(fig)
        else:
            st.warning("Aucune colonne de végétation trouvée pour ce massif.")
    else:
        st.warning(f"Aucune donnée trouvée pour le massif : {selected_massif_name}")
else:
    st.info("Cliquez sur un massif de la carte pour afficher le graphique de sa végétation.")
