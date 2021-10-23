from django.shortcuts import render
from django.shortcuts import redirect
import re
import pandas as pd
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
    address = parcelData.parcels.loc[key][COLUMNS.ADDRESS]
    return [address]


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
    if name:
        searchTerms = name.split(" ")
        patterns = ["(" + r"(^|\s)"+word.replace("*", r"\S*").replace("_", ".*") +
                    r"($|\s)" + ")" for word in searchTerms]
        pattern = "|".join(patterns)
        print(pattern)
        matchingOwnerName = parcels[parcels[COLUMNS.NAMES].str.contains(
            pattern, na=False, case=False, regex=True)]
        matchingApplicantName = parcels[parcels[COLUMNS.LCNS_APPL].str.contains(
            pattern, na=False, case=False, regex=True)]
        matches = pd.concat([matchingOwnerName, matchingApplicantName])
    else:
        return redirect(f"/parcels/portfolios")

    portfolios = matches.groupby(COLUMNS.PORT_ID)[[
        COLUMNS.NAMES, 'LCNS_APPL', COLUMNS.PORT_SZ]].agg({
            COLUMNS.PORT_SZ: min,
            COLUMNS.NAMES: lambda s: '; '.join(list(set(s.dropna()))),
        }).reset_index()

    context = {
        'name': name,
        'portfolios': portfolios.to_dict(orient='records')
    }
    return render(request, 'parcels/portfolio_search.html', context)


def portfolios(request):
    """
    Display all portfolios
    """
    portfolios = parcelData.allPortfolios
    context = {
        'portfolios': portfolios.to_dict(orient='records')
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
