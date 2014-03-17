import taxii.settings
import taxii.handlers as handlers
import libtaxii.messages as tm

def taxii_auth_check(func):
    """
    The taxii_auth_check decorator checks the global taxii.AUTH_REQUIRED 
    flag to see if the application is configured to require authentication. If set to True
    and the request is not authenticated, a TAXII UNAUTHORIZED status message will be
    returned.
    """
    def inner(request, *args, **kwargs):
        if not taxii.settings.AUTH_REQUIRED:
            return func(request, *args, **kwargs)
        elif request.user.is_authenticated():
            return func(request, *args, **kwargs)
        
        m = tm.StatusMessage(tm.generate_message_id(), '0', status_type=tm.ST_UNAUTHORIZED, message='You are not authorized to access this URL.')
        return handlers.create_taxii_response(m)
    
    return inner