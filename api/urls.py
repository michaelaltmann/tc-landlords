from django.urls import path

from . import views

urlpatterns = [
    path('portfolio', views.portfolio),
    path('portfolio_network', views.portfolio_network),
]
