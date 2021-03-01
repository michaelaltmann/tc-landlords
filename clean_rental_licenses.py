from numpy.lib.arraysetops import unique
import pandas as pd
import numpy as np
import re
from licenses.union_find import UnionFind
from licenses.transform import clean, cleanName, cleanAddressLine


def buildAddress(row):
    '''
    Build an address string from the pieces in a Henn county record
    THe address has directional abbreviations are NE, NW, SE, and SW
    '''
    words = []
    if isinstance(row['HOUSE_NO'], str) and len(row['HOUSE_NO'].strip()) > 0:
        words.append(row['HOUSE_NO'].strip())
    if isinstance(row['FRAC_HOUSE_NO'], str) and len(row['FRAC_HOUSE_NO'].strip()) > 0:
        words.append(row['FRAC_HOUSE_NO'].strip())
    if isinstance(row['STREET_NM'], str) and len(row['STREET_NM'].strip()) > 0:
        street = row['STREET_NM'].strip()
        street = re.sub(' N E$', ' NE', street)
        street = re.sub(' N W$', ' NW', street)
        street = re.sub(' S E$', ' SE', street)
        street = re.sub(' S W$', ' SW', street)
        words.append(street)
    if isinstance(row['CONDO_NO'], str) and len(row['CONDO_NO'].strip()) > 0:
        words.append('#' + row['CONDO_NO'].strip())
    s = " ".join(words)
    if isinstance(row['MUNIC_NM'], str) and len(row['MUNIC_NM'].strip()) > 0:
        s = s + ", " + row['MUNIC_NM'].strip()
    return s


def addLinksForAttribute(df, key, attribute, uf):
    temp = df.loc[~df[attribute].isna()]
    g = temp.groupby(attribute)[key]
    for name, group in g:
        rows = group.tolist()
        if len(rows) > 1:
            if len(rows) > 200:
                print('Popular ' + attribute, name, len(rows))
            first = rows[0]
            for other in rows[1:]:
                if (first in uf and other in uf):
                    uf.union(first, other)


def loadHennProperty():
    path = 'data/raw/Henn_Parcels.csv'
    rawHenn = pd.read_csv(path, index_col=0, dtype={'HOUSE_NO': 'str', 'FRAC_HOUSE_NO': 'str', 'CONDO_NO': 'str'},
                          low_memory=False)
    df = rawHenn
    propertyTypes = ['APARTMENT', 'RESIDENTIAL',
                     'LOW INCOME RENTAL', 'TOWNHOUSE',
                     'RESIDENTIAL-TWO UNIT',  'TRIPLEX',
                     'VACANT LAND-RESIDENTIAL',
                     'CONDOMINIUM', 'RESIDENTIAL MISCELLANEOUS',
                     'RESIDENTIAL-ZERO LOT LINE', 'RESIDENTIAL LAKE SHORE',
                     'COOPERATIVE HOUSING-MASTER',
                     'COOPERATIVE HOUSING',
                     'VACANT LAND-RURAL RESIDENTIAL',
                     'NON-PROFIT COMMUNITY ASSN', 'SEASONAL LAKESHORE RESTAURANT',
                     ]
    rowsOfInterest = df.loc[df['HMSTD_CD1'].str.match(
        'N', na=False) & df['PR_TYP_NM1'].isin(propertyTypes)]
#    rowsOfInterest = rowsOfInterest.loc[df['MUNIC_NM'].str.match('MINNEAPOLIS', na=False)]
    rowsOfInterest['address'] = rowsOfInterest.apply(
        lambda row: buildAddress(row), axis=1)
    return rowsOfInterest


def loadMplsLicense():
    path = 'data/raw/mpls_rental_licences.csv'
    df = pd.read_csv(path, index_col=False,
                     low_memory=False)
    return df


# return the first address that has a number in it
def selectAddress(addressList):
    a = next((s for s in addressList if isinstance(
        s, str) and re.match(r'\d', s)), np.nan)
    return a


def apnToStatePin(s):
    mplsPrefix = '27053-'
    if len(s) == 12:
        return mplsPrefix + '0' + s
    else:
        return mplsPrefix + s


def createGroups():
    # Load data
    global henn, licenses
    henn = loadHennProperty()
    licenses = loadMplsLicense()
    licenses = clean(licenses)
    licenses['address'] = licenses['address'] + ', MINNEAPOLIS'

    # Get all the addresses
    allAddresses = pd.concat(
        [henn[[key]], licenses[[key]]]).drop_duplicates(key)
    # initialize
    uf = UnionFind()
    for id in allAddresses[key]:
        uf.add(id)

    print(f"Begin with n_comps={uf.n_comps}")

    addLinksForAttribute(licenses, key, 'xEmail', uf)
    print(f"After linking by xEmail  n_comps={uf.n_comps}")

    addLinksForAttribute(licenses, key, 'xPhone', uf)
    print(f"After linking by xPhone  n_comps={uf.n_comps}")

    ownerNames = henn[[key, 'OWNER_NM']].rename(
        columns={'OWNER_NM': 'xName'})
    ownerNames['xName'] = ownerNames['xName'].apply(lambda s: cleanName(s))
    taxNames = henn[[key, 'TAXPAYER_NM']].rename(
        columns={'TAXPAYER_NM': 'xName'})
    taxNames['xName'] = taxNames['xName'].apply(lambda s: cleanName(s))

    names = pd.concat([ownerNames, taxNames, licenses[[key, 'xName']]
                       ], axis=0)

    addLinksForAttribute(names, key, 'xName', uf)
    print(f"After linking by xName  n_comps={uf.n_comps}")

    henn['xAddress'] = henn.apply(lambda row: cleanAddressLine(selectAddress([
        row['TAXPAYER_NM'], row['TAXPAYER_NM_1']])), axis=1)

    addresses = pd.concat([
        henn[[key, 'xAddress']], licenses[[key, 'xAddress']]
    ], axis=0)

    addLinksForAttribute(addresses, key, 'xAddress', uf)
    print(f"After linking by xAddress  n_comps={uf.n_comps}")

    print("Writing portfolio id back to the dataframe")
    allAddresses['portfolioId'] = allAddresses[key].apply(
        lambda id: uf.find(id))
    print("Writing portfolio size back to the dataframe")
    componentMapping = uf.component_mapping()
    allAddresses['portfolioSize'] = allAddresses[key].apply(
        lambda id: len(componentMapping[id]))
    print("Done creating portfolios")
    return allAddresses


if __name__ == "__main__":
    key = 'address'
    allAddresses = createGroups()
    allAddresses = allAddresses.set_index(key)
    licenses = licenses.set_index(key)
    henn = henn.set_index(key)
    # Add fields from source files
    allAddresses = allAddresses.join(licenses[['apn', 'licenseNum', 'issueDate', 'applicantN', 'ownerName']].rename(
        columns={'ownerName': 'licenseOwnerName'}), how='left')
    allAddresses = allAddresses.join(
        henn[['PID', 'OWNER_NM', 'PR_TYP_NM1', 'LAT', 'LON']], how='left')
    allAddresses = allAddresses.rename(
        columns={'LAT': 'latitude', 'LON': 'longitude'})
    allAddresses['ownerName'] = allAddresses['licenseOwnerName'].fillna(
        allAddresses['OWNER_NM']).str.strip()

    print(allAddresses)

    print("Writing to data/gen/clean_grouped_rental_licenses.csv")
    allAddresses.to_csv('data/gen/clean_grouped_rental_licenses.csv', mode='w')

    portfolios = allAddresses.groupby('portfolioId')[[
        'ownerName', 'applicantN', 'portfolioSize']].agg({
            'portfolioSize': min,
            'ownerName': lambda s: '; '.join(list(set(s.dropna()))),
            'applicantN': lambda s: '; '.join(list(set(s.dropna()))),
        })
    portfolios = portfolios.sort_values(
        by='portfolioSize', ascending=False)
    allPortfolios = portfolios.reset_index().rename(
        columns={"ownerName": "ownerNames", "applicantN": "applicantNames"})
    print(allPortfolios.head(20))
