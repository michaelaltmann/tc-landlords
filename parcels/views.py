from django.shortcuts import render
from django.shortcuts import redirect
import re
import pandas as pd
import numpy as np
from .transform import cleanName, street_abvs
from violations.violation_data import ViolationData
from .parcel_data import ParcelData
COLUMNS = ParcelData.COLUMNS
parcelData = ParcelData()
violationData = ViolationData()

def get_addresses_for_key(key):
    '''
    Handle the slight chance that there are multiple addresses
    for the same parcel
    '''
    addresses =  parcelData.parcels.loc[key][COLUMNS.ADDRESS]
    if isinstance(addresses,str):
        return [addresses]
    else:
        return addresses.tolist()


def countViolations(key):
    addresses_for_key = get_addresses_for_key(key)
    total = 0
    for address in addresses_for_key:
        countByAddress = violationData.countByAddress
        if address in countByAddress.index:
            row = countByAddress.loc[address]
            total = total +  row['violationCount']
    return total


def index(request):
    """
    Home page for rental parcels
    """
    parcels = parcelData.parcels
    context = {
        'parcels': parcels[[COLUMNS.NAMES, COLUMNS.PORT_SZ]],
        'key': ''}
    return render(request, 'parcels/index.html', context)

def get_tags(keys):
    tags = parcelData.tags
    parcel_tags = tags.loc[keys].reset_index().drop_duplicates().set_index(COLUMNS.keyCol)
    parcel_tags = parcel_tags.join(parcelData.parcels[[COLUMNS.ADDRESS]], how='left')
    return parcel_tags.sort_values(by=[COLUMNS.keyCol,'tag_type', 'tag_value']).to_dict(orient='records')

def property(request):
    """
    Display info about one parcel
    """
    parcels = parcelData.parcels
    violations = violationData.violations
    if request.method == "GET":
        key = request.GET['key']
    elif request.method == "POST":
        key = request.POST['key']
    if not key in parcelData.parcels.index:
        context = {
            'keyCol': COLUMNS.keyCol
        }
        return render(request, 'parcels/list.html', context)
    parcel = parcels.loc[key]
    portfolioId = parcel[COLUMNS.PORT_ID]
    sameOwner = parcels.loc[parcels[COLUMNS.PORT_ID]
                             == portfolioId][[COLUMNS.ADDRESS,'licenseNum', COLUMNS.NAMES]]
    sameOwner['violationCount'] = sameOwner.index.map(
        lambda key: countViolations(key))
    sameOwner = sameOwner.sort_values(by=COLUMNS.ADDRESS)
    propertyViolations = violations[violations[
        COLUMNS.ADDRESS]== parcel[COLUMNS.ADDRESS]
        ].sort_values(by='violationDate', ascending=False)
    context = {'parcels': parcels,
               'ADDRESS': parcel[COLUMNS.ADDRESS],
               'key': key,
               'details': parcel.reset_index(),
               COLUMNS.PORT_ID: portfolioId,
               'sameOwner': sameOwner.reset_index().to_dict(orient='records'),
               'violations': propertyViolations.to_dict(orient='records'),
               'tags':  get_tags([key])}
    return render(request, 'parcels/parcel.html', context)


def portfolio(request):
    """
    Display all the properties for one portfolio
    """
    parcels = parcelData.parcels
    if request.method == "GET":
        portfolioId = request.GET[COLUMNS.PORT_ID]
    elif request.method == "POST":
        portfolioId = request.POST[COLUMNS.PORT_ID]
    portfolioId = int(portfolioId)
    samePortfolio = parcels.loc[parcels[COLUMNS.PORT_ID]
                             == portfolioId][[COLUMNS.ADDRESS,'licenseNum', 'phone', 'email', COLUMNS.NAMES]]
    samePortfolio['violationCount'] = samePortfolio.index.map(
        lambda key: countViolations(key))
    samePortfolio = samePortfolio.sort_values(by=COLUMNS.ADDRESS)

    # For each property, get a list of words in the name that are not part of the address
    # For example, if the owner is Tom Smith, this will allow us to search for any property
    # owned by Tom or Smith
    wordLists = list(samePortfolio.apply(
        lambda row: [word for word in re.sub(r"[^a-zA-Z]", " ", cleanName(row[COLUMNS.NAMES])).split(' ') if row[COLUMNS.ADDRESS] and  not word in row[COLUMNS.ADDRESS]], axis=1))
    # Concat all the wordLists
    words = []
    for l in wordLists:
        for word in l:
            words.append(word)
    distinctWords = list(set(words))
    wordsToSkip = ['management', 'home', 'properties', 'property']
    searchTerms = [w for w in distinctWords if len(
        w) > 2 and w not in wordsToSkip and w not in street_abvs]
    pattern = " ".join(searchTerms)

    context = {
        COLUMNS.PORT_ID: portfolioId,
        'searchTerms': pattern,
        'sameOwner': samePortfolio.reset_index().to_dict(orient='records'),
        'tags':  get_tags(samePortfolio.index.tolist())
    }
    return render(request, 'parcels/portfolio.html', context)

def portfolio_tags(request):
    """
    Display the properties and shared tags
    """
    parcels = parcelData.parcels
    if request.method == "GET":
        portfolioId = request.GET[COLUMNS.PORT_ID]
        selected_tag_ids = []
    elif request.method == "POST":
        portfolioId = request.POST[COLUMNS.PORT_ID]
        selected_tag_ids = request.POST.getlist('selected_tag_ids[]', [])
    
    portfolioId = int(portfolioId)
    samePortfolio = parcels.loc[parcels[COLUMNS.PORT_ID]
                             == portfolioId][[COLUMNS.ADDRESS,'licenseNum', 'phone', 'email', COLUMNS.NAMES]]
    samePortfolio = samePortfolio.sort_values(by=COLUMNS.ADDRESS)
    tags = parcelData.tags.loc[samePortfolio.index.tolist()].reset_index().drop(columns=['source_type', 'source_value']).drop_duplicates().set_index(COLUMNS.keyCol)
    tags['tag_type_value'] = tags['tag_type'] + '|' + tags['tag_value']
    grouped_tags = tags.join(samePortfolio, how='left').reset_index().groupby(['tag_type','tag_value'])
    tag_freq = grouped_tags[COLUMNS.keyCol, 'tag_type_value'].agg({COLUMNS.keyCol: 'count', 'tag_type_value': np.min})
    tag_freq = tag_freq.rename(columns = {COLUMNS.keyCol: 'parcels'})
    shared_tag_groups = tag_freq[tag_freq['parcels']>1]
    shared_tag_groups['checked'] = shared_tag_groups['tag_type_value'].isin(selected_tag_ids)
    
    selected_tags = tags[ tags['tag_type_value'].isin(selected_tag_ids) ]
 
    from parcels.union_find import UnionFind
    uf = UnionFind()
    for id in selected_tags.index.unique(): #parcel IDs
        uf.add(id)
    for tag_type_and_value, group in grouped_tags[COLUMNS.keyCol]:
        rows = group.tolist()
        if len(rows) > 1:
            first = rows[0]
            for other in rows[1:]:
                if (first in uf and other in uf):
                    uf.union(first, other)

    samePortfolio['portfolio_subgroup'] = 0
    portfolio_subgroup = 0
    for component in uf.components():
        portfolio_subgroup = portfolio_subgroup +1
        for id in component:
            samePortfolio.loc[id,'portfolio_subgroup'] = portfolio_subgroup
    
    subgroup_count = len(uf.components())
    unassigned_count = len(samePortfolio[samePortfolio['portfolio_subgroup']==0].index)

    unmatched_tags = tags[ ~ tags['tag_type_value'].isin(selected_tag_ids) ]
    selected_parcel_ids = selected_tags.index.unique()
    unmatched_tags = unmatched_tags[ ~ unmatched_tags.index.isin(selected_parcel_ids)]
    grouped_unmatched_tags = unmatched_tags.reset_index().groupby(['tag_type','tag_value'])[[COLUMNS.keyCol]].agg('count').rename(columns={COLUMNS.keyCol: 'unassigned'})
    shared_tag_groups = shared_tag_groups.join(grouped_unmatched_tags)
    shared_tag_groups['unassigned'] = shared_tag_groups['unassigned'].fillna(0).astype('int')
    colors = ['black', 'red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet']
    context = {
        'portfolioId': portfolioId,
        'shared_tags': shared_tag_groups.reset_index().to_dict(orient='records'),
        'samePortfolio': samePortfolio.reset_index().to_dict(orient='records'),

        'colors': colors,
        'unassigned_count': unassigned_count,
        'subgroup_count': subgroup_count
    }
    return render(request, 'parcels/portfolio_tags.html', context)


def search(request):
    """
    Display a list of properties that match search criteria
    """
    parcels = parcelData.parcels
    if request.method == "GET":
        address = request.GET.get('address', '')
    elif request.method == "POST":
        address = request.POST.get('address', '')
    if address:
        # search by parcel ID
        matches = parcels[parcels.index.str.endswith(
            "-" +address, na=False)]
        if (len(matches.index) == 0):
            # search by address
            address_matches = parcels[parcels[COLUMNS.ADDRESS].str.contains(
                address, regex=False, na=False, case=False)]
            abbrev_address_matches = parcels[parcels[COLUMNS.ABBREV_ADD].str.contains(
                address, regex=False, na=False, case=False)]
            matches = pd.concat([address_matches,abbrev_address_matches],axis=0).drop_duplicates()

        if len(matches.index) == 1:
            # Exactly one match
            key = matches.iloc[0].name
            return redirect(f"/parcels/property?key={key}")
        else:
            matches = matches[[COLUMNS.ADDRESS,'licenseNum', COLUMNS.NAMES]
                              ].sort_values(by=COLUMNS.ADDRESS)
            context = {COLUMNS.ADDRESS: address,
                       'properties': matches.reset_index().to_dict(orient='records')}
            return render(request, 'parcels/list.html', context)
    else:
        return render(request, 'parcels/search.html')


def portfolio_search(request):
    """
    Find portfolios by owner/applicant name.  The name is treated as a space-separated
    list of search terms.  For example Tom* Smith searches for any owner or applicant containing
    a word starting with Tom or the word Smith
    If no name is provided display all portfolios
    """
    parcels = parcelData.parcels
    if request.method == "GET":
        name = request.GET.get('name', "")
    elif request.method == "POST":
        name = request.POST.get('name', "")
    if not name:
        return redirect(f"/parcels/portfolios")
    searchTerms = name.split(" ")
    patterns = ["(" + r"(^|\s)"+word.replace("*", r"\S*").replace("_", ".*") +
                r"($|\s)" + ")" for word in searchTerms]
    pattern = "|".join(patterns)
    print(pattern)
    matchingTags = parcelData.tags[ parcelData.tags['tag_value'].str.contains(pattern, na=False, case=False, regex=True) ]

    portfolio_ids = parcels.join(matchingTags, how="inner").drop_duplicates([COLUMNS.PORT_ID])[COLUMNS.PORT_ID].tolist()

    matchingPortfolios = parcelData.portfolios.loc[portfolio_ids]

    context = {
        'name': name,
        'portfolios': matchingPortfolios.reset_index().to_dict(orient='records')
    }
    return render(request, 'parcels/portfolio_search.html', context)



def portfolios(request):
    """
    Display all portfolios
    """
    if request.method == "GET":
        limit = request.GET.get('limit', '100')
    elif request.method == "POST":
        limit = request.POST.get('limit', '100')
    limit = int(limit)
    portfolios = parcelData.portfolios
    context = {
        'portfolios': portfolios.head(limit).reset_index().to_dict(orient='records')
    }
    return render(request, 'parcels/portfolios.html', context)


def map(request):
    """
    Display a map with dots for the properties
    in a portfolio.
    """
    parcels = parcelData.parcels
    if request.method == "GET":
        portfolioId = request.GET[COLUMNS.PORT_ID]
    elif request.method == "POST":
        portfolioId = request.POST[COLUMNS.PORT_ID]
    portfolioId = int(portfolioId)

    sameOwner = parcels.loc[parcels[COLUMNS.PORT_ID]
                             == portfolioId][[COLUMNS.ADDRESS,'licenseNum',  COLUMNS.NAMES, COLUMNS.LAT, COLUMNS.LON]]
    context = {
        'portfolioId': portfolioId,
        'mapbox_access_token': 'pk.eyJ1IjoibWFsdG1hbm4iLCJhIjoiQjgzZTEyNCJ9.0_UJWIO6Up0HkMQajYj6Ew',
        'properties': sameOwner.to_dict(orient='records')
    }
    return render(request, 'parcels/map.html', context)
