from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, HttpResponseForbidden
from .proxy import proxy_view
import logging

logger = logging.getLogger(__name__)

def debug_proxy_view(request, path=''):
    logger.info(f"Debug proxy view called with path: {request.path}, captured path: {path}")
    return proxy_view(request, path)

# def catch_all(request, path=''):
#     return HttpResponseForbidden()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('data_app.urls')),
    path('data/', debug_proxy_view, name='proxy_view_root'),
    path('data/<path:path>', debug_proxy_view, name='proxy_view'),
    # path('<path:path>', catch_all, name='catch_all'),  # This will catch all other requests
]
