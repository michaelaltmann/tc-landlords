from azure.storage.filedatalake import DataLakeServiceClient
import os
from pathlib import Path
import urllib.request

'''
Manage access to ADLS data storage
'''

def download_using_adls_file(file_name):
  STORAGE_ACCNT='tclandlords'
  CONTAINER='tc-landlords-data'
  remote_directory='data/gen'
  local_directory = 'data/gen'
  storage_account_key = os.environ.get('STORAGE_ACCOUNT_KEY')
  service = DataLakeServiceClient(account_url=f"https://{STORAGE_ACCNT}.dfs.core.windows.net", credential=storage_account_key)
  file_system_client = service.get_file_system_client(CONTAINER)
  file_path= f'{local_directory}/{file_name}'
  directory_client = file_system_client.get_directory_client(remote_directory)
  file_client = directory_client.get_file_client(file_name)
  Path(local_directory).mkdir(parents=True, exist_ok=True)
  local_file = open(file_path,'wb')

  download = file_client.download_file()
  downloaded_bytes = download.readall()
  print("Downloaded", len(downloaded_bytes), f"bytes from {CONTAINER} {remote_directory}/{file_name}")
  local_file.write(downloaded_bytes)
  local_file.close()

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