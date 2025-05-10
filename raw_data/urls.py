from django.urls import path
from . import views

urlpatterns = [
    path('db/', views.sqlite_web_proxy, name='sqlite_web_proxy'),
    path('db/<path:path>', views.sqlite_web_proxy, name='sqlite_web_proxy_path'),
] 