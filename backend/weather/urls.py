from django.urls import path
from weather import views

urlpatterns = [
    path('', views.index, name='index'),
    path('autocomplete/', views.autocomplete, name='autocomplete'),
    path('api/cities/', views.city_popularity_view, name='city_popularity'),
]
