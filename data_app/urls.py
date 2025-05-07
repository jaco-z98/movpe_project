from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('get_approximation_x/', views.get_approximation_x, name='get_approximation_x'),
    path('get_approximation_y/', views.get_approximation_y, name='get_approximation_y'),    
    path('data-preview/', views.preview_data, name='data_preview'),
    path('preview/', views.preview_data, name='preview_data'),
]