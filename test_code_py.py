import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# --- Configuration de la page Streamlit ---
st.set_page_config(layout="wide")
st.title("Dashboard de la Végétation des Massifs des Bouches-du-Rhône")
st.markdown("Visualisation interactive de la végétation et répartition par massif.")

# --- Sidebar pour les instructions et sélection ---
with st.sidebar:
    st.header("Options")
    option_affichage = st.radio("Afficher sur la carte :", ("Massifs", "Végétation"))
    st.markdown("Choisissez un massif pour voir sa répartition de végétation.")

# --- Chargement des données ---
@st.cache_data

def load_data():
    gdf_massifs = gpd.read_file("massifs_13_mrs/massifs_13_mrs.shp")
    gdf_vegetation = gpd.read_file("veg_massifs_mrs/veg_massifs_mrs.shp")
    return gdf_massifs, gdf_vegetation

gdf_massifs, gdf_vegetation = load_data()

# --- Colonnes de lien ---
colonne_lien_vegetation_massif = "nom_maf"
colonne_type_vegetation = "NATURE"
colonne_surface = "surface_ve"

# --- Couleurs pour chaque type de végétation ---
types_vegetation = gdf_vegetation[colonne_type_vegetation].unique()
palette = plt.cm.get_cmap("tab20", len(types_vegetation))
color_map = {veg: f"#{''.join([format(int(255*c), '02x') for c in palette(i)[:3]])}" for i, veg in enumerate(types_vegetation)}

# --- Carte Folium ---
m = folium.Map(location=[43.5, 5.5], zoom_start=9)

if option_affichage == "Massifs":
    folium.GeoJson(
        gdf_massifs,
        name="Massifs",
        tooltip=folium.GeoJsonTooltip(fields=["nom_maf"], aliases=["Massif:"])
    ).add_to(m)
else:
    def style_function(feature):
        veg_type = feature['properties'][colonne_type_vegetation]
        return {
            'fillColor': color_map.get(veg_type, 'gray'),
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.6
        }

    folium.GeoJson(
        gdf_vegetation,
        name="Végétation",
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(fields=[colonne_type_vegetation, colonne_lien_vegetation_massif], aliases=["Végétation:", "Massif:"])
    ).add_to(m)

    # Légende personnalisée
    legend_html = """
    <div style='position: fixed; 
                bottom: 50px; left: 50px; width: 250px; height: auto; 
                background-color: white; z-index:9999; font-size:14px; border:2px solid grey; padding: 10px;'>
        <b>Légende Végétation</b><br>
    """
    for veg, color in color_map.items():
        legend_html += f"""
            <i style='background:{color};width:18px;height:18px;float:left;margin-right:8px;opacity:0.7;border:1px solid #000'></i>
            <span style='color:black;'>{veg}</span><br>
        """
    legend_html += "</div>"
    m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, height=500, width='100%')

# --- Camembert de répartition ---
st.subheader("Répartition de la végétation par massif")
massif_selectionne = st.selectbox("Choisir un massif :", gdf_massifs["nom_maf"].unique())
data_massif = gdf_vegetation[gdf_vegetation[colonne_lien_vegetation_massif] == massif_selectionne]

if not data_massif.empty:
    repartition = data_massif.groupby(colonne_type_vegetation)[colonne_surface].sum()
    repartition_pct = 100 * repartition / repartition.sum()

    fig, ax = plt.subplots()
    ax.pie(repartition_pct, labels=repartition_pct.index, colors=[color_map.get(k, 'gray') for k in repartition_pct.index], autopct='%1.1f%%', textprops={'color': 'black'})
    ax.set_title(f"Types de végétation dans {massif_selectionne}", fontsize=14)
    st.pyplot(fig)
else:
    st.warning("Pas de données de végétation pour ce massif.")

# --- Analyse par type de végétation ---
st.subheader("Répartition d'un type de végétation dans les massifs")
veg_choisie = st.selectbox("Choisir un type de végétation :", types_vegetation)
data_type = gdf_vegetation[gdf_vegetation[colonne_type_vegetation] == veg_choisie]

if not data_type.empty:
    surface_par_massif = data_type.groupby(colonne_lien_vegetation_massif)[colonne_surface].sum()
    total_par_massif = gdf_vegetation.groupby(colonne_lien_vegetation_massif)[colonne_surface].sum()
    pourcentages = 100 * surface_par_massif / total_par_massif.loc[surface_par_massif.index]

    df_affichage = pd.DataFrame({
        "Massif": pourcentages.index,
        "% de ce type de végétation": pourcentages.values.round(2)
    })
    st.dataframe(df_affichage)
else:
    st.info("Ce type de végétation n'est présent dans aucun massif.")


