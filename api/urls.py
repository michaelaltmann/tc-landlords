from django.urls import path

from . import views

urlpatterns = [
    path('portfolio', views.portfolio),
    path('tags', views.tags),
]
