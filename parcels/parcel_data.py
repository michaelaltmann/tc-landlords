import os
import time
import pandas as pd
import numpy as np
import geopandas
import util.adls as adls
###
# Use singleton and lazy property patterns
# to provide efficient access to rental license data
###


class ParcelData:
    DOWNLOAD = True
    singleton = None
    class COLUMNS((object)):
        keyCol = 'GLOBAL_ID'
        geometry = 'geometry'
        PID = 'PID'
        ADDRESS = 'ADDRESS'
        ABBREV_ADD = 'ABBREV_ADD'
        LAT = 'LAT'
        LON = 'LON'
        NUM_UNITS = 'NUM_UNITS'
        SALE_DATE = 'SALE_DATE'
        NAMES = 'NAMES'  #all names tagged to this parcel
        PORTFOLIO_NAMES = 'PORTFOLIO_NAMES' # all names tagged to any parcel in the same portfolio
        PORT_ID = 'PORT_ID'
        PORT_SZ = 'PORT_SZ'
        LCNS_APPL = 'LCNS_APPL'
    

    def __init__(self):
        if not ParcelData.singleton:
            ParcelData.singleton = ParcelData.__ParcelData()

    def __getattr__(self, name):
        return getattr(self.singleton, name)

    class __ParcelData:
        def __init__(self):
            self._portfolios = None
            self._parcels = None
            self._tags = None

        @property
        def parcels(self):
            """
            Dataframe indexed by GlobalId with many intrinsic attributes of the parcel
            """
            if self._parcels is None:
                self._parcels = self.getParcels()
            return self._parcels

        def getParcels(self):
            print('** Loading parcels **')
            tic = time.perf_counter()
            cwd = os.getcwd()
# Loading a shape file is an order of magnitude slower that csv.
# We can live with LAT, LON and no geometry
#            adls.download_file('clean_grouped_rental_parcels.zip')
#            parcels = geopandas.read_file(f'data/gen/clean_grouped_rental_parcels.zip')
 
            if ParcelData.DOWNLOAD:
                 adls.download_file('clean_grouped_rental_parcels.csv')
            parcels = pd.read_csv(f'data/gen/clean_grouped_rental_parcels.csv', index_col="GLOBAL_ID",
                                   low_memory=False,dtype={'phone':np.str, 'PID': np.str})
            parcels[ParcelData.COLUMNS.NAMES] = parcels[ParcelData.COLUMNS.NAMES].str.replace('~','; ', regex=False)
            toc = time.perf_counter()
            print(f"Loaded parcels in {toc - tic:0.4f} seconds")
            return parcels

        @property
        def tags(self):
            """
            Dataframe indexed by GlobalId (which may repeat) that has tags
            associated with each parcel
            """
            if self._tags is None:
                self._tags = self.getTags()
            return self._tags

        def getTags(self):
            print('** Loading tags **')
            tic = time.perf_counter()
            if ParcelData.DOWNLOAD:
                adls.download_file('tags.csv')
            tags = pd.read_csv('data/gen/tags.csv', index_col="GLOBAL_ID",
                                   low_memory=False)
            toc = time.perf_counter()
            print(f"Loaded tags in {toc - tic:0.4f} seconds")
            return tags

        @property
        def portfolios(self):
            if self._portfolios is None:
                self._portfolios = self.getPortfolios()
            return self._portfolios



        def getPortfolios(self):
            print("** Loading portfolios **")
            tic = time.perf_counter()
            if ParcelData.DOWNLOAD:
                adls.download_file('portfolios.csv')
            portfolios = pd.read_csv('data/gen/portfolios.csv', index_col="PORT_ID",
                                   low_memory=False)
            portfolios[ParcelData.COLUMNS.PORTFOLIO_NAMES] = portfolios[ParcelData.COLUMNS.PORTFOLIO_NAMES].str.replace('~', '; ', regex=False)
            print(f"All Portfolios\n{portfolios}")
            toc = time.perf_counter()
            print(f"Loaded all portfolios in {toc - tic:0.4f} seconds")
            return portfolios


if __name__ == "__main__":
    parcels = ParcelData().parcels
    print(parcels.head())
    portfolios = ParcelData().portfolios
    print(portfolios.head())