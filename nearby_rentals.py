import shutil
import tempfile
import pandas
import os
import geopandas
from parcels.parcel_data import ParcelData
import time
COLUMNS = ParcelData.COLUMNS
def geo_to_zip(gdf, name, zip_path):
    '''
    Save a GeoDataFrame to a zip'd shape file with sidecar files
    '''
    with tempfile.TemporaryDirectory() as tmp_dir:
      gdf.to_file(f"{tmp_dir}/{name}.shp")
      shutil.make_archive(zip_path, 'zip', tmp_dir)



precincts = geopandas.read_file(f'data/raw/shp_bdry_votingdistricts.zip')
precincts = precincts[precincts.COUNTYNAME.isin (['Hennepin'])] #(['Anoka', 'Carver', 'Dakota', 'Hennepin','Ramsey', 'Scott', 'Washington'])]
print("Precincts", precincts.geometry, sep="\n")

parcels = geopandas.read_file(f'data/gen/clean_grouped_rental_parcels.zip')[[COLUMNS.keyCol,'geometry', COLUMNS.ADDRESS, COLUMNS.NAMES, COLUMNS.NUM_UNITS, COLUMNS.PORT_ID, COLUMNS.PORT_SZ, COLUMNS.LAT, COLUMNS.LON]]
parcels = parcels.to_crs(precincts.crs)
parcels['centroid'] = parcels.geometry.centroid
parcels.set_geometry('centroid')
joined = geopandas.sjoin(parcels.reset_index(),precincts[['geometry', 'VTDID', 'PCTNAME','PCTCODE']],'inner')
joined.set_geometry('geometry')
joined.drop(columns=['centroid'], inplace=True)

print('Parcels joined with precinct',joined, sep="\n")
print('Un-assigned parcels',joined[joined.PCTNAME.isna()][[COLUMNS.ADDRESS, COLUMNS.LAT, COLUMNS.LON]], sep="\n")

count_assigned = joined.groupby([COLUMNS.keyCol]).size().reset_index(name='counts')
poorly_assigned = count_assigned[count_assigned.counts != 1]
print('Poorly assigned parcels',poorly_assigned, sep="\n")

count_pct_port = joined.groupby(['PCTCODE', 'PCTNAME',COLUMNS.PORT_ID]).size().reset_index(name='counts')
print("Count By Precinct and Portfolio",count_pct_port, sep="\n")

count_pct = joined.groupby(['PCTCODE']).size().reset_index(name='total')
print("Count By Precinct",count_pct, sep="\n")

count_pct_port = count_pct_port.merge(count_pct, left_on='PCTCODE', right_on='PCTCODE', how='left' )
print("Count By Precinct and Portfolio",count_pct_port, sep="\n")

count_pct_port['share'] = count_pct_port['counts'] / count_pct_port['total']
print("High Share Portfolios",count_pct_port[(count_pct_port.share > 0.2) & (count_pct_port.total > 5)] , sep="\n")

parcels_with_market_share =  joined.merge(count_pct_port, left_on=[COLUMNS.PORT_ID,'PCTCODE'], right_on=[COLUMNS.PORT_ID, 'PCTCODE'], how='left')

print("Parcels With Market Share",parcels_with_market_share, sep="\n")

pandas.set_option("display.max_rows", None, "display.max_columns", None)
print("Havenbrook Portfolios",count_pct_port[(count_pct_port[COLUMNS.PORT_ID] == 42543)].sort_values(by='PCTNAME') , sep="\n")
pandas.set_option("display.max_rows", 5, "display.max_columns", 10)

geo_to_zip(parcels_with_market_share, 'parcels_with_market_share', 'parcels_with_market_share')
#parcels_with_market_share.to_file('parcels_with_market_share.shp')