import pandas as pd
import time

from parcels.parcel_data import ParcelData
import util.adls as adls
COLUMNS = ParcelData.COLUMNS

class ViolationData:
    singleton = None

    def __init__(self):
        if not ViolationData.singleton:
            ViolationData.singleton = ViolationData.__ViolationData()

    def __getattr__(self, name):
        return getattr(self.singleton, name)

    class __ViolationData:
        def __init__(self):
            self._violations = None
            self._countByAddress = None

        @property
        def violations(self):
            if self._violations is None:
                self._violations = self.getViolations()
            return self._violations

        @property
        def countByAddress(self):
            if self._countByAddress is None:
                self._countByAddress = self.getCountByAddress()
            return self._countByAddress


        def getViolations(self):
            print('** Loading violations **')
            adls.download_file('violations.csv')
            df = pd.read_csv('data/gen/violations.csv')
            return df

    
        def getCountByAddress(self):
            tic = time.perf_counter()
            countByAddress = self.violations[[COLUMNS.ADDRESS]].groupby(
                COLUMNS.ADDRESS).size().reset_index(name='violationCount').set_index(COLUMNS.ADDRESS)
            toc = time.perf_counter()
            print(f"Counted violations by address in {toc - tic:0.4f} seconds")
            return countByAddress

