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
        NAMES = 'NAMES'
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
            self._allPortfolios = None
            self._parcels = None
            self._tags = None

        @property
        def parcels(self):
            if self._parcels is None:
                self._parcels = self.getParcels()
            return self._parcels

        def getParcels(self):
            print('** Loading parcels **')
            tic = time.perf_counter()
            cwd = os.getcwd()
            adls.download_file('clean_grouped_rental_parcels.zip')
            parcels = geopandas.read_file(f'data/gen/clean_grouped_rental_parcels.zip')
            toc = time.perf_counter()
            print(f"Loaded parcels in {toc - tic:0.4f} seconds")
            return parcels.set_index(ParcelData.COLUMNS.keyCol)

        @property
        def tags(self):
            if self._tags is None:
                self._tags = self.getTags()
            return self._tags

        def getTags(self):
            print('** Loading tags **')
            tic = time.perf_counter()
            adls.download_file('tags.csv')
            tags = pd.read_csv('data/gen/tags.csv', index_col=0,
                                   low_memory=False)
            toc = time.perf_counter()
            print(f"Loaded tags in {toc - tic:0.4f} seconds")
            return tags

        @property
        def allPortfolios(self):
            if self._allPortfolios is None:
                self._allPortfolios = self.getAllPortfolios()
            return self._allPortfolios

        def getAllPortfolios(self):
            tic = time.perf_counter()
            portfolios = self.parcels.groupby(ParcelData.COLUMNS.PORT_ID)[[
                ParcelData.COLUMNS.NAMES,  ParcelData.COLUMNS.PORT_SZ]].agg({
                    ParcelData.COLUMNS.PORT_SZ: min,
                    ParcelData.COLUMNS.NAMES: lambda s: '; '.join(list(set(s.dropna())))
                })
            portfolios = portfolios.reset_index().sort_values(
                by= ParcelData.COLUMNS.PORT_SZ, ascending=False)
            allPortfolios = portfolios
            print(f"All Portfolios\n{allPortfolios}")
            toc = time.perf_counter()
            print(f"Loaded all portfolios in {toc - tic:0.4f} seconds")
            return allPortfolios


if __name__ == "__main__":
    parcels = ParcelData().parcels
    print(parcels.head())
    portfolios = ParcelData().allPortfolios
    print(portfolios.head())