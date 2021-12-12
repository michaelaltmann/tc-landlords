from django.urls import path

from . import views

urlpatterns = [
    path('portfolio.json', views.portfolio),
    path('portfolio_network.xml', views.portfolio_network_xml),
    path('portfolio_network.json', views.portfolio_network_json),
]
