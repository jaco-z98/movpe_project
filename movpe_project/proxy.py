import requests
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
import re
from urllib.parse import urljoin, urlencode

def proxy_view(request, path=''):
    """
    Proxy view that forwards requests to sqlite-web
    """
    print(">>>> proxy_view req:", request)
    print(">>>> proxy_view path:", path)
    print(">>>> proxy_view method:", request.method)
    print(">>>> proxy_view headers:", dict(request.headers))
    
    # Remove the 'data/' prefix from the path
    if path.startswith('data/'):
        path = path[5:]

    # Add query parameters to the path
    if request.GET:
        query_string = urlencode(request.GET)
        path = f"{path}?{query_string}"

    # Block access to any path that doesn't start with 'raw_data_rawmeasurement/' or 'static/'
    # if not path.startswith('raw_data_rawmeasurement/') and not path.startswith('raw_data_rawmeasurement/content/') and not path.startswith('static/'):
    #     return HttpResponseForbidden()

    # Construct the target URL
    target_url = f'http://127.0.0.1:8085/{path}'
    print("target_url:", target_url)
    
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
    print("forwarding headers:", headers)
    
    # Forward the request
    resp = requests.request(
        method=request.method,
        url=target_url,
        headers=headers,
        data=request.body,
        cookies=request.COOKIES,
        allow_redirects=False,  # Don't follow redirects automatically
    )
    
    print("response status:", resp.status_code)
    print("response headers:", dict(resp.headers))
    
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
        
        # Rewrite relative URLs that don't start with /data/
        content = re.sub(
            r'(href|action)="(?!http|https|/data|/static|/css|/js|/img)([^"]+)"',
            r'\1="/data/\2"',
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
    
    # # Copy headers, excluding hop-by-hop headers
    # for key, value in resp.headers.items():
    #     if key.lower() not in hop_by_hop_headers:
    #         # If this is a Location header (redirect), rewrite the URL
    #         if key.lower() == 'location':
    #             print("Original location header:", value)
    #             # If the location is relative, make it absolute first
    #             if not value.startswith(('http://', 'https://')):
    #                 value = urljoin(target_url, value)
    #             # Then rewrite it to use our /data/ prefix
    #             if value.startswith('http://127.0.0.1:8085/'):
    #                 value = value.replace('http://127.0.0.1:8085/', '/data/')
    #             elif value.startswith('/'):
    #                 value = '/data' + value
    #             print("Rewritten location header:", value)
    #         response[key] = value
            
    return response 