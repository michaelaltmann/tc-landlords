from django.urls import path

from . import views

urlpatterns = [
    path('', views.index),
    path('property', views.property),
    path('search', views.search),
    path('portfolios', views.portfolios),
    path('portfolio_search', views.portfolio_search),
    path('portfolio', views.portfolio),
    path('portfolio_tags', views.portfolio_tags),
    path('map', views.map),
    path('search', views.search),
    path('clear', views.clear),
    path('network', views.network)
]
