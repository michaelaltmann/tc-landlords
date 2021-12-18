from django.shortcuts import redirect, render

import pandas as pd
from django.http import JsonResponse

from violations.violation_data import ViolationData
import time
from parcels.parcel_data import ParcelData
from parcels.views import countViolations
import numpy as np
parcelData = ParcelData()
violationData = ViolationData()
COLUMNS = ParcelData.COLUMNS

def asFeature(p):
    return {
        "type": "Feature",
        'properties': p,
        "geometry": {
            "type": "Point",
            "coordinates": [
                p[COLUMNS.LON], p[COLUMNS.LAT]
            ]
        }
    }


def portfolio(request):
    parcels = parcelData.parcels
    if request.method == "GET":
        portfolioId = request.GET[COLUMNS.PORT_ID]
    elif request.method == "POST":
        portfolioId = request.POST[COLUMNS.PORT_ID]
    portfolioId = int(portfolioId)

    sameOwner = parcels.loc[parcels[COLUMNS.PORT_ID]
                             == portfolioId][
                                 [COLUMNS.ADDRESS,'licenseNum', COLUMNS.NAMES, COLUMNS.LAT, COLUMNS.LON]]
    sameOwner = sameOwner.loc[sameOwner[COLUMNS.LAT].notnull() &
                              sameOwner[COLUMNS.LON].notnull()]
    sameOwner = sameOwner.fillna('NA')
    sameOwner['violationCount'] = sameOwner.index.map(
        lambda key: countViolations(key))

    features = [asFeature(p)
                for p in sameOwner.reset_index().to_dict(orient='records')]
    data = {
        "type": "FeatureCollection",
        "features": features
    }
    return JsonResponse(data)

def get_address_tags(addresses):
    tags = parcelData.tags
    address_tags = tags[tags.address.isin(addresses)].drop_duplicates()
    return address_tags.sort_values(by=[COLUMNS.ADDRESS,'tag_type', 'tag_value'])

def listOfUniqueStrings(series):
    strings = series.dropna().tolist()
    trimmedStrings = [s.strip() for s in strings if isinstance(s, str) and s.strip() and len(s.strip())>0]
    trimmedStrings = list(set(trimmedStrings))
    trimmedStrings.sort()
    return "~".join(trimmedStrings)

def portfolio_network_data(request):
    parcels = parcelData.parcels
    if request.method == "GET":
        portfolioId = request.GET[COLUMNS.PORT_ID]
    elif request.method == "POST":
        portfolioId = request.POST[COLUMNS.PORT_ID]
    portfolioId = int(portfolioId)

    samePortfolio = parcels.loc[parcels[COLUMNS.PORT_ID]
                             == portfolioId][[COLUMNS.ADDRESS]]
    tags = parcelData.tags.loc[samePortfolio.index.tolist()].reset_index()[[COLUMNS.keyCol, 'tag_value', 'source_value']].drop_duplicates()
    # Create a new source_value col with the joined set of source_values
    tags = tags.reset_index().groupby([COLUMNS.keyCol, 'tag_value']).agg(listOfUniqueStrings).reset_index()
    grouped_tags = tags.groupby('tag_value').agg('count')
    shared_grouped_tags = grouped_tags[grouped_tags[COLUMNS.keyCol]>1]
    shared_tag_values = shared_grouped_tags.index.unique().tolist()

    tags = tags[tags['tag_value'].isin(shared_tag_values)]
    tags['id'] = range(1, 1+len(tags))

    data = {
        'parcels' : samePortfolio.reset_index().to_dict(orient='records'),
        'tag_values': shared_tag_values,
        "tags": tags.to_dict(orient='records')
    }
    return data

def portfolio_network_xml(request):
    context = portfolio_network_data(request)
    return render(request, 'api/portfolio_network.xml', context, content_type="application/xml")

def portfolio_network_json(request):
    data = portfolio_network_data(request)
    return JsonResponse(data)
