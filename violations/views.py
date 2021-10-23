from django.shortcuts import render

from violations.violation_data import ViolationData

violationData = ViolationData()

# Create your views here.


def index(request):
    """
    Home page for violations 
    """
    addresses = violationData.countByAddress.nlargest(
        20, 'violationCount').reset_index()

    context = {'addresses': addresses.to_dict(orient='records')}
    return render(request, 'violations/index.html', context)
