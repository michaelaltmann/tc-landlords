import pandas as pd


class Violations:

    def load(self):
        all_files = [f"violations/ward{n}.csv" for n in range(1, 14)]
        print(f"Loading {all_files}")
        # Address	Tier	Case Number	Violation Code	Violation Code Description	Violation Grouping	Violation Resolved?	Violator Name   	Violator Name	Violation Date

        columns = ['address', 'tier', 'caseNumber', 'code', 'description',
                   'grouping', 'isResolved', 'filler1', 'violatorName', 'violationDateStr']
        df = pd.concat([pd.read_csv(f, delimiter="\t",
                                    header=0, names=columns,
                                    low_memory=False, encoding='utf-16') for f in all_files])
        df['violationDate'] = pd.to_datetime(
            df['violationDateStr'], format="%m/%d/%Y", errors='coerce').dt.strftime('%Y-%m-%d')
        self.violations = df
        self.countByAddress = df[['address']].groupby(
            'address').size().reset_index(name='violationCount').set_index('address')


if __name__ == "__main__":
    # execute only if run as a script
    v = Violations()
    v.load()
    print(v.violations)
    print(v.countByAddress)
