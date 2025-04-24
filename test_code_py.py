import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import fiona
import random

# --- Configuration de la page Streamlit ---
st.set_page_config(layout="wide")
st.title("Dashboard de la Végétation des Massifs des Bouches-du-Rhône")
st.markdown("Visualisation interactive de la végétation à partir de données Shapefile hébergées sur GitHub.")

# --- Sidebar pour les instructions ---
with st.sidebar:
    st.header("Options d'affichage")
    option_affichage = st.radio(
        "Afficher :",
        ("Massifs", "Végétation")
    )
    st.header("Instructions")
    st.markdown("1. Les fichiers des massifs et de la végétation sont lus directement depuis les fichiers `.shp` (et leurs accompagnements) dans les dossiers du dépôt.")
    st.markdown("2. Assurez-vous que les chemins relatifs vers vos fichiers sont corrects.")
    st.markdown("3. Le fichier des massifs doit contenir une colonne d'identification unique (ex: 'id_massif', 'nom_massif').")
    st.markdown("4. Le fichier de végétation doit contenir une colonne liant la végétation au massif ('nom_maf') et une colonne de type de végétation ('NATURE').")
    st.markdown("5. Sélectionnez un élément sur la carte pour afficher des informations.")

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

# --- Création de la carte interactive avec Folium ---
col_map, col_info = st.columns([1, 1])

with col_map:
    st.subheader("Carte Interactive")
    m = folium.Map(location=[43.5, 5.5], zoom_start=9)
    selected_feature_id = st.session_state.get("selected_feature_id")
    selected_feature_nom = st.session_state.get("selected_feature_nom")
    vegetation_colors = {} # Dictionnaire pour stocker les couleurs par type de végétation

    def get_vegetation_color(feature):
        vegetation_type = feature['properties'][colonne_type_vegetation]
        if vegetation_type not in vegetation_colors:
            vegetation_colors[vegetation_type] = "#{:06x}".format(random.randint(0, 0xFFFFFF)) # Générer une couleur aléatoire
        return {'fillColor': vegetation_colors[vegetation_type], 'color': 'darkgreen', 'weight': 0.5, 'fillOpacity': 0.7}

    def add_to_map(gdf, name, id_col, nom_col=None, style_function=None, highlight_function=None, on_click_function=None):
        tooltip_fields = [nom_col] if nom_col and nom_col in gdf.columns else [id_col]
        tooltip_aliases = [name[:-1] + ':'] if nom_col and nom_col in gdf.columns else ['ID:']
        tooltip = folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases)

        folium.GeoJson(
            gdf,
            name=name,
            style_function=style_function,
            highlight_function=highlight_function,
            tooltip=tooltip,
            on_click=on_click_function
        ).add_to(m)

    massif_style = lambda x: {'fillColor': 'lightblue', 'color': 'black', 'weight': 1, 'fillOpacity': 0.5}
    massif_highlight = lambda x: {'fillColor': 'blue', 'color': 'black', 'weight': 3, 'fillOpacity': 0.7}
    massif_onclick = "function(feature) { L.setOptions({fillColor: 'red'}); sessionStorage.setItem('selected_feature_id', feature.properties." + colonne_id_massif + "); sessionStorage.setItem('selected_feature_nom', feature.properties." + colonne_nom_massif + "); }"

    vegetation_highlight = lambda x: {'fillColor': 'green', 'color': 'darkgreen', 'weight': 1, 'fillOpacity': 0.9}
    vegetation_onclick = "function(feature) { L.setOptions({fillColor: 'red'}); sessionStorage.setItem('selected_feature_id', feature.properties." + colonne_type_vegetation + "); sessionStorage.setItem('selected_feature_nom', feature.properties." + colonne_type_vegetation + "); }" # Utiliser le type de végétation comme ID/nom pour l'instant


    if option_affichage == "Massifs" and gdf_massifs is not None:
        add_to_map(gdf_massifs, "Massifs", colonne_id_massif, colonne_nom_massif, massif_style, massif_highlight, massif_onclick)
    elif option_affichage == "Végétation" and gdf_vegetation is not None:
        add_to_map(gdf_vegetation, "Végétation", colonne_type_vegetation, colonne_type_vegetation, get_vegetation_color, vegetation_highlight, vegetation_onclick)
        # Ajouter la légende
        legend_html = """
             <div style="position: fixed;
                         bottom: 50px; left: 50px; width: 150px; height: 200px;
                         border:2px solid grey; z-index:9999; font-size:14px; background-color:white; opacity:0.9;">
               &nbsp; <b>Légende</b> <br>
             </div>
             """
        for veg_type, color in vegetation_colors.items():
            legend_html += f"""
                           &nbsp; <i style="background:{color}; border-radius:50%; width: 10px; height: 10px; float: left; margin-right: 5px;"></i> {veg_type} <br>
                           """
        m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl().add_to(m)
    st_folium(m, height=500, width='100%')

with col_info:
    st.subheader("Informations")
    if selected_feature_id and option_affichage == "Massifs":
        st.write(f"**Massif sélectionné:** {selected_feature_nom if selected_feature_nom else selected_feature_id}")
        vegetation_massif = gdf_vegetation[gdf_vegetation[colonne_lien_vegetation_massif] == selected_feature_id]
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
    elif selected_feature_id and option_affichage == "Végétation":
        st.write(f"**Type de végétation sélectionné:** {selected_feature_nom}")
        # Tu peux ajouter ici des informations spécifiques au type de végétation si nécessaire
    else:
        st.info("Sélectionnez un élément sur la carte pour afficher des informations.")

st.write("Noms des colonnes de gdf_massifs:", gdf_massifs.columns if gdf_massifs is not None else None)
st.write("Noms des colonnes de gdf_vegetation:", gdf_vegetation.columns if gdf_vegetation is not None else None)

st.subheader("DEBUG - Vérification du chargement des données")
st.write("gdf_massifs:")
st.write(gdf_massifs.head() if gdf_massifs is not None else None)
st.write("gdf_vegetation:")
st.write(gdf_vegetation.head() if gdf_vegetation is not None else None)
