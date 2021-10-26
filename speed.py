import geopandas
import timeit
import pickle
import pandas

DEBUG=False

def read_shape():
  global gdf, df
  gdf = geopandas.read_file('data/gen/clean_grouped_rental_parcels.zip')
  if DEBUG:
    print(gdf.head())
  return gdf

def write_csv():
  global gdf, df
  df.to_csv('df.csv', mode='w')

def read_csv():
  global gdf, df
  df = pandas.read_csv('df.csv')
  if DEBUG:
    print(df.head())

def write_gdf_pickle():
  global gdf, df
  with open('gdf.pickle', 'wb') as handle:
    pickle.dump(gdf, handle, protocol=pickle.HIGHEST_PROTOCOL)

def read_gdf_pickle():
  global gdf, df
  with open('gdf.pickle', 'rb') as handle:
    gdf = pickle.load(handle)
  if DEBUG:
    print(gdf.head())

if __name__  == "__main__":
  loops = 4 
  print("read_shape",timeit.timeit(read_shape, number=loops))
  df = gdf.drop(columns=['geometry'])
  print("write_csv",timeit.timeit(write_csv, number=loops))
  print("read_csv",timeit.timeit(read_csv, number=loops))

  print("write_gdf_pickle",timeit.timeit(write_gdf_pickle, number=loops))
  print("read_gdf_pickle",timeit.timeit(read_gdf_pickle, number=loops))
