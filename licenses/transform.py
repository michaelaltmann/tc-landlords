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
        s = re.sub(r'[,\.;\-]', ' ', s)
        s = re.sub(r'( |,)+(l\.?){1,3}c$', '', s)
        s = re.sub(r'llp$', '', s)
        s = re.sub(r'ltd$', '', s)
        s = re.sub(r'inc$', '', s)
        s = re.sub(r'\s+', ' ', s)
        return s
    else:
        return s


def cleanEmail(s):
    if isinstance(s, str):
        return s.replace('\n', ' ').replace(' ', '').replace('\t', '').lower()
    else:
        return s


def load():
    df = pd.read_csv('licenses/licences-raw.csv', index_col=0,
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

    # create new columns, using applicant data when owner data is missing
    df['xPhone'] = df['ownerPhone'].fillna(df['applicantP']).str.replace(
        r"[\(\)\-\.\s]", "", regex=True)
    df['xEmail'] = df['ownerEmail'].fillna(df['applicantE']).apply(cleanEmail)
    df['xName'] = df['ownerName'].fillna(df['applicantN']).apply(cleanName)
    df['xAddress'] = df.apply(lambda row: cleanAddressPair(
        row['ownerAddre'], row['ownerAdd_1']), axis=1)
    return df


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

    print("Writing portfolio id back to the dataframe")
    df['portfolioId'] = df['OBJECTID'].apply(lambda id: uf.find(id))
    print("Writing portfolio size back to the dataframe")
    componentMapping = uf.component_mapping()
    df['portfolioSize'] = df['OBJECTID'].apply(
        lambda id: len(componentMapping[id]))
    print("Done creating portfolios")


def addLinksForAttribute(df, uf, attribute):
    g = df.groupby(attribute)['OBJECTID']
    for name, group in g:
        rows = group.tolist()
        if len(rows) > 1:
            first = rows[0]
            for other in rows[1:]:
                uf.union(first, other)
