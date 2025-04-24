import geopandas as gpd
import requests
import io
import zipfile
import fiona

url_test = "https://github.com/Unigatsu/massifsBDR_M1_test/blob/567dd868905ab7ffde26ef9594f804d445835945/massifs_13_mrs.zip?raw=true"

try:
    response = requests.get(url_test, stream=True)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        shp_file = [f for f in zf.namelist() if f.endswith(".shp")][0]
        with zf.open(shp_file) as shp:
            gdf_test = gpd.read_file(shp, engine='fiona')
            print("Lecture réussie !")
            print(gdf_test.head())
except fiona.errors.DriverError as e:
    print(f"Erreur Fiona: {e}")
except Exception as e:
    print(f"Autre erreur: {e}")
