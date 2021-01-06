import pandas as pd
import time


class Violations:
    singleton = None

    def __init__(self):
        if not Violations.singleton:
            Violations.singleton = Violations.__Violations()

    def __getattr__(self, name):
        return getattr(self.singleton, name)

    class __Violations:
        def __init__(self):
            self.load()

        def load(self):
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

            self.violations = df
            tic = time.perf_counter()
            self.countByAddress = df[['address']].groupby(
                'address').size().reset_index(name='violationCount').set_index('address')
            toc = time.perf_counter()
            print(f"Counted violations by address in {toc - tic:0.4f} seconds")
