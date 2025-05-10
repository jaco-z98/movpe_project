import requests
from django.http import HttpResponse
from django.conf import settings
import re

def proxy_view(request, path=''):
    """
    Proxy view that forwards requests to sqlite-web
    """
    # Remove the 'data/' prefix from the path
    if path.startswith('data/'):
        path = path[5:]
    
    # Construct the target URL
    target_url = f'http://127.0.0.1:8085/{path}'
    
    # List of hop-by-hop headers that should not be forwarded
    hop_by_hop_headers = {
        'connection', 'keep-alive', 'proxy-authenticate',
        'proxy-authorization', 'te', 'trailers', 'transfer-encoding',
        'upgrade'
    }
    
    # Filter out hop-by-hop headers from request
    headers = {
        key: value for key, value in request.headers.items()
        if key.lower() not in hop_by_hop_headers
    }
    
    # Forward the request
    resp = requests.request(
        method=request.method,
        url=target_url,
        headers=headers,
        data=request.body,
        cookies=request.COOKIES,
        allow_redirects=False,
    )
    
    # Get the content type
    content_type = resp.headers.get('Content-Type', '')
    
    # Create the response
    if 'text/html' in content_type:
        # For HTML content, rewrite the URLs
        content = resp.content.decode('utf-8')
        
        # Rewrite static file paths
        content = re.sub(
            r'(href|src)="(/static/|/css/|/js/|/img/)',
            r'\1="/data\2',
            content
        )
        
        # Rewrite API endpoints
        content = re.sub(
            r'(action|href)="(/api/|/db/)',
            r'\1="/data\2',
            content
        )
        
        response = HttpResponse(
            content=content.encode('utf-8'),
            status=resp.status_code,
            content_type=content_type
        )
    else:
        # For non-HTML content, return as is
        response = HttpResponse(
            content=resp.content,
            status=resp.status_code,
            content_type=content_type
        )
    
    # Copy headers, excluding hop-by-hop headers
    for key, value in resp.headers.items():
        if key.lower() not in hop_by_hop_headers:
            response[key] = value
            
    return response 