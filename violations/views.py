from django.shortcuts import render

from violations.violations import Violations

v = Violations()

# Create your views here.


def index(request):
    """
    Home page for violations 
    """
    addresses = v.countByAddress.nlargest(10, 'violationCount').reset_index()

    context = {'addresses': addresses.to_dict(orient='records')}
    return render(request, 'violations/index.html', context)
