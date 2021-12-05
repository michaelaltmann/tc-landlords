import os
from pathlib import Path
import urllib.request

'''
Manage access to ADLS data storage
'''


def download_file(file_name):
  # https://tclandlords.blob.core.windows.net/tc-landlords-data/data/gen/tags.csv
  STORAGE_ACCNT='tclandlords'
  CONTAINER='tc-landlords-data'
  remote_directory='data/gen'
  local_directory = 'data/gen'
  url=f"https://{STORAGE_ACCNT}.blob.core.windows.net/{CONTAINER}/{remote_directory}/{file_name}"
  urllib.request.urlretrieve(url, f'{local_directory}/{file_name}')
  


if __name__ == "__main__":
  download_file('clean_grouped_rental_parcels.zip')