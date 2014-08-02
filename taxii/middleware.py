import logging
from django.http import HttpResponseServerError

import libtaxii.messages as tm
import taxii.handlers as handlers

class ProcessExceptionMiddleware(object):
    def process_exception(self, request, exception):
        #Method that process exceptions
        logger = logging.getLogger('TAXIIApplication.taxii.middleware.ProcessExceptionMiddleware.process_exception')
        logger.exception('Server error occured')
    
        if request.path.startswith('/services'):
            logger.debug('Returning ST_FAILURE message')
            m = tm.StatusMessage(tm.generate_message_id(), '0', status_type=tm.ST_FAILURE, message='An internal server error occurred')
            return handlers.create_taxii_response(m, handlers.HTTP_STATUS_OK, use_https=request.is_secure())

        resp = HttpResponseServerError()
        resp.body = 'A server error occurred'
        return resp