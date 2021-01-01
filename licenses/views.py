from django.shortcuts import render
import pandas as pd
from django.http import HttpResponse
from .transform import cleanAddressLine
from violations.violations import Violations

v = Violations()
v.load()
violations = v.violations
print(violations)

# Create your views here.
print('** Loading licenses **')
licenses = pd.read_csv('licenses/clean_grouped_rental_licenses.csv', index_col=0,
                       low_memory=False)


def index(request):
    """
    Home page for rental licenses
    """
    context = {'licenses': licenses[[
        'address', 'ownerName', 'portfolioSize']], 'address': ''}
    return render(request, 'licenses/index.html', context)


def countViolations(address):
    return len(violations[violations.address == address].index)


def property(request):
    """
    Display info about one property
    """
    if request.method == "GET":
        apn = request.GET['apn']
    elif request.method == "POST":
        apn = request.POST['apn']
    if not apn in licenses.index:
        context = {
            'message': 'No matching rental license'
        }
        return render(request, 'licenses/list.html', context)
    license = licenses.loc[apn]
    portfolioId = license['portfolioId']
    sameOwner = licenses.loc[licenses['portfolioId']
                             == portfolioId][['licenseNum', 'address', 'ownerName']]
    sameOwner['violationCount'] = sameOwner['address'].apply(
        lambda address: countViolations(address))
    sameOwner = sameOwner.reset_index().sort_values(by='address')
    propertyViolations = violations[violations.address ==
                                    license['address']].sort_values(by='violationDate', ascending=False)
    print(f"Violations:\n{propertyViolations}")
    context = {'licenses': licenses,
               'apn': apn,
               'license': license,
               'sameOwner': sameOwner.to_dict(orient='records'),
               'violations': propertyViolations.to_dict(orient='records')}
    return render(request, 'licenses/property.html', context)


def portfolio(request):
    """
    Display all the properties for one portfolio
    """
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
    if request.method == "GET":
        address = request.GET['address']
    elif request.method == "POST":
        address = request.POST['address']
    matches = licenses[licenses.address.str.contains(
        address, na=False, case=False)]
    matches = matches[['licenseNum', 'address', 'ownerName']
                      ].reset_index().sort_values(by='address')
    context = {'address': address,
               'properties': matches.to_dict(orient='records')}
    return render(request, 'licenses/list.html', context)


def portfolios(request):
    """
    Find portfolios by owner name
    """
    if request.method == "GET":
        name = request.GET['name']
    elif request.method == "POST":
        name = request.POST['name']
    matchingOwnerName = licenses[licenses.ownerName.str.contains(
        name, na=False, case=False, regex=True)]
    matchingApplicantName = licenses[licenses.applicantN.str.contains(
        name, na=False, case=False, regex=True)]
    matches = pd.concat([matchingOwnerName, matchingApplicantName])
    g = matches.groupby('portfolioId')['ownerName']
    portfolios = [{'portfolioId': portfolioId, 'ownerNames': ", ".join(
        list(set(group.tolist())))} for portfolioId, group in g]
    context = {
        'portfolios': portfolios
    }
    return render(request, 'licenses/portfolios.html', context)
