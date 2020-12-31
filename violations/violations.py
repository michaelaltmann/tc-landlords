import pandas as pd


class Violations:

    def load(self):
        all_files = [f"violations/ward{n}.csv" for n in range(1, 14)]
        print(f"Loading {all_files}")
        # Address	Tier	Case Number	Violation Code	Violation Code Description	Violation Grouping	Violation Resolved?	Violator Name   	Violator Name	Violation Date

        columns = ['address', 'tier', 'caseNumber', 'code', 'description',
                   'grouping', 'isResolved', 'filler1', 'violatorName', 'violationDate']
        df = pd.concat([pd.read_csv(f, delimiter="\t",
                                    header=0, names=columns,
                                    low_memory=False, encoding='utf-16') for f in all_files])
        self.violations = df


if __name__ == "__main__":
    # execute only if run as a script
    v = Violations()
    v.load()
    df = v.violations
    print(df)
