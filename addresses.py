from parcels.parcel_data import ParcelData
from violations.violation_data import ViolationData

if __name__ == "__main__":
    parcels = ParcelData().parcels
    parcels[ParcelData.COLUMNS.ADDRESS] = parcels[ParcelData.COLUMNS.ADDRESS].str.upper()
    violations = ViolationData().violations
    violations[ParcelData.COLUMNS.ADDRESS] = violations[ParcelData.COLUMNS.ADDRESS].str.upper()

    v_addresses = violations[[ParcelData.COLUMNS.ADDRESS]].drop_duplicates()
    print('Violation addresses')
    print(v_addresses.head())
    p_addresses = parcels[[ParcelData.COLUMNS.ADDRESS]]
    print('Parcel addresses')
    print(p_addresses.head())
    merged = v_addresses.merge(p_addresses, how="left", on=ParcelData.COLUMNS.ADDRESS, indicator=True)
    print('Merged')
    print(merged.head())
    missed = merged[merged['_merge']=='left_only']
    print('Violations missing parcels')
    print(missed.head())

    strings = ['38 27', '27TH AVENUE NORTHEAST', '41 LOWRY', '38 26']
    
    parcels[[ParcelData.COLUMNS.ADDRESS]].head()
    violations[[ParcelData.COLUMNS.ADDRESS]].head()
    for s in strings:
      print(f"#### Searching for {s}")
      print('Parcels')
      print(parcels[parcels[ParcelData.COLUMNS.ADDRESS].str.contains(s, case=False, regex=False)][[ParcelData.COLUMNS.ADDRESS]])
      print('Violations')
      print(violations[violations[ParcelData.COLUMNS.ADDRESS].str.contains(s, case=False, regex=False)][[ParcelData.COLUMNS.ADDRESS]].drop_duplicates())