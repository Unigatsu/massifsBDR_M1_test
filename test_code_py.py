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
    st.markdown("3. Le fichier des massifs doit contenir une colonne d'identification unique (ex: 'id_massif', 'nom_massif').")
    st.markdown("4. Le fichier de végétation doit contenir une colonne géographique (geometry) et une colonne de 'classe' liant la végétation au massif correspondant (ex: 'id_massif').")
    st.markdown("5. Sélectionnez un massif sur la carte pour afficher le graphique de sa végétation.")

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
url_massifs = "https://github.com/Unigatsu/massifsBDR_M1_test/blob/567dd868905ab7ffde26ef9594f804d445835945/massifs_13_mrs.zip"
url_vegetation = "https://github.com/Unigatsu/massifsBDR_M1_test/blob/6666ff74a9c8fb10f25ec99751dc5e539303952a/veg_massifs_mrs.zip"

# --- Chargement des données ---
gdf_massifs = load_data_from_github(url_massifs)
gdf_vegetation = load_data_from_github(url_vegetation)

# --- Vérification du chargement des données ---
if gdf_massifs is None or gdf_vegetation is None:
    st.stop()

# --- Nom de la colonne d'identification des massifs et de la colonne de liaison dans la végétation ---
colonne_id_massif = 'nom_maf'  # Remplacez par le nom réel de la colonne dans gdf_massifs
colonne_lien_vegetation_massif = 'nom_maf'  # Remplacez par le nom réel de la colonne dans gdf_vegetation

# --- Création de la carte interactive avec Folium ---
st.subheader("Carte Interactive des Massifs")
m = folium.Map(location=[43.5, 5.5], zoom_start=9)

# Fonction pour ajouter les massifs à la carte et stocker l'id sélectionné
selected_massif_id = st.session_state.get("selected_massif_id")

def add_massifs_to_map(gdf, id_col):
    folium.GeoJson(
        gdf,
        name="Massifs",
        style_function=lambda x: {'fillColor': 'lightblue', 'color': 'black', 'weight': 1, 'fillOpacity': 0.5},
        tooltip=folium.GeoJsonTooltip(fields=[id_col], aliases=['Massif ID:']),
        highlight_function=lambda x: {'fillColor': 'blue', 'color': 'black', 'weight': 3, 'fillOpacity': 0.7},
        # Ajouter un gestionnaire d'événements de clic pour stocker l'ID du massif sélectionné
        on_click="function(feature) { L.setOptions({fillColor: 'red'}); sessionStorage.setItem('selected_massif_id', feature.properties." + id_col + "); }"
    ).add_to(m)

if gdf_massifs is not None:
    add_massifs_to_map(gdf_massifs, colonne_id_massif)

folium.LayerControl().add_to(m)

# Affichage de la carte dans Streamlit
map_output = st_folium(m, height=500, width='100%')

# Récupérer l'ID du massif sélectionné depuis l'état de la session
clicked_massif_id = map_output.last_object_clicked
selected_massif_id = st.session_state.get("selected_massif_id")

st.subheader("Graphique de la Végétation par Massif")

if selected_massif_id:
    st.info(f"Massif sélectionné (ID): {selected_massif_id}")
    # Filtrer les données de végétation pour le massif sélectionné
    vegetation_massif = gdf_vegetation[gdf_vegetation[colonne_lien_vegetation_massif] == selected_massif_id]

    if not vegetation_massif.empty:
        # Identifier la colonne contenant les types de végétation (la "classe")
        colonne_type_vegetation = 'type_vegetation'  # Remplacez par le nom réel de la colonne
        if colonne_type_vegetation in vegetation_massif.columns:
            # Calculer la fréquence des différents types de végétation
            vegetation_counts = vegetation_massif[colonne_type_vegetation].value_counts().sort_values(ascending=False)

            # Créer un graphique à barres
            fig, ax = plt.subplots()
            vegetation_counts.plot(kind='bar', ax=ax)
            ax.set_title(f"Répartition de la Végétation (Massif ID: {selected_massif_id})")
            ax.set_xlabel("Type de Végétation")
            ax.set_ylabel("Nombre de Zones")
            st.pyplot(fig)
        else:
            st.warning(f"La colonne '{colonne_type_vegetation}' n'a pas été trouvée dans les données de végétation.")
    else:
        st.warning(f"Aucune donnée de végétation trouvée pour le massif avec l'ID: {selected_massif_id}")
else:
    st.info("Cliquez sur un massif de la carte pour afficher le graphique de sa végétation.")
