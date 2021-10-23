from django.shortcuts import redirect

import pandas as pd
from django.http import JsonResponse

from violations.violation_data import ViolationData
import time
from parcels.parcel_data import ParcelData
from parcels.views import countViolations

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

def tags(request):
    parcels = parcelData.parcels
    if request.method == "GET":
        portfolioId = request.GET[ParcelData.columns.PORT_ID]
    elif request.method == "POST":
        portfolioId = request.POST[ParcelData.columns.PORT_ID]
    portfolioId = int(portfolioId)

    sameOwner = parcels.loc[parcels[ParcelData.columns.PORT_ID]
                             == portfolioId]
 
    tags = get_address_tags(sameOwner[ParcelData.columns.ADDRESS].tolist()) 

    tags['tag'] =  tags['tag_type'] + '|' + tags['tag_value']
    unique_tags = pd.DataFrame.drop_duplicates(tags[['tag']])
    keyed_tags = tags[['address','tag']].set_index('tag') 
    links = pd.merge(keyed_tags,keyed_tags,left_index=True, right_index=True, how='outer')
    links = links[links['address_x']!=links['address_y']].reset_index()
    print(links)
    links.to_csv(f'data/gen/links-{portfolioId}.csv', mode='w')

    # Create the graph of 
    keyed_tags = tags[[COLUMNS.ADDRESS,'tag']].set_index(COLUMNS.ADDRESS) 
    links = pd.merge(keyed_tags,keyed_tags,left_index=True, right_index=True, how='outer')
    links = links[links['tag_x']!=links['tag_y']].reset_index()
    links = links.groupby(['tag_x', 'tag_y']).agg(['count'])
    links.to_csv(f'data/gen/tag-links-{portfolioId}.csv', mode='w')

    unique_tags.to_csv(f'data/gen/unique_tags-{portfolioId}.csv', mode='w')

    sameOwner[['address']].to_csv(f'data/gen/address-{portfolioId}.csv', mode='w')
    
    data = {
  #      "property_tags": tags.to_dict(orient='records'),
        "unique_tags": unique_tags.to_dict(orient='records'),
  #      "links": links.to_dict(orient='records')

    }
    return JsonResponse(data)