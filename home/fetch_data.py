
import shutil

import urllib.request
'''
Fetch data from external sources
'''

def fetch_metrogis():
  '''
  Get parcel data for all seven counties 
  '''
  url = 'https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_state_metrogis/plan_regional_parcels/shp_plan_regional_parcels.zip'
  print('Fetching from', url)
  urllib.request.urlretrieve(url, 'data/raw/metrogis_parcels.zip')
  print('Fetched into','data/raw/metrogis_parcels.zip')

def fetch_mpls_licenses():
  '''
  Get Mpls rental licenses
  '''
  url = 'https://opendata.arcgis.com/api/v3/datasets/baf5f14d67704668884275686e3db867_0/downloads/data?format=csv&spatialRefId=4326'
  print('Fetching from', url)
  urllib.request.urlretrieve(url, 'data/raw/mpls_rental_licences.csv')
  print('Fetched into','data/raw/mpls_rental_licences.csv')

def fetch_mpls_violations():
  '''
  Not yet working because Tableau does not easily support download
  '''
  for ward in range(1,14):
    url = 'https://tableau.minneapolismn.gov/views/OpenDataRegulatoryServices-Violations/Introduction ...'
    print('Fetching from', url)
    urllib.urlretrieve.urlopen(url, f'data/raw/mpls_violations/ward{ward}.csv')
    print('Fetched into','data/raw/mpls_rental_licences.csv')
  

if __name__ == "__main__":
#  fetch_metrogis()
#  fetch_mpls_licenses()  
  fetch_mpls_violations()