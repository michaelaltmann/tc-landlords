from licenses.transform import *

if __name__ == "__main__":
    # execute only if run as a script
    df = load()
    df = clean(df)
    createGroups(df)
    print(df)
    print("Writing to licenses/clean_grouped_rental_licenses.csv")
    df.to_csv('licenses/clean_grouped_rental_licenses.csv', mode='w')
