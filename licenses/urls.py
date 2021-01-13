from django.urls import path

from . import views

urlpatterns = [
    path('/', views.index, name='index'),
    path('/property', views.property, name="property"),
    path('/search', views.search, name="search"),
    path('/portfolios', views.portfolios),
    path('/portfolio_search', views.portfolio_search),
    path('/portfolio', views.portfolio),
    path('/map', views.map),
]
