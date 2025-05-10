from django.contrib import admin
from django.urls import path, include, re_path
from .proxy import proxy_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('app/', include('data_app.urls')),
    re_path(r'^data/(?P<path>.*)$', proxy_view),
]
