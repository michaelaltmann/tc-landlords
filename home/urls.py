from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('/about', views.about),
    path('/help', views.help),
    path('/links', views.links),
]
