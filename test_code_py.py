import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import fiona

# --- Configuration de la page Streamlit ---
st.set_page_config(layout="wide")
st.title("Dashboard de la Végétation des Massifs des Bouches-du-Rhône")
st.markdown("Visualisation interactive de la végétation à partir de données Shapefile hébergées sur GitHub.")

# --- Sidebar pour les instructions ---
with st.sidebar:
    st.header("Instructions")
    st.markdown("1. Les fichiers des massifs et de la végétation sont lus directement depuis les fichiers `.shp` (et leurs accompagnements) dans les dossiers du dépôt.")
    st.markdown("2. Assurez-vous que les chemins relatifs vers vos fichiers sont corrects.")
    st.markdown("3. Le fichier des massifs doit contenir une colonne d'identification unique (ex: 'id_massif', 'nom_massif').")
    st.markdown("4. Le fichier de végétation doit contenir une colonne liant la végétation au massif ('nom_maf') et une colonne de type de végétation ('NATURE').")
    st.markdown("5. Sélectionnez un massif sur la carte pour afficher les types de végétation distincts.")

# --- Fonction pour charger les données ---
@st.cache_data
def load_data(shp_massifs, dbf_massifs, shx_massifs, prj_massifs, shp_vegetation, dbf_vegetation, shx_vegetation, prj_vegetation):
    try:
        gdf_massifs = gpd.read_file(shp_massifs, dbf=dbf_massifs, shx=shx_massifs, prj=prj_massifs)
        gdf_vegetation = gpd.read_file(shp_vegetation, dbf=dbf_vegetation, shx=shx_vegetation, prj=prj_vegetation)
        return gdf_massifs, gdf_vegetation
    except fiona.errors.DriverError as e:
        st.error(f"Erreur de pilote Fiona: {e}")
        return None, None
    except Exception as e:
        st.error(f"Erreur inattendue lors du chargement des données: {e}")
        return None, None

st.subheader("DEBUG - Vérification du chargement des données")
st.write("gdf_massifs:")
st.write(gdf_massifs)
st.write("gdf_vegetation:")
st.write(gdf_vegetation)

# --- Chemins des fichiers ---
path_massifs_shp = "massifs_13_mrs/massifs_13_mrs.shp"
path_massifs_dbf = "massifs_13_mrs/massifs_13_mrs.dbf"
path_massifs_shx = "massifs_13_mrs/massifs_13_mrs.shx"
path_massifs_prj = "massifs_13_mrs/massifs_13_mrs.prj"

path_vegetation_shp = "veg_massifs_mrs/veg_massifs_mrs.shp"
path_vegetation_dbf = "veg_massifs_mrs/veg_massifs_mrs.dbf"
path_vegetation_shx = "veg_massifs_mrs/veg_massifs_mrs.shx"
path_vegetation_prj = "veg_massifs_mrs/veg_massifs_mrs.prj"

# --- Chargement des données ---
gdf_massifs, gdf_vegetation = load_data(path_massifs_shp, path_massifs_dbf, path_massifs_shx, path_massifs_prj,
                                       path_vegetation_shp, path_vegetation_dbf, path_vegetation_shx, path_vegetation_prj)

# --- Vérification du chargement des données ---
if gdf_massifs is None or gdf_vegetation is None:
    st.stop()

# --- Noms des colonnes ---
colonne_id_massif = 'nom_maf'
colonne_nom_massif = 'nom_maf'
colonne_lien_vegetation_massif = 'nom_maf'
colonne_type_vegetation = 'NATURE'

# --- Création de la mise en page en colonnes ---
col_map, col_info = st.columns([1, 1])

with col_map:
    st.subheader("Carte Interactive des Massifs")
    m = folium.Map(location=[43.5, 5.5], zoom_start=9)
    selected_massif_id = st.session_state.get("selected_massif_id")
    selected_massif_nom = st.session_state.get("selected_massif_nom")

    def add_massifs_to_map(gdf, id_col, nom_col=None):
        tooltip_fields = [nom_col] if nom_col and nom_col in gdf.columns else [id_col]
        tooltip_aliases = ['Massif:'] if nom_col and nom_col in gdf.columns else ['ID:']
        tooltip = folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)

        folium.GeoJson(
            gdf,
            name="Massifs",
            style_function=lambda x: {'fillColor': 'lightblue', 'color': 'black', 'weight': 1, 'fillOpacity': 0.5},
            tooltip=tooltip,
            highlight_function=lambda x: {'fillColor': 'blue', 'color': 'black', 'weight': 3, 'fillOpacity': 0.7},
            # Ajouter un gestionnaire d'événements de clic pour stocker l'ID et le nom du massif sélectionné
            on_click="function(feature) { L.setOptions({fillColor: 'red'}); sessionStorage.setItem('selected_massif_id', feature.properties." + id_col + "); sessionStorage.setItem('selected_massif_nom', feature.properties." + (nom_col if nom_col and nom_col in gdf.columns else id_col) + "); }"
        ).add_to(m)

    if gdf_massifs is not None:
        add_massifs_to_map(gdf_massifs, colonne_id_massif, colonne_nom_massif)

    folium.LayerControl().add_to(m)
    st_folium(m, height=500, width='100%')

with col_info:
    st.subheader("Types de Végétation par Massif")
    selected_massif_id = st.session_state.get("selected_massif_id")
    selected_massif_nom = st.session_state.get("selected_massif_nom")

    if selected_massif_id:
        st.write(f"**Massif sélectionné:** {selected_massif_nom if selected_massif_nom else selected_massif_id}")
        vegetation_massif = gdf_vegetation[gdf_vegetation[colonne_lien_vegetation_massif] == selected_massif_id]

        if not vegetation_massif.empty:
            distinct_vegetation_types = vegetation_massif[colonne_type_vegetation].unique()
            if len(distinct_vegetation_types) > 0:
                st.write("**Types de végétation présents :**")
                for veg_type in distinct_vegetation_types:
                    st.write(f"- {veg_type}")
            else:
                st.write("Aucun type de végétation trouvé pour ce massif.")
        else:
            st.info("Aucune donnée de végétation trouvée pour ce massif.")
    else:
        st.info("Cliquez sur un massif de la carte pour afficher les types de végétation distincts.")

st.write("Noms des colonnes de gdf_massifs:", gdf_massifs.columns if gdf_massifs is not None else None)
st.write("Noms des colonnes de gdf_vegetation:", gdf_vegetation.columns if gdf_vegetation is not None else None)
