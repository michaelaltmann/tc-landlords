import geopandas
import zipfile
import pandas
import tempfile
import shutil
import os
def geo_to_zip(gdf, name, zip_path):
    with tempfile.TemporaryDirectory() as tmp_dir:
      gdf.to_file(f"{tmp_dir}/{name}.shp")
      shutil.make_archive(zip_path, 'zip', tmp_dir)

df = pandas.DataFrame(
    {'City': ['Buenos Aires', 'Brasilia', 'Santiago', 'Bogota', 'Caracas'],
     'Country': ['Argentina', 'Brazil', 'Chile', 'Colombia', 'Venezuela'],
     'Latitude': [-34.58, -15.78, -33.45, 4.60, 10.48],
     'Longitude': [-58.66, -47.91, -70.66, -74.08, -66.86]})

gdf = geopandas.GeoDataFrame(
    df, geometry=geopandas.points_from_xy(df.Longitude, df.Latitude))

geo_to_zip(gdf, "foo", "mycontent")