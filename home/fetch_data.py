
import shutil

import urllib.request
'''
Fetch data from external sources
'''

def fetch_metrogis():
  url = 'https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_state_metrogis/plan_regional_parcels/shp_plan_regional_parcels.zip'
  print('Fetching from', url)
  with urllib.request.urlopen(url) as response:
    shutil.copyfileobj(response, 'data/raw/metrogis_parcels.zip')
    print('Fetched into','data/raw/metrogis_parcels.zip')

def fetch_mpls_violations():
  pass


if __name__ == "__main__":
  fetch_metrogis()
