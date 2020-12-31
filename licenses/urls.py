from django.urls import path

from . import views

urlpatterns = [
    path('/', views.index, name='index'),
    path('/property', views.property, name='property'),
    path('/search', views.search, name='search'),
]
