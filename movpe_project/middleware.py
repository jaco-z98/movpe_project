import logging

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info(f"Request received: {request.method} {request.path}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request GET params: {request.GET}")
        logger.info(f"Request POST params: {request.POST}")
        logger.info(f"Request META: {request.META}")
        
        response = self.get_response(request)
        logger.info(f"Response sent: {response.status_code} for {request.path}")
        return response 