import numpy
import pandas as pd
import re
from .union_find import UnionFind

street_abvs = r" ave(\Z| )| av(\Z| )| ste(\Z| )| blvd(\Z| )| st(\Z| )| drive(\Z| )| dr(\Z| )|#| ln(\Z| )| dri(\Z| )| ter(\Z| )| pl(\Z| )| street(\Z| )| ct(\Z| )| rd(\Z| )| cicle(\Z| )| road(\Z| )| lane(\Z| )| trail(\Z| )| way(\Z| )| pk(\Z| )| avenue(\Z| )| place(\Z| )| hwy(\Z| )| court(\Z| )| cir(\Z| )| pkwy(\Z| )| xing(\Z| )"

type_abbrevs  = {'avenue':'AVE', 'bend':'BND','branch':'BR', 'boulevard':'BLVD', 'circle':'CIR', 
        'cove':'CV','court':'CT', 'creek':'CRK', 'curve':'CURV', 
        'crest': 'CRST', 'crescent': 'CRES', 'crossing': 'XING', 'crossroad': 'XRD', 'dale':'DL', 'drive':'DR','extension':'EXT', 
        'expressway':'EXPY', 'freeway':'FWY', 'garden':'GDN', 'gardens':'GDNS', 'gateway':'GTWY','glen': 'GL', 'freen': 'GRN', 'grove':'GRV', 'harbor':'HBR', 'heights':'HTS', 'highway':'HWY', 
        'hill': 'HL', 'island':'IS', 
        'junction':'JCT','lake':'LK','landing':'LNDG', 'lane':'LN','loop':'LOOP', 'mall':'MALL', 'mountain':'MTN',
        'park':'PARK','parkway':'PKWY', 'pass':'PASS','path':'PATH', 'place':'PL','plaza':'PLZ','point':'PT','points':'PTS','prairie':'PR',
        'ridge':'RDG', 'road':'RD', 
        'route':'RT', 'row':'ROW', 'run': 'RUN',
        'suite': 'STE', 'square':'SQ', 'street':'ST' , 'terrace':'TERR', 'trail':'TR', 'view': 'VW', 'walk': 'WALK', 'way': 'WAY'}
direction_abbrevs = {'north':'N', 'northeast':'NE', 'east': 'E', 'southeast': 'SE', 
    'south': 'S','southwest': 'SW', 'west': 'W', 'northwest': 'NW'}
abbrev_expansions = dict()
for (key, val) in type_abbrevs.items():
    abbrev_expansions[val] = key
for (key, val) in direction_abbrevs.items():
    abbrev_expansions[val] = key


def abbreviateType(s):
    if isinstance(s,str):
        if s.lower() in type_abbrevs.keys():
            return  type_abbrevs.get(s.lower(),s).upper()
        else:
            print ("Did not abbrev type ", s)
    return s

def abbreviateDirection(s):
    if isinstance(s,str):
        if s.lower() in direction_abbrevs.keys():
            return direction_abbrevs.get(s.lower(),s).upper()
        else:
            print ("Could not abbrev direction ", s)    
    return s

def expandAbbrev( s):
    if isinstance(s,str):
        if s.upper() in abbrev_expansions.keys():
            return abbrev_expansions.get(s.upper(),s).upper()   
    return s


def expandAddress(s):
    words = s.split(' ')
    expandedWords = [expandAbbrev(word) for word in words]
    return ' '.join(expandedWords)

def shortenZipcode(s):
    match = re.match(r'^(\d{5})(\-\d*)?$', s)
    if match:
        return match.group(1)
    else:
        return s

def cleanAddressLine(s):
    if isinstance(s, str) and s:
        s = s.replace(',',' ')
        s = re.sub('\s+', ' ',s).replace('.', '')
        s = ' ' + s.strip().upper() + ' '
        s = s.replace(' S E ', ' SE ')
        s = s.replace(' S W ', ' SW ')
        s = s.replace(' N E ', ' NE ')
        s = s.replace(' N W ', ' NW ')

        # Look for addresses like 123Main that need a space inserted
        match = re.search(r"^([0-9]+)([a-z]+)", s)
        if match:
            start = match.span()[0]
            finish = match.span()[1]
            streetName = match.group(2)
            if not streetName in ['TH', 'ST', 'RD', 'ND'] and len(streetName) > 0:
                s = s[:start] + match.group(1) + \
                    " " + match.group(2) + s[finish:]
        words = s.strip().split(' ')
        words = [shortenZipcode(expandAbbrev(word)) for word in words]
        address = " ".join(words)
        return address            
    else:
        return s

def cleanAddressList(lines):
    address = " ".join([cleanAddressLine(line) for line in lines if isinstance(line,str) and line])
    return address

def cleanAddressPair(s, s2):
    s = cleanAddressLine(s)
    if isinstance(s, str) and 'pobox' in s:
        s2 = cleanAddressLine(s2)
        if s2:
            s = s + s2
    return s


def cleanName(s):
    if isinstance(s, str):
        s = s.replace('\n', ' ').lower()
        s = re.sub(r'[,\.;\-]', ' ', s) # turn punctuation into spaces
        s = re.sub(r'\s+', ' ', s) ## collapes multiple white spaces

        s = re.sub(r'( |,)+(l ?){1,3}c( |$)', '', s) # Remove LLC and its variants
        s = re.sub(r'llp$', '', s)
        s = re.sub(r'ltd$', '', s)
        s = re.sub(r'inc$', '', s)
        s  = re.sub(r'apts?( |$)', 'apartments ', s)
        s = s.strip() 
        return s
    else:
        if (not pd.isnull(s)):
            print (type(s),s)
        return s


def cleanEmail(s):
    if isinstance(s, str):
        return s.replace('\n', ' ').replace(' ', '').replace('\t', '').lower()
    else:
        return s


def cleanPhone(s):
    if isinstance(s, str):
        # remove periods and parens and dashes
        s = re.sub(r'[\(\)\-\.\s]', '', s)
        # remove extension
        s = re.sub(r'x\d*$', '', s, flags=re.IGNORECASE)
        if len(s) == 7:
            return s[:3] + '.' + s[3:]
        if len(s) == 10:
            return s[:3] + '.' + s[3:6] + '.' + s[6:]
        return s
    else:
        return s


def load():
    df = pd.read_csv('parcels/licences-raw.csv', index_col=False,
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
    df['xPhone'] = df['ownerPhone'].fillna(df['applicantP']).apply(cleanPhone)
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
