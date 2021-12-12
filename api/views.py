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

def portfolio_network(request):
    parcels = parcelData.parcels
    if request.method == "GET":
        portfolioId = request.GET[COLUMNS.PORT_ID]
    elif request.method == "POST":
        portfolioId = request.POST[COLUMNS.PORT_ID]
    portfolioId = int(portfolioId)

    samePortfolio = parcels.loc[parcels[COLUMNS.PORT_ID]
                             == portfolioId][[COLUMNS.ADDRESS]].reset_index().drop_duplicates().set_index(COLUMNS.keyCol)
    tags = parcelData.tags.loc[samePortfolio.index.tolist()].reset_index()[[COLUMNS.keyCol, 'tag_value']].drop_duplicates().set_index(COLUMNS.keyCol)
    grouped_tags = tags.reset_index().groupby('tag_value').agg('count')
    shared_grouped_tags = grouped_tags[grouped_tags[COLUMNS.keyCol]>1]
    shared_tag_values = shared_grouped_tags.index.unique().tolist()
    tags = tags[tags['tag_value'].isin(shared_tag_values)]
    tags['id'] = range(1, 1+len(tags))

    context = {
        'parcels' : samePortfolio.reset_index().to_dict(orient='records'),
        'tag_values': shared_tag_values,
        "tags": tags.reset_index().to_dict(orient='records')
    }
    return render(request, 'api/portfolio_network.xml', context, content_type="application/xml")

