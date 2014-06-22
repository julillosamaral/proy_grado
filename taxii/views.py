import logging
from django.views.decorators.csrf import csrf_exempt
from taxii.decorators import taxii_auth_check
import taxii.handlers as handlers
from taxii.utils import make_safe
import libtaxii.messages_11 as tm
import StringIO
from lxml import etree
from django.contrib.auth.models import User, Group
from taxii.models import Inbox, DataFeed, MessageBindingId, ContentBindingId, ContentBlock, ProtocolBindingId, DataFeedPushMethod, DataFeedPollInformation, DataFeedSubscriptionMethod, DataFeedSubscription, ContentBlockRTIR
from rest_framework.response import Response
from rest_framework import viewsets
from taxii.serializers import UserSerializer, GroupSerializer, InboxSerializer, DataFeedSerializer, MessageBindingIdSerializer, ContentBindingIdSerializer, ContentBlockSerializer, ProtocolBindingIdSerializer, DataFeedPushMethodSerializer, DataFeedPollInformationSerializer, DataFeedSubscriptionMethodSerializer, DataFeedSubscriptionSerializer, ContentBlockRTIRSerializer
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view

@csrf_exempt
@taxii_auth_check
def inbox_service(request, inbox_name):
    """Handles TAXII Inbox Service requests."""
    logger = logging.getLogger('TAXIIApplication.taxii.views.inbox_service')
    logger.debug('Entering Inbox service')

    resp = handlers.validate_taxii_request(request)
    if resp: return resp # if validation failed, return the response

    try:
        taxii_message = tm.get_message_from_xml(request.body)
    except Exception as ex:
        logger.debug('Unable to parse inbound message:s', ex.message)
        m = tm.StatusMessage(tm.generate_message_id(), '0', status_type=tm.ST_BAD_MESSAGE, message='Message received could not be parsed')
        return handlers.create_taxii_response(m, use_https=request.is_secure())

    logger.debug('Inbox [%s] received TAXII message with id [%s] and type [%s]',
                 make_safe(inbox_name), make_safe(taxii_message.message_id), make_safe(taxii_message.message_type))

    if taxii_message.message_type != tm.MSG_INBOX_MESSAGE:
        logger.info('TAXII message with id [%s] was not Inbox type [%s]', make_safe(taxii_message.message_id), make_safe(taxii_message.message_type))
        m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type=tm.ST_FAILURE, message='Message sent to Inbox service did not have an inbox Message type')
        return handlers.create_taxii_response(m, use_https=request.is_secure())

    resp = handlers.inbox_add_content(request, inbox_name, taxii_message)
    return resp

@csrf_exempt
@taxii_auth_check
def poll_service(request):
    """Handles TAXII Poll Service requests."""
    logger = logging.getLogger("TAXIIApplication.taxii.views.poll_service")
    logger.debug('Entering poll service')

    resp = handlers.validate_taxii_request(request)
    if resp: return resp # if validation failed, return the response

    try:
        taxii_message = tm.get_message_from_xml(request.body)
    except Exception as ex:
        logger.debug('Unable to parse inbound message: %s', ex.message)
        m = tm.StatusMessage(tm.generate_message_id(), '0', status_type=tm.ST_BAD_MESSAGE, message='Message received could not be parsed')
        return handlers.create_taxii_response(m, use_https=request.is_secure())

    logger.debug('Poll service received TAXII message with id [%s] and type [%s]', make_safe(taxii_message.message_id), make_safe(taxii_message.message_type))

    if taxii_message.message_type != tm.MSG_POLL_REQUEST:
        logger.info('TAXII message with id [%s] was not Poll request [%s]', make_safe(taxii_message.message_id), make_safe(taxii_message.message_type))
        m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type=tm.ST_FAILURE, message='Message sent to Poll service did not have a poll request message type')
        return handlers.create_taxii_response(m, use_https=request.is_secure())

    resp = handlers.poll_get_content(request, taxii_message)
    return resp

@csrf_exempt
@taxii_auth_check
def discovery_service(request):
    """Handles TAXII Discovery Service requests"""
    logger = logging.getLogger('TAXIIApplication.taxii.views.discovery_service')
    logger.debug('Entering discovery service')

    resp = handlers.validate_taxii_request(request)
    if resp: return resp # if validation fails, return the response

    try:
        taxii_message = tm.get_message_from_xml(request.body)
    except Exception as ex:
        logger.debug('Unable to parse inbound message: %s', ex.message)
        m = tm.StatusMessage(tm.generate_message_id(), '0', status_type=tm.ST_BAD_MESSAGE, message='Message received could not be parsed')
        return handlers.create_taxii_response(m, use_https=request.is_secure())

    logger.debug('Discovery service received TAXII message with id [%s] and type [%s]', make_safe(taxii_message.message_id), make_safe(taxii_message.message_type))

    if taxii_message.message_type != tm.MSG_DISCOVERY_REQUEST:
        logger.info('TAXII message with id [%s] was not Discovery request [%s]', make_safe(taxii_message.message_id), make_safe(taxii_message.message_type))
        m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type=tm.ST_FAILURE, message='Message sent to discovery service did not have a discovery request message type')
        return handlers.create_taxii_response(m, use_https=request.is_secure())

    resp = handlers.discovery_get_services(request, taxii_message)
    return resp
