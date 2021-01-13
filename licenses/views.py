from django.shortcuts import render
from django.shortcuts import redirect

import pandas as pd
from django.http import HttpResponse
from .transform import cleanAddressLine
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
    context = {'licenses': licenses[[
        'address', 'ownerName', 'portfolioSize']], 'address': ''}
    return render(request, 'licenses/index.html', context)


def property(request):
    """
    Display info about one property
    """
    licenses = licenseData.licenses
    violations = violationData.violations
    if request.method == "GET":
        apn = request.GET['apn']
    elif request.method == "POST":
        apn = request.POST['apn']
    if not apn in licenseData.licenses.index:
        context = {

        }
        return render(request, 'licenses/list.html', context)
    license = licenses.loc[apn]
    portfolioId = license['portfolioId']
    sameOwner = licenses.loc[licenses['portfolioId']
                             == portfolioId][['licenseNum', 'tier', 'address', 'ownerName']]
    sameOwner['violationCount'] = sameOwner['address'].apply(
        lambda address: countViolations(address))
    sameOwner = sameOwner.reset_index().sort_values(by='address')
    propertyViolations = violations[violations.address ==
                                    license['address']].sort_values(by='violationDate', ascending=False)
    context = {'licenses': licenses,
               'apn': apn,
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
                             == portfolioId][['licenseNum', 'address', 'ownerName']]
    sameOwner['violationCount'] = sameOwner['address'].apply(
        lambda address: countViolations(address))
    sameOwner = sameOwner.reset_index().sort_values(by='address')
    print(f"Portfolio {portfolioId}\n{sameOwner}")

    context = {
        'portfolioId': portfolioId,
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
    matches = licenses[licenses.address.str.contains(
        address, na=False, case=False)]
    if len(matches.index) == 1:
        apn = matches.iloc[0].name
        return redirect(f"/licenses/property?apn={apn}")
    else:
        matches = matches[['licenseNum', 'address', 'ownerName']
                          ].reset_index().sort_values(by='address')
        context = {'address': address,
                   'properties': matches.to_dict(orient='records')}
        return render(request, 'licenses/list.html', context)


def portfolio_search(request):
    """
    Find portfolios by owner name, or diplay largest
    """
    licenses = licenseData.licenses
    if request.method == "GET":
        name = request.GET.get('name', "")
    elif request.method == "POST":
        name = request.POST.get('name', "")
    if name:
        matchingOwnerName = licenses[licenses.ownerName.str.contains(
            name, na=False, case=False, regex=True)]
        matchingApplicantName = licenses[licenses.applicantN.str.contains(
            name, na=False, case=False, regex=True)]
        matches = pd.concat([matchingOwnerName, matchingApplicantName])
        message = f"Portfolios matching {name}"
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
    licenses = licenseData.licenses
    if request.method == "GET":
        portfolioId = request.GET['portfolioId']
    elif request.method == "POST":
        portfolioId = request.POST['portfolioId']
    portfolioId = int(portfolioId)

    sameOwner = licenses.loc[licenses['portfolioId']
                             == portfolioId][['licenseNum', 'address', 'ownerName', 'latitude', 'longitude']]
    context = {
        'portfolioId': portfolioId,
        'mapbox_access_token': 'pk.eyJ1IjoibWFsdG1hbm4iLCJhIjoiQjgzZTEyNCJ9.0_UJWIO6Up0HkMQajYj6Ew',
        'properties': sameOwner.to_dict(orient='records')
    }
    return render(request, 'licenses/map.html', context)
