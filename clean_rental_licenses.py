import pandas as pd
import numpy as np
import re
from licenses.union_find import UnionFind
from licenses.transform import clean


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
    df = df.loc[df['HMSTD_CD1'].str.match(
        'N', na=False) & df['PR_TYP_NM1'].isin(propertyTypes)]
    df = df.loc[df['MUNIC_NM'].str.match('MINNEAPOLIS', na=False)]
    df['address'] = df.apply(lambda row: buildAddress(row), axis=1)
    return df


def loadMplsLicense():
    path = 'data/raw/mpls_rental_licences.csv'
    df = pd.read_csv(path, index_col=False,
                     low_memory=False)
    return df


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
    key = 'address'
# Load data
    henn = loadHennProperty()
    licenses = loadMplsLicense()
    licenses = clean(licenses)

    # initialize
    uf = UnionFind()
    for id in licenses[key]:
        uf.add(id)

    print(f"Begin with n_comps={uf.n_comps}")

    addLinksForAttribute(licenses, key, 'xEmail', uf)
    print(f"After linking by xEmail  n_comps={uf.n_comps}")

    addLinksForAttribute(licenses, key, 'xPhone', uf)
    print(f"After linking by xPhone  n_comps={uf.n_comps}")

    ownerNames = henn[[key, 'OWNER_NM']].rename(columns={'OWNER_NM': 'xName'})
    taxNames = henn[[key, 'TAXPAYER_NM']].rename(
        columns={'TAXPAYER_NM': 'xName'})

    names = pd.concat([ownerNames, taxNames, licenses[['address', 'xName']]
                       ], axis=0)

    addLinksForAttribute(names, key, 'xName', uf)
    print(f"After linking by xName  n_comps={uf.n_comps}")

    henn['zTaxAddress'] = henn.apply(lambda row: selectAddress([
        row['TAXPAYER_NM'], row['TAXPAYER_NM_1']]), axis=1)

    addresses = pd.concat([
        henn[[key, 'zTaxAddress']].rename(
            columns={'zTaxAddress': 'xAddress'}), licenses[[key, 'xAddress']]
    ], axis=0)

    addLinksForAttribute(addresses, key, 'xAddress', uf)
    print(f"After linking by xAddress  n_comps={uf.n_comps}")

    print("Writing portfolio id back to the dataframe")
    licenses['portfolioId'] = licenses[key].apply(lambda id: uf.find(id))
    print("Writing portfolio size back to the dataframe")
    componentMapping = uf.component_mapping()
    licenses['portfolioSize'] = licenses[key].apply(
        lambda id: len(componentMapping[id]))
    print("Done creating portfolios")
    return licenses


if __name__ == "__main__":
    # execute only if run as a script
    licenses = createGroups()
    print(licenses)

    print("Writing to data/gen/clean_grouped_rental_licenses.csv")
    licenses.to_csv('data/gen/clean_grouped_rental_licenses.csv', mode='w')

    portfolios = licenses.groupby('portfolioId')[[
        'ownerName', 'applicantN', 'portfolioSize']].agg({
            'portfolioSize': min,
            'ownerName': lambda s: '; '.join(list(set(s.dropna()))),
            'applicantN': lambda s: '; '.join(list(set(s.dropna()))),
        })
    portfolios = portfolios.sort_values(
        by='portfolioSize', ascending=False)
    allPortfolios = portfolios.reset_index().rename(
        columns={"OWNER_NAME": "ownerNames", "applicantN": "applicantNames"})
    print(allPortfolios.head(20))
