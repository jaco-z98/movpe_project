from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import sqlite_web
import io
import sys
from urllib.parse import urlparse

# Create your views here.

class CaptureOutput:
    def __init__(self):
        self.output = io.StringIO()
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr

    def __enter__(self):
        sys.stdout = self.output
        sys.stderr = self.output
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

@csrf_exempt
def sqlite_web_proxy(request):
    print(">>>>request: ", request)

    # Capture sqlite-web output
    with CaptureOutput() as capture:
        # Get the path from the request
        path = request.path
        
        # Create a mock environment for sqlite-web
        environ = {
            'REQUEST_METHOD': request.method,
            'PATH_INFO': path,
            'QUERY_STRING': request.META.get('QUERY_STRING', ''),
            'CONTENT_TYPE': request.META.get('CONTENT_TYPE', ''),
            'CONTENT_LENGTH': request.META.get('CONTENT_LENGTH', ''),
            'wsgi.input': io.BytesIO(request.body) if request.body else None,
            'HTTP_COOKIE': request.META.get('HTTP_COOKIE', ''),
        }
        
        # Add headers
        for key, value in request.headers.items():
            environ[f'HTTP_{key.upper().replace("-", "_")}'] = value

        # Run sqlite-web
        sqlite_web.app.run(environ, lambda status, headers, exc_info=None: None)

    # Get the captured output
    response_text = capture.output.getvalue()
    
    # Create response
    response = HttpResponse(response_text)
    
    # Add headers
    response['Content-Type'] = 'text/html'
    
    return response
