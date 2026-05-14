class NoCacheForAuthenticatedMiddleware:
    """
    Adds Cache-Control: no-store to all responses for authenticated users.
    This prevents the browser from caching protected pages, so pressing Back
    forces a fresh fetch from the server instead of restoring from BFCache.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
