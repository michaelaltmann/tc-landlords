import pandas as pd
import time


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
                print("self._violations is None")
                self._violations = self.getViolations()
            return self._violations

        @property
        def countByAddress(self):
            if self._countByAddress is None:
                print("self._countByAddress is None")
                self._countByAddress = self.getCountByAddress()
            return self._countByAddress

        def getViolations(self):
            all_files = [f"violations/ward{n}.csv" for n in range(1, 14)]
            print(f"Loading {all_files}")
            # Address	Tier	Case Number	Violation Code	Violation Code Description	Violation Grouping	Violation Resolved?	Violator Name   	Violator Name	Violation Date

            columns = ['address', 'tier', 'caseNumber', 'code', 'description',
                       'grouping', 'isResolved', 'filler1', 'violatorName', 'violationDateStr']
            tic = time.perf_counter()
            df = pd.concat([pd.read_csv(f, delimiter="\t",
                                        header=0, names=columns,
                                        low_memory=False, encoding='utf-16') for f in all_files])
            df['violationDate'] = pd.to_datetime(
                df['violationDateStr'], format="%m/%d/%Y", errors='coerce').dt.strftime('%Y-%m-%d')
            toc = time.perf_counter()
            print(f"Loaded violations in {toc - tic:0.4f} seconds")
            return df

        def getCountByAddress(self):
            tic = time.perf_counter()
            countByAddress = self.violations[['address']].groupby(
                'address').size().reset_index(name='violationCount').set_index('address')
            toc = time.perf_counter()
            print(f"Counted violations by address in {toc - tic:0.4f} seconds")
            return countByAddress
