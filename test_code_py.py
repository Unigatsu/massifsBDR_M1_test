import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import io
import zipfile
import requests
import fiona  # Importez fiona

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

# --- Fonction pour charger les données depuis GitHub (avec tentative fiona) ---
@st.cache_data
def load_data_from_github(github_url):
    try:
        response = requests.get(github_url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            shp_file = [f for f in zf.namelist() if f.endswith(".shp")][0]
            with zf.open(shp_file) as shp:
                gdf = gpd.read_file(shp, engine='fiona')  # Spécifiez le moteur fiona
        return gdf
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de requête HTTP vers {github_url}: {e}")
        return None
    except zipfile.BadZipFile as e:
        st.error(f"Erreur lors de l'ouverture du fichier ZIP depuis {github_url}: {e}")
        return None
    except IndexError:
        st.error(f"Aucun fichier .shp trouvé dans l'archive ZIP de {github_url}")
        return None
    except fiona.errors.DriverError as e:
        st.error(f"Erreur de pilote Fiona lors de la lecture de {github_url}: {e}")
        return None
    except Exception as e:
        st.error(f"Erreur inattendue lors du chargement des données depuis {github_url}: {e}")
        return None

# --- URL de tes fichiers Shapefile zippés sur GitHub ---
# Remplacez ici par les URL réelles de vos fichiers .zip
url_massifs = "https://github.com/Unigatsu/massifsBDR_M1_test/blob/567dd868905ab7ffde26ef9594f804d445835945/massifs_13_mrs.zip?raw=true"
url_vegetation = "https://github.com/Unigatsu/massifsBDR_M1_test/blob/8b89379371c3d935c367d0ecbd070a40092c85d8/veg_massifs_mrs.zip?raw=true"

# --- Chargement des données ---
gdf_massifs = load_data_from_github(url_massifs)
gdf_vegetation = load_data_from_github(url_vegetation)

# --- Vérification du chargement des données ---
if gdf_massifs is None or gdf_vegetation is None:
    st.stop()

# --- Nom de la colonne d'identification des massifs et de la colonne de liaison dans la végétation ---
colonne_id_massif = 'ID_M1'  # Remplacez par le nom réel de la colonne dans gdf_massifs
colonne_lien_vegetation_massif = 'ID_M1'  # Remplacez par le nom réel de la colonne dans gdf_vegetation
colonne_nom_massif = 'NOM_M1' # Nom de la colonne à afficher dans le tooltip des massifs (si elle existe)

# --- Création de la carte interactive avec Folium ---
st.subheader("Carte Interactive des Massifs")
m = folium.Map(location=[43.5, 5.5], zoom_start=9)

# Fonction pour ajouter les massifs à la carte et stocker l'id sélectionné
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

# Affichage de la carte dans Streamlit
map_output = st_folium(m, height=500, width='100%')

# Récupérer l'ID et le nom du massif sélectionné depuis l'état de la session
clicked_massif_id = map_output.last_object_clicked
selected_massif_id = st.session_state.get("selected_massif_id")
selected_massif_nom = st.session_state.get("selected_massif_nom")

st.subheader("Graphique de la Végétation par Massif")

if selected_massif_id:
    massif_display_name = f" (ID: {selected_massif_id})"
    if selected_massif_nom:
        massif_display_name = f" ({selected_massif_nom})"
    st.info(f"Massif sélectionné{massif_display_name}")

    # Filtrer les données de végétation pour le massif sélectionné
    vegetation_massif = gdf_vegetation[gdf_vegetation[colonne_lien_vegetation_massif] == selected_massif_id]

    if not vegetation_massif.empty:
        # Identifier la colonne contenant les types de végétation (la "classe")
        colonne_type_vegetation = 'CODE_NIV2'  # Remplacez par le nom réel de la colonne
        if colonne_type_vegetation in vegetation_massif.columns:
            # Calculer la fréquence des différents types de végétation
            vegetation_counts = vegetation_massif[colonne_type_vegetation].value_counts().sort_values(ascending=False).head(10) # Afficher les 10 principaux types

            # Créer un graphique à barres
            fig, ax = plt.subplots(figsize=(10, 6)) # Ajuster la taille du graphique
            vegetation_counts.plot(kind='bar', ax=ax)
            ax.set_title(f"Répartition des Types de Végétation (Massif{massif_display_name})")
            ax.set_xlabel("Type de Végétation")
            ax.set_ylabel("Nombre de Zones")
            plt.xticks(rotation=45, ha='right') # Incliner les labels de l'axe x
            plt.tight_layout() # Ajuster la mise en page pour éviter le chevauchement
            st.pyplot(fig)
        else:
            st.warning(f"La colonne '{colonne_type_vegetation}' n'a pas été trouvée dans les données de végétation.")
    else:
        st.warning(f"Aucune donnée de végétation trouvée pour le massif avec l'ID: {selected_massif_id}")
else:
    st.info("Cliquez sur un massif de la carte pour afficher le graphique de sa végétation.")
