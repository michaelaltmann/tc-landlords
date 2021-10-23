from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    context = {}
    return render(request, 'home/index.html', context)
def about(request):
    context = {}
    return render(request, 'home/about.html', context)
def help(request):
    context = {}
    return render(request, 'home/help.html', context)
def links(request):
    context = {}
    return render(request, 'home/links.html', context)


def search(request):
    context = {}
    return render(request, 'home/search.html', context)
