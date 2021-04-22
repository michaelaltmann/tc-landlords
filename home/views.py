from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    context = {}
    return render(request, 'home/index.html', context)


def search(request):
    context = {}
    return render(request, 'home/search.html', context)
