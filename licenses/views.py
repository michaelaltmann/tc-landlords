from django.shortcuts import render
from django.shortcuts import redirect
import re
import pandas as pd
from django.http import HttpResponse
from .transform import cleanName, street_abvs
from violations.violation_data import ViolationData
import time
from .license_data import LicenseData

licenseData = LicenseData()
violationData = ViolationData()


def countViolations(address):
    countByAddress = violationData.countByAddress
    if address in countByAddress.index:
        row = countByAddress.loc[address]
        return row['violationCount']
    else:
        return 0


def index(request):
    """
    Home page for rental licenses
    """
    licenses = licenseData.licenses
    context = {
        'licenses': licenses[['ownerName', 'portfolioSize']],
        'address': ''}
    return render(request, 'licenses/index.html', context)


def property(request):
    """
    Display info about one property
    """
    licenses = licenseData.licenses
    violations = violationData.violations
    if request.method == "GET":
        address = request.GET['address']
    elif request.method == "POST":
        address = request.POST['address']
    if not address in licenseData.licenses.index:
        context = {

        }
        return render(request, 'licenses/list.html', context)
    license = licenses.loc[address]
    portfolioId = license['portfolioId']
    sameOwner = licenses.loc[licenses['portfolioId']
                             == portfolioId][['licenseNum', 'ownerName']]
    sameOwner = sameOwner.reset_index()
    sameOwner['violationCount'] = sameOwner['address'].apply(
        lambda address: countViolations(address))
    sameOwner = sameOwner.sort_values(by='address')
    propertyViolations = violations[violations.address ==
                                    address].sort_values(by='violationDate', ascending=False)
    context = {'licenses': licenses,
               'address': address,
               'license': license,
               'portfolioId': portfolioId,
               'sameOwner': sameOwner.to_dict(orient='records'),
               'violations': propertyViolations.to_dict(orient='records')}
    return render(request, 'licenses/property.html', context)


def portfolio(request):
    """
    Display all the properties for one portfolio
    """
    licenses = licenseData.licenses
    if request.method == "GET":
        portfolioId = request.GET['portfolioId']
    elif request.method == "POST":
        portfolioId = request.POST['portfolioId']
    portfolioId = int(portfolioId)
    sameOwner = licenses.loc[licenses['portfolioId']
                             == portfolioId][['licenseNum',  'ownerName', 'applicantN']]
    sameOwner = sameOwner.reset_index()
    sameOwner['violationCount'] = sameOwner['address'].apply(
        lambda address: countViolations(address))
    sameOwner = sameOwner.sort_values(by='address')

    # For each property, get a list of words in the name that are not part of the address
    # For example, if the owner is Tom Smith, this will allow us to search for any property
    # owned by Tom or Smith
    wordLists = list(sameOwner.apply(
        lambda row: [word for word in re.sub(r"[^a-zA-Z]", " ", cleanName(row['ownerName'])).split(' ') if not word in row['address']], axis=1))
    # Concat all the wordLists
    words = []
    for l in wordLists:
        words = words + l
    distinctWords = list(set(words))
    wordsToSkip = ['management', 'home', 'properties', 'property']
    searchTerms = [w for w in distinctWords if len(
        w) > 2 and w not in wordsToSkip and w not in street_abvs]
    pattern = " ".join(searchTerms)

    context = {
        'portfolioId': portfolioId,
        'searchTerms': pattern,
        'sameOwner': sameOwner.to_dict(orient='records')
    }
    return render(request, 'licenses/portfolio.html', context)


def search(request):
    """
    Display a list of properties that match search criteria
    """
    licenses = licenseData.licenses
    if request.method == "GET":
        address = request.GET['address']
    elif request.method == "POST":
        address = request.POST['address']
    matches = licenses[licenses.index.str.contains(
        address, na=False, case=False)]
    if len(matches.index) == 1:
        address = matches.iloc[0].name
        return redirect(f"/licenses/property?address={address}")
    else:
        matches = matches[['licenseNum',  'ownerName']
                          ].reset_index().sort_values(by='address')
        context = {'address': address,
                   'properties': matches.to_dict(orient='records')}
        return render(request, 'licenses/list.html', context)


def portfolio_search(request):
    """
    Find portfolios by owner/applicant name.  The name is treated as a space-separated
    list of search terms.  For example Tom* Smith searches for any owner or applicant containing
    a word starting with Tom or the word Smith
    If no name is provided display all portfolios
    """
    licenses = licenseData.licenses
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
        matchingOwnerName = licenses[licenses.ownerName.str.contains(
            pattern, na=False, case=False, regex=True)]
        matchingApplicantName = licenses[licenses.applicantN.str.contains(
            pattern, na=False, case=False, regex=True)]
        matches = pd.concat([matchingOwnerName, matchingApplicantName])
    else:
        return redirect(f"/licenses/portfolios")

    portfolios = matches.groupby('portfolioId')[[
        'ownerName', 'applicantN', 'portfolioSize']].agg({
            'portfolioSize': min,
            'ownerName': lambda s: '; '.join(list(set(s.dropna()))),
            'applicantN': lambda s: '; '.join(list(set(s.dropna()))),
        }).reset_index().rename(columns={"ownerName": "ownerNames", "applicantN": "applicantNames"})

    context = {
        'name': name,
        'portfolios': portfolios.to_dict(orient='records')
    }
    return render(request, 'licenses/portfolio_search.html', context)


def portfolios(request):
    """
    Display all portfolios
    """
    portfolios = licenseData.allPortfolios
    context = {
        'portfolios': portfolios.to_dict(orient='records')
    }
    return render(request, 'licenses/portfolios.html', context)


def map(request):
    """
    Display a map with dots for the properties
    in a portfolio.
    """
    licenses = licenseData.licenses
    if request.method == "GET":
        portfolioId = request.GET['portfolioId']
    elif request.method == "POST":
        portfolioId = request.POST['portfolioId']
    portfolioId = int(portfolioId)

    sameOwner = licenses.loc[licenses['portfolioId']
                             == portfolioId][['licenseNum',  'ownerName', 'latitude', 'longitude']]
    sameOwner = sameOwner.reset_index()
    context = {
        'portfolioId': portfolioId,
        'mapbox_access_token': 'pk.eyJ1IjoibWFsdG1hbm4iLCJhIjoiQjgzZTEyNCJ9.0_UJWIO6Up0HkMQajYj6Ew',
        'properties': sameOwner.to_dict(orient='records')
    }
    return render(request, 'licenses/map.html', context)
