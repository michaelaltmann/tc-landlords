from django.shortcuts import redirect

import pandas as pd
from django.http import JsonResponse

from violations.violation_data import ViolationData
import time
from licenses.license_data import LicenseData
from licenses.views import countViolations

licenseData = LicenseData()
violationData = ViolationData()


def asFeature(p):
    return {
        "type": "Feature",
        'properties': p,
        "geometry": {
            "type": "Point",
            "coordinates": [
                p['longitude'], p['latitude']
            ]
        }
    }


def portfolio(request):
    licenses = licenseData.licenses
    if request.method == "GET":
        portfolioId = request.GET['portfolioId']
    elif request.method == "POST":
        portfolioId = request.POST['portfolioId']
    portfolioId = int(portfolioId)

    sameOwner = licenses.loc[licenses['portfolioId']
                             == portfolioId][['licenseNum', 'address', 'ownerName', 'latitude', 'longitude']]
    sameOwner['violationCount'] = sameOwner['address'].apply(
        lambda address: countViolations(address))

    features = [asFeature(p) for p in sameOwner.to_dict(orient='records')]
    data = {
        "type": "FeatureCollection",
        "features": features
    }
    return JsonResponse(data)
