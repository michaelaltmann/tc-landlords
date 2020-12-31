import pandas as pd
import re
from .union_find import UnionFind

street_abvs = r" ave(\Z| )| av(\Z| )| ste(\Z| )| blvd(\Z| )| st(\Z| )| drive(\Z| )| dr(\Z| )|#| ln(\Z| )| dri(\Z| )| ter(\Z| )| pl(\Z| )| street(\Z| )| ct(\Z| )| rd(\Z| )| cicle(\Z| )| road(\Z| )| lane(\Z| )| trail(\Z| )| way(\Z| )| pk(\Z| )| avenue(\Z| )| place(\Z| )| hwy(\Z| )| court(\Z| )| cir(\Z| )| pkwy(\Z| )| xing(\Z| )"


def cleanAddressLine(address):
    s = address
    if isinstance(s, str):
        s = s.replace('\n', ' ').replace('.', '').lower().strip()

        # Ignore ave, street, lane, etc
        s = re.sub(street_abvs, ' ', s)

        # Look for addresses like 123Main that need a space inserted
        match = re.search(r"^([0-9]+)([a-z]+)", s)
        if match:
            start = match.span()[0]
            finish = match.span()[1]
            streetName = match.group(2)
            if not streetName in ['th', 'st', 'rd', 'nd'] and len(streetName) > 0:
                s = s[:start] + match.group(1) + \
                    " " + match.group(2) + s[finish:]
        # Condense whitespace
        s = re.sub('\s+', ' ', s)
        # print(address)
        # print(s)
        return s
    else:
        return s


def cleanAddressPair(s, s2):
    s = cleanAddressLine(s)
    if isinstance(s, str) and 'pobox' in s:
        s2 = cleanAddressLine(s2)
        if s2:
            s = s + s2
    return s


def cleanName(s):
    if isinstance(s, str):
        s = s.replace('\n', ' ').lower().strip()
        s = re.sub(r'l{1,3}c$', '', s)
        s = re.sub(r'llp$', '', s)
        s = re.sub(r'ltd$', '', s)
        s = re.sub(r'inc$', '', s)
        return s
    else:
        return s


def cleanEmail(s):
    if isinstance(s, str):
        return s.replace('\n', ' ').replace(' ', '').replace('\t', '').lower()
    else:
        return s


def load():
    df = pd.read_csv('licences-raw.csv', index_col=0,
                     low_memory=False)
    return df


def clean(df):
    '''
    :param df:
    :return:df with columns xEmail, xName and xAddress that are cleaned versions of the owner info
    '''

    # do minimal cleaning in place
    df['ownerPhone'] = df['ownerPhone'].str.replace("\n", "")
    df['ownerEmail'] = df['ownerEmail'].str.replace("\n", "")
    df['ownerName'] = df['ownerName'].str.replace("\n", "")
    df['ownerAddre'] = df['ownerAddre'].str.replace("\n", "")
    df['ownerAdd_1'] = df['ownerAdd_1'].str.replace("\n", "")

    # create new columns
    df['xPhone'] = df['ownerPhone'].str.replace("[\(\)\-\.\s]", "", regex=True)
    df['xEmail'] = df['ownerEmail'].apply(cleanEmail)
    df['xName'] = df['ownerName'].apply(cleanEmail)
    df['xAddress'] = df.apply(lambda row: cleanAddressPair(
        row['ownerAddre'], row['ownerAdd_1']), axis=1)
    return df


def key(row):
    if isinstance(row, int):
        return str(row)
    return str(row.index)


def createGroups(df):
    # initialize
    uf = UnionFind()
    for id in df['OBJECTID']:
        uf.add(id)
    print(f"Begin with n_comps={uf.n_comps}")
    addLinksForAttribute(df, uf, 'xEmail')
    print(f"After linking by xEmail  n_comps={uf.n_comps}")
    addLinksForAttribute(df, uf, 'xPhone')
    print(f"After linking by xPhone  n_comps={uf.n_comps}")
    addLinksForAttribute(df, uf, 'xName')
    print(f"After linking by xName  n_comps={uf.n_comps}")
    addLinksForAttribute(df, uf, 'xAddress')
    print(f"After linking by xAddress  n_comps={uf.n_comps}")

    df['groupId'] = df['OBJECTID'].apply(lambda id: uf.find(id))
    df['groupSize'] = df['OBJECTID'].apply(lambda id: len(uf.component(id)))


def addLinksForAttribute(df, uf, attribute):
    g = df.groupby(attribute)['OBJECTID']
    for name, group in g:
        rows = group.tolist()
        if len(rows) > 1:
            first = rows[0]
            for other in rows[1:]:
                uf.union(first, other)


if __name__ == "__main__":
    # execute only if run as a script
    df = load()
    df = clean(df)
    createGroups(df)
    print(df)
    df.to_csv('clean_grouped_rental_licenses.csv')
    manyProperties = df[df.groupSize > 5].sort_values(by='groupId')
    print(manyProperties)
