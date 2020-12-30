from django.shortcuts import render
import pandas as pd
from django.http import HttpResponse

# Create your views here.
licenses = pd.read_csv('licenses/clean_grouped_rental_licenses.csv', index_col=0,
                       low_memory=False)


def index(request):
    """
    Home page for rental licenses
    """
    context = {'licenses': licenses}
    return render(request, 'index.html', context)


def property(request):
    """
    Display info about one property
    """
    if request.method == "GET":
        apn = request.GET['apn']
    elif request.method == "POST":
        apn = request.POST['apn']
    license = licenses.loc[apn]
    groupId = license['groupId']
    sameOwner = licenses.loc[licenses['groupId']
                             == groupId][['licenseNum', 'address', 'ownerName']]
    sameOwner = sameOwner.reset_index().sort_values(by='address')
    context = {'licenses': licenses,
               'apn': apn,
               'license': license,
               'sameOwner': sameOwner.to_dict(orient='records')}
    return render(request, 'property.html', context)
