import shutil
import tempfile
import pandas as pd
import numpy as np
import re
import geopandas

from pandas.core.frame import DataFrame
from parcels.union_find import UnionFind
from parcels.transform import clean, cleanEmail, cleanName, cleanAddressLine, cleanAddressPair, cleanPhone
from parcels.parcel_data import ParcelData
import time
COLUMNS = ParcelData.COLUMNS


def asString(x):
    if isinstance(x,str): return x.strip() 
    if isinstance(x,int): return str(x) 
    return ""

def buildMetroGISAddress(row):
    '''
    Build an address string from the pieces in a MetroGIS parcel record
    '''
    words = [row['ANUMBERPRE'],row['ANUMBER'], row['ANUMBERSUF'], 
        row['ST_PRE_MOD'], row['ST_PRE_DIR'], row['ST_PRE_TYP'], row['ST_PRE_SEP'],
        row['ST_NAME'], row['ST_POS_TYP'], row['ST_POS_DIR'], row['ST_POS_MOD'],
        row['SUB_TYPE1'], row['SUB_ID1']
        ]
    words = [asString(word) for word in words]
    words = [word for word in words if len(word)>0]
    s = " ".join(words)
    if isinstance(row['POSTCOMM'], str) and len(row['POSTCOMM'].strip()) > 0:
        s = s + ", " + row['POSTCOMM'].strip() 
    return s.upper()

type_abbrevs  = {'avenue':'AVE', 'bend':'BND','branch':'BR', 'boulevard':'BLVD', 'circle':'CIR', 
        'cove':'CV','court':'CT', 'creek':'CRK', 'curve':'CURV', 
        'crest': 'CRST', 'crescent': 'CRES', 'crossing': 'XING', 'crossroad': 'XRD', 'dale':'DL', 'drive':'DR','extension':'EXT', 
        'expressway':'EXPY', 'freeway':'FWY', 'garden':'GDN', 'gardens':'GDNS', 'gateway':'GTWY','glen': 'GL', 'freen': 'GRN', 'grove':'GRV', 'harbor':'HBR', 'heights':'HTS', 'highway':'HWY', 
        'hill': 'HL', 'island':'IS', 
        'junction':'JCT','lake':'LK','landing':'LNDG', 'lane':'LN','loop':'LOOP', 'mall':'MALL', 'mountain':'MTN',
        'park':'PARK','parkway':'PKWY', 'pass':'PASS','path':'PATH', 'place':'PL','plaza':'PLZ','point':'PT','points':'PTS','prairie':'PR',
        'ridge':'RDG', 'road':'RD', 
        'route':'RT', 'row':'ROW', 'run': 'RUN',
        'square':'SQ', 'street':'ST' , 'terrace':'TERR', 'trail':'TR', 'view': 'VW', 'walk': 'WALK', 'way': 'WAY'}
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


def buildMetroGISAbbrevAddress(row):
    '''
    Build an address string with abbreviations from the pieces in a MetroGIS parcel record
    '''
    words = [row['ANUMBERPRE'],row['ANUMBER'], row['ANUMBERSUF'], 
        row['ST_PRE_MOD'], abbreviateDirection(row['ST_PRE_DIR']), row['ST_PRE_TYP'], row['ST_PRE_SEP'],
        row['ST_NAME'], abbreviateType(row['ST_POS_TYP']), abbreviateDirection(row['ST_POS_DIR']), row['ST_POS_MOD'],
        row['SUB_TYPE1'], row['SUB_ID1']
        ]
    words = [asString(word) for word in words]
    words = [word for word in words if len(word)>0]
    s = " ".join(words)
    if isinstance(row['POSTCOMM'], str) and len(row['POSTCOMM'].strip()) > 0:
        s = s + ", " + row['POSTCOMM'].strip() 
    return s.upper()


def listOfUniqueStrings(*strings):
    trimmedStrings = [s.strip() for s in strings if s and isinstance(s, str) and s.strip() and len(s.strip())>0]
    return "; ".join(list(set(trimmedStrings)))

def geo_to_zip(gdf, name, zip_path):
    '''
    Save a GeoDataFrame to a zip'd shape file with sidecar files
    '''
    with tempfile.TemporaryDirectory() as tmp_dir:
      gdf.to_file(f"{tmp_dir}/{name}.shp")
      shutil.make_archive(zip_path, 'zip', tmp_dir)

def addLinksForTags(tags, uf):
    g = tags.groupby(['tag_type', 'tag_value'])[COLUMNS.keyCol]
    for name, group in g:
        rows = group.tolist()
        if len(rows) > 1:
            if len(rows) > 200:
                print('Popular tag', name, len(rows))
            first = rows[0]
            for other in rows[1:]:
                if (first in uf and other in uf):
                    uf.union(first, other)

def loadMetroGISCountyParcels(county):
    df = geopandas.read_file( f'data/raw/metrogis_parcels.zip!Parcels{county}.shp')
    print(f"Read {len(df.index)} for {county}")
    return df


def loadMetroGISParcels():
    counties = ['Anoka', 'Carver', 'Dakota', 'Hennepin','Ramsey', 'Scott', 'Washington']
    geo_files = [ loadMetroGISCountyParcels(county) for county in counties]
    df = pd.concat(geo_files, axis=0)
    # Project to lat/lon
    df = df.to_crs('EPSG:4326')

    df = df[~df['COUNTY_PIN'].isna()]
    df = df[~df['HOMESTEAD'].str.fullmatch('Yes', case=False, na=False)]
    pattern = '(RESIDENTIAL)|(RES )|(APT)|(APARTMENT)|(CONDO)|(COOP)|(DUPLEX)|(TRIPLEX)|(TOWNHOUSE)|(RENTAL)|(MANUFACTURED)|(MH )'
    df = df[df['USECLASS1'].str.match(pattern, case=False, na=False) | df['USECLASS2'].str.match(pattern, case=False, na=False)]  
    df = df[~df['USECLASS1'].str.match('(VACANT)|(RES V)', case=False, na=False)]
    df = df[~df['ST_NAME'].str.match('(ADDRESS PENDING)|(ADDRESS UNASSIGNED)', case=False, na=False)]
    df = df[~df['COUNTY_PIN'].str.match('(PINS PENDING)|(PINS UNASSIGNED)', case=False, na=False)]
    df[COLUMNS.ABBREV_ADD] = df.apply( lambda row: buildMetroGISAbbrevAddress(row), axis=1)
    df[COLUMNS.ADDRESS] = df.apply( lambda row: buildMetroGISAddress(row), axis=1)
#    df['SALE_DATE'] = pd.to_datetime(df['SALE_DATE'],format='%Y%m', errors='coerce')
    df[COLUMNS.keyCol] = 'US-MN-' + df['STATE_PIN'].astype(str)
    return df

def loadMplsLicense():
    path = 'data/raw/mpls_rental_licences.csv'
    df = pd.read_csv(path, index_col=False,
                     low_memory=False)
    df[COLUMNS.keyCol] = 'US-MN-27053-' + df['apn'] 
    return df

def loadStPaulLicense():
    path = 'data/raw/stpaul_rental_licences.csv'
    df = pd.read_csv(path, index_col=False,
                     low_memory=False)
    return df

# return the first address that has a number in it
def selectAddress(addressList):
    a = next((s for s in addressList if isinstance(
        s, str) and re.match(r'\d', s)), np.nan)
    return a


def add_tags(tags, df, source_type, tag_type):
    df = df.copy()
    df['source_type'] = source_type
    df['tag_type'] = tag_type
    df = df.loc[df['tag_value'].notnull() ]
    df['tag_value'] = df['tag_value'].astype(str)   
    df = df.loc[~ df['tag_value'].str.isspace() ]
    print(f"Adding {len(df.index)} tags for {source_type}")
    return pd.concat([tags,df[[COLUMNS.keyCol,'tag_type','tag_value','source_type', 'source_value']]], axis=0) 

def createGroups():
    # Load data
    tc_parcels = loadMetroGISParcels()
    mpls_licenses = loadMplsLicense()
    mpls_licenses = clean(mpls_licenses)
    mpls_licenses['address'] = mpls_licenses['address'] + ', MINNEAPOLIS'

    # Get all the addresses
    allKeys = pd.concat(
        [tc_parcels[[COLUMNS.keyCol]], 
        mpls_licenses[[COLUMNS.keyCol]]]
        ).drop_duplicates(COLUMNS.keyCol)
    # initialize
    uf = UnionFind()
    for id in allKeys[COLUMNS.keyCol]:
        uf.add(id)

    print(f"Begin with n_comps={uf.n_comps}")

    tags = pd.DataFrame({COLUMNS.keyCol: pd.Series([], dtype='str'),
                   'tag_type': pd.Series([], dtype='str'),
                   'tag_value': pd.Series([], dtype='str'),
                   'source_type': pd.Series([], dtype='str'),
                   'source_value': pd.Series([], dtype='str')
                   })
    
    df = mpls_licenses[[COLUMNS.keyCol,'ownerEmail']].rename(columns={'ownerEmail':'source_value'}).copy()
    df['tag_value'] = df['source_value'].apply(cleanEmail)
    tags = add_tags(tags, df, 'Mpls ownerEmail', 'email')
    print ("Mpls license owner email")
    print (tags.tail())

    df = mpls_licenses[[COLUMNS.keyCol,'ownerPhone']].rename(columns={'ownerPhone':'source_value'}).copy()
    df['tag_value'] = df['source_value'].apply(cleanPhone)
    tags = add_tags(tags, df, 'Mpls ownerPhone', 'phone')
    print ("Mpls license owner phone")
    print (tags.tail())

    df = tc_parcels[[COLUMNS.keyCol,'OWNER_NAME']].rename(columns={'OWNER_NAME':'source_value'}).copy()
    df['tag_value'] = df['source_value'].apply(cleanName)
    tags = add_tags(tags, df, 'OWNER_NAME', 'name')
    print (tags.tail())

    df = tc_parcels[[COLUMNS.keyCol,'TAX_NAME']].rename(columns={'TAX_NAME':'source_value'}).copy()
    df['tag_value'] = df['source_value'].apply(cleanName)
    tags = add_tags(tags, df, 'TAX_NAME', 'name')
    print (tags.tail())


    df = tc_parcels[[COLUMNS.keyCol,'TAX_ADD_L1']].rename(columns={'TAX_ADD_L1':'source_value'}).copy()
    df['tag_value'] = df['source_value'].apply(cleanName)
    tags = add_tags(tags, df, 'Taxpayer address', 'address')
    print (tags.tail())

    # df = mpls_licenses[[keyCol,'xAddress', 'ownerAddre','ownerAdd_1']].rename(columns={'xAddress':'tag_value'})
    # df['source_value'] = df.apply(lambda row: f"{row['ownerAddre'] if pd.notna(row['ownerAddre']) else ''} {(' ' + row['ownerAdd_1']) if pd.notna(row['ownerAdd_1']) else ''}", axis=1)
    # tags = add_tags(tags, df, 'Mpls Taxpayer Address', 'address')
    # print ("Mpls license owner address")
    # print (tags.tail())
   
    addLinksForTags(tags, uf)

    print("Writing portfolio id back to the dataframe")
    allKeys[COLUMNS.PORT_ID] = allKeys[COLUMNS.keyCol].apply(
        lambda id: uf.find(id))
    print("Writing portfolio size back to the dataframe")
    componentMapping = uf.component_mapping()
    allKeys[COLUMNS.PORT_SZ] = allKeys[COLUMNS.keyCol].apply(
        lambda id: len(componentMapping[id]))
    print("Done creating portfolios")

    return tc_parcels, mpls_licenses, allKeys, tags

def process_parcels():
    tc_parcels, mpls_licenses, allKeys, tags = createGroups()
    tags = tags.set_index(COLUMNS.keyCol)
    allKeys = allKeys.set_index(COLUMNS.keyCol)
    mpls_licenses = mpls_licenses.set_index(COLUMNS.keyCol)
    tc_parcels = tc_parcels.set_index(COLUMNS.keyCol)
    
    # Add fields from source files

    tc_parcels = tc_parcels[['geometry', COLUMNS.ABBREV_ADD , COLUMNS.ADDRESS, 'COUNTY_PIN', 'OWNER_NAME', 'TAX_NAME',  'CO_NAME', COLUMNS.SALE_DATE, COLUMNS.NUM_UNITS]]

    tc_parcels = tc_parcels.join(mpls_licenses[['apn', 'address', 'licenseNum', 'issueDate', 'applicantN', 'ownerName', 'xPhone', 'xEmail']].rename(
        columns={'address': 'LCNS_ADD', 'ownerName': 'LCNS_OWNR','applicantN': COLUMNS.LCNS_APPL, 'xEmail': 'email', 'xPhone': 'phone'}), how='left')
    allAddresses = tc_parcels.join(allKeys[['PORT_ID', 'PORT_SZ']], how='left')

    allAddresses[COLUMNS.LAT] = allAddresses['geometry'].centroid.y
    allAddresses[COLUMNS.LON] = allAddresses['geometry'].centroid.x

    allAddresses[COLUMNS.NAMES] = allAddresses.apply(lambda row: listOfUniqueStrings(
        row['LCNS_OWNR'], row['LCNS_APPL'], row['OWNER_NAME'], row['TAX_NAME']), axis=1)
    for col in ['OWNER_NAME', 'TAX_NAME']:
        allAddresses[col] = allAddresses[col].str.strip()

    print ('Parcels with no addresses')
    print(allAddresses.loc[allAddresses[COLUMNS.ADDRESS].isna()])

    print("Writing to data/gen/clean_grouped_rental_parcels.zip")

    geo_to_zip(allAddresses, "clean_grouped_rental_parcels", "data/gen/clean_grouped_rental_parcels") 
    print("Writing to data/gen/tags.csv")
    tags.to_csv('data/gen/tags.csv', mode='w')

    # Informational 
    portfolios = allAddresses.groupby(COLUMNS.PORT_ID)[[
        COLUMNS.NAMES,  COLUMNS.PORT_SZ]].agg({
            COLUMNS.PORT_SZ: min,
            COLUMNS.NAMES: lambda s: listOfUniqueStrings(s.tolist()),
        })
    portfolios = portfolios.sort_values(
        by=COLUMNS.PORT_SZ, ascending=False)
    allPortfolios = portfolios.reset_index()
    print(allPortfolios.head(20))

def read_violations():
    all_files = [
        f"data/raw/mpls-violations/ward{n}.csv" for n in range(1, 14)]
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
    df = df.rename(columns={'address' : COLUMNS.ADDRESS})
    df = df.drop(columns=['isResolved','filler1', 'violationDateStr'])

    toc = time.perf_counter()
    print(f"Loaded violations in {toc - tic:0.4f} seconds")
    tic = time.perf_counter()
    df[COLUMNS.ADDRESS] = df[COLUMNS.ADDRESS].apply( lambda s: expandAddress(s).upper() + ", MINNEAPOLIS")
    toc = time.perf_counter()
    print(f"Violations addresses normalized in in {toc - tic:0.4f} seconds")
    return df    

def process_violations():
    violations = read_violations()
    violations.to_csv('data/gen/violations.csv', mode='w')

if __name__ == "__main__":
    process_parcels()
    process_violations()