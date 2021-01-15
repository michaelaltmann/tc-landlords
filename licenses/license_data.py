import time
import pandas as pd

###
# Use singleton and lazy property patterns
# to provide efficient access to rental license data
###


class LicenseData:
    singleton = None

    def __init__(self):
        if not LicenseData.singleton:
            LicenseData.singleton = LicenseData.__LicenseData()

    def __getattr__(self, name):
        return getattr(self.singleton, name)

    class __LicenseData:
        def __init__(self):
            self._allPortfolios = None
            self._licenses = None

        @property
        def licenses(self):
            if self._licenses is None:
                print("self._licenses is None")
                self._licenses = self.getLicenses()
            return self._licenses

        def getLicenses(self):
            print('** Loading licenses **')
            tic = time.perf_counter()
            licenses = pd.read_csv('licenses/clean_grouped_rental_licenses.csv', index_col=0,
                                   low_memory=False)
            toc = time.perf_counter()
            print(f"Loaded licenses in {toc - tic:0.4f} seconds")
            return licenses

        @property
        def allPortfolios(self):
            if self._allPortfolios is None:
                print("self._allPortfolios is None")
                self._allPortfolios = self.getAllPortfolios()
            else:
                print("self._allPortfolios is set")
            return self._allPortfolios

        def getAllPortfolios(self):
            tic = time.perf_counter()
            portfolios = self.licenses.groupby('portfolioId')[[
                'ownerName', 'applicantN', 'portfolioSize']].agg({
                    'portfolioSize': min,
                    'ownerName': lambda s: '; '.join(list(set(s.dropna()))),
                    'applicantN': lambda s: '; '.join(list(set(s.dropna()))),
                })
            portfolios = portfolios.sort_values(
                by='portfolioSize', ascending=False)
            allPortfolios = portfolios.reset_index().rename(
                columns={"ownerName": "ownerNames", "applicantN": "applicantNames"})
            print(f"AllPortfolios\n{allPortfolios}")
            toc = time.perf_counter()
            print(f"Loaded allportfolios in {toc - tic:0.4f} seconds")
            return allPortfolios
