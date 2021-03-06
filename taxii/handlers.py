import datetime
from dateutil.tz import tzutc
import logging

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from stix.core import STIXPackage

import libtaxii as t
import libtaxii.messages as tm
from taxii.models import Inbox, DataFeed, ContentBlock, ContentBindingId, \
    ContentBlockRTIR, MessageBindingId, ProtocolBindingId, DataFeedSubscriptionMethod, DataFeedSubscription
import taxii.settings as s
from taxii.utils import make_safe
from django.utils import timezone

# A set of headers that are utilized by TAXII. These are formatted as Django's
# HttpRequest.META keys: https://docs.djangoproject.com/en/dev/ref/request-response/#django.http.HttpRequest.REQUEST
DJANGO_HTTP_HEADER_CONTENT_TYPE         = 'CONTENT_TYPE'
DJANGO_HTTP_HEADER_ACCEPT               = 'HTTP_ACCEPT'
DJANGO_HTTP_HEADER_X_TAXII_CONTENT_TYPE = 'HTTP_X_TAXII_CONTENT_TYPE'
DJANGO_HTTP_HEADER_X_TAXII_PROTOCOL     = 'HTTP_X_TAXII_PROTOCOL'
DJANGO_HTTP_HEADER_X_TAXII_ACCEPT       = 'HTTP_X_TAXII_ACCEPT'
DJANGO_HTTP_HEADER_X_TAXII_SERVICES     = 'HTTP_X_TAXII_SERVICES'

# A list of request headers that are required by TAXII
DICT_REQUIRED_TAXII_HTTP_HEADERS = (DJANGO_HTTP_HEADER_CONTENT_TYPE,
                                    DJANGO_HTTP_HEADER_X_TAXII_CONTENT_TYPE,
                                    DJANGO_HTTP_HEADER_X_TAXII_PROTOCOL)

#For each TAXII Header that may appear in a request, a list of the values this application supports
DICT_TAXII_HTTP_HEADER_VALUES = {DJANGO_HTTP_HEADER_ACCEPT: ['application/xml'],
                                 DJANGO_HTTP_HEADER_CONTENT_TYPE: ['application/xml'],
                                 DJANGO_HTTP_HEADER_X_TAXII_CONTENT_TYPE: [t.VID_TAXII_XML_10],
                                 DJANGO_HTTP_HEADER_X_TAXII_PROTOCOL: [t.VID_TAXII_HTTPS_10, t.VID_TAXII_HTTP_10]}

# A set of headers that are utilized by TAXII. These are formatted using HTTP header conventions
HTTP_HEADER_CONTENT_TYPE            = 'Content-Type'
HTTP_HEADER_ACCEPT                  = 'Accept'
HTTP_HEADER_X_TAXII_CONTENT_TYPE    = 'X-TAXII-Content-Type'
HTTP_HEADER_X_TAXII_PROTOCOL        = 'X-TAXII-Protocol'
HTTP_HEADER_X_TAXII_ACCEPT          = 'X-TAXII-Accept'
HTTP_HEADER_X_TAXII_SERVICES        = 'X-TAXII-Services'

# Dictionary for mapping Django's HttpRequest.META headers to actual HTTP headers
DICT_REVERSE_DJANGO_NORMALIZATION = {DJANGO_HTTP_HEADER_CONTENT_TYPE: HTTP_HEADER_CONTENT_TYPE,
                                     DJANGO_HTTP_HEADER_X_TAXII_CONTENT_TYPE: HTTP_HEADER_X_TAXII_CONTENT_TYPE,
                                     DJANGO_HTTP_HEADER_X_TAXII_PROTOCOL: HTTP_HEADER_X_TAXII_PROTOCOL,
                                     DJANGO_HTTP_HEADER_ACCEPT: HTTP_HEADER_ACCEPT}

# TAXII Services Version ID
TAXII_VERSION_ID = "urn:taxii.mitre.org:services:1.0"

# TAXII Protocol IDs
TAXII_PROTO_HTTP_BINDING_ID     = "urn:taxii.mitre.org:protocol:http:1.0"
TAXII_PROTO_HTTPS_BINDING_ID    = "urn:taxii.mitre.org:protocol:https:1.0"

# TAXII Message Binding IDs
TAXII_MESSAGE_XML_BINDING_ID    = "urn:taxii.mitre.org:message:xml:1.0"

# HTTP status codes
HTTP_STATUS_OK              = 200
HTTP_STATUS_SERVER_ERROR    = 500
HTTP_STATUS_NOT_FOUND       = 400

def create_taxii_response(message, status_code=HTTP_STATUS_OK, use_https=True):
    """Creates a TAXII HTTP Response for a given message and status code"""
    resp = HttpResponse()
    resp.content = message.to_xml()
    set_taxii_headers_response(resp, use_https)
    resp.status_code = status_code
    return resp

def set_taxii_headers_response(response, use_https):
    """Sets the TAXII HTTP Headers for a given HTTP response"""
    response[HTTP_HEADER_CONTENT_TYPE] = 'application/xml'
    response[HTTP_HEADER_X_TAXII_CONTENT_TYPE] = t.VID_TAXII_XML_10
    protocol = t.VID_TAXII_HTTPS_10 if use_https else t.VID_TAXII_HTTP_10
    response[HTTP_HEADER_X_TAXII_PROTOCOL] = protocol
    return response

def validate_taxii_headers(request, request_message_id):
    """
    Validates TAXII headers. It returns a response containing a TAXII
    status message if the headers were not valid. It returns None if
    the headers are valid.
    """
    logger = logging.getLogger("taxii.utils.handlers.validate_taxii_headers")
    # Make sure the required headers are present
    logger.debug("TAXII headers are going to be validated")
    missing_required_headers = set(DICT_REQUIRED_TAXII_HTTP_HEADERS).difference(set(request.META))
    if missing_required_headers:
        logger.debug("MIssing required headers")
        required_headers = ', '.join(DICT_REVERSE_DJANGO_NORMALIZATION[x] for x in missing_required_headers)
        msg = "Required headers not present: [%s]" % (required_headers)
        m = tm.StatusMessage(tm.generate_message_id(), request_message_id, status_type=tm.ST_FAILURE, message=msg)
        return create_taxii_response(m, use_https=request.is_secure())

    #For headers that exist, make sure the values are supported
    for header in DICT_TAXII_HTTP_HEADER_VALUES:
        if header not in request.META:
            continue

        header_value = request.META[header]
        supported_values = DICT_TAXII_HTTP_HEADER_VALUES[header]

        if header_value not in supported_values:
            logger.debug("A header value is not supported [%s]", header_value)
            msg = 'The value of %s is not supported. Supported values are %s' % (DICT_REVERSE_DJANGO_NORMALIZATION[header], supported_values)
            m = tm.StatusMessage(tm.generate_message_id(), request_message_id, status_type=tm.ST_FAILURE, message=msg)
            return create_taxii_response(m, use_https=request.is_secure())

    # Check to make sure the specified protocol matches the protocol used
    if request.META[DJANGO_HTTP_HEADER_X_TAXII_PROTOCOL] == t.VID_TAXII_HTTPS_10:
        header_proto = 'HTTPS'
    elif request.META[DJANGO_HTTP_HEADER_X_TAXII_PROTOCOL] == t.VID_TAXII_HTTP_10:
        header_proto = 'HTTP'
    else:
        header_proto = 'unknown'

    request_proto = 'HTTPS' if request.is_secure() else 'HTTP' # Did the request come over HTTP or HTTPS?

    if header_proto != request_proto:
        msg = 'Protocol value incorrect. TAXII header specified %s but was sent over %s' % (header_proto, request_proto)
        m = tm.StatusMessage(tm.generate_message_id(), request_message_id, status_type=tm.ST_FAILURE, message=msg)
        return create_taxii_response(m, use_https=request.is_secure())

    # At this point, the header values are known to be good.
    return None

def validate_taxii_request(request):
    """Validates the broader request parameters and request type for a TAXII exchange"""
    logger = logging.getLogger("taxii.utils.handlers.validate_taxii_request")
    logger.debug('Attempting to validate request')

    if request.method != 'POST':
        logger.info('Request was not POST - returning error')
        m = tm.StatusMessage(tm.generate_message_id(), '0', status_type=tm.ST_FAILURE, message='Request must be POST')
        return create_taxii_response(m, use_https=request.is_secure())

    header_validation_resp = validate_taxii_headers(request, '0') # TODO: What to use for request message id?
    logger.info('Validating header [%s]', header_validation_resp)
    if header_validation_resp: # If response is not None an validation of the TAXII headers failed
        logger.info('TAXII header validation failed.')
        return header_validation_resp

    if len(request.body) == 0:
        m = tm.StatusMessage(tm.generate_message_id(), '0', status_type=tm.ST_FAILURE, message='No POST data')
        logger.info('Request had a body length of 0. Returning error.')
        return create_taxii_response(m, use_https=request.is_secure())

    logger.debug('Request was valid')
    return None

def create_RTIR_ticket(stix_package):
    """ Creates a RTIR ticket with the title in the parameter """
    logger = logging.getLogger('taxii.utils.handlers.create_RTIR_ticket')
    logger.debug('Create new RTIR ticket')

    url = s.RTIR_URL
    user_login = s.RTIR_USER
    user_password = s.RTIR_PASSWORD

    tracker = rt.Rt(url, user_login, user_password)
    if tracker.login():
        logger.debug(stix_package.stix_header.title)
        ticket_id = tracker.create_ticket(Queue = 'General', Subject=stix_package.stix_header.title, Text='ticket_text - 20140315 eclipse julio jj')
        logger.debug('New RTIR Ticket created')
        if ticket_id == -1 :
            raise Exception("It was not possible to create the ticket in RTIR.")
        else :
            return ticket_id
    else:
        logger.error('There was an error login into RTIR')


def inbox_add_content(request, inbox_name, taxii_message):
    """Adds content to inbox and associated data feeds"""
    logger = logging.getLogger('taxii.utils.handlers.inbox_add_content')
    logger.debug('Adding content to inbox [%s]', make_safe(inbox_name))

    try:
        inbox = Inbox.objects.get(name=inbox_name)
    except:
        logger.debug('Attempting to push content to unknown inbox [%s]', make_safe(inbox_name))
        m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type=tm.ST_NOT_FOUND, message='Inbox does not exist [%s]' % (make_safe(inbox_name)))
        return create_taxii_response(m, use_https=request.is_secure())

    logger.debug('TAXII message [%s] contains [%d] content blocks', make_safe(taxii_message.message_id), len(taxii_message.content_blocks))

    datafeed = taxii_message.subscription_information.collection_name
    
    for content_block in taxii_message.content_blocks:
        try:
            content_binding_id = ContentBindingId.objects.filter(binding_id=content_block.content_binding)
        except:
            logger.debug('TAXII message [%s] contained unrecognized content binding [%s]', make_safe(taxii_message.message_id), make_safe(content_block.content_binding))
            continue # cannot proceed - move on to the next content block

        if content_binding_id[0] not in inbox.supported_content_bindings.all():
            logger.debug('Inbox [%s] does not accept content with binding id [%s]', make_safe(inbox_name), make_safe(content_block.content_binding))
        else:

            tree = etree.parse(c.content)

            import stix.bindings.stix_core as stix_core_binding
            stix_package_obj = stix_core_binding.STIXType().factory()
            stix_package_obj.build(tree.getroot())

            from stix.core import STIXPackage # resolve circular dependencies
            stix_package = STIXPackage().from_obj(stix_package_obj)
            
            info = ContentBlock.objects.filter(stix_id = stix_package._id)
            if info.exists():

                c = ContentBlock()
                c.origen = datafeed
                c.message_id = taxii_message.message_id
                c.content_binding = content_binding_id[0]
                c.content = content_block.content
                if content_block.padding:
                    c.padding = content_block.padding

                if request.user.is_authenticated():
                    c.submitted_by = request.user

                c.save()
                inbox.content_blocks.add(c) # add content block to inbox

                for data_feed in inbox.data_feeds.all():
                    if content_binding_id[0] in data_feed.supported_content_bindings.all():
                        data_feed.content_blocks.add(c)
                        data_feed.save()
                    else:
                        logger.debug('Inbox [%s] received data using content binding [%s] - '
                                 'associated data feed [%s] does not support this binding.',
                                 make_safe(inbox_name), make_safe(content_block.content_binding), make_safe(data_feed.name))

    inbox.save()
    m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type = tm.ST_SUCCESS)
    return create_taxii_response(m, use_https=request.is_secure())

def get_message_bindings(message_bindings):
    """ Returns the list of Message Bindings """
    logger = logging.getLogger('taxii.utils.handlers.feed_mangment_get_content')
    logger.debug('Retriving data feed names')
    list_msg_bindings = []
    for msg in message_bindings.all():
        logger.debug(msg.title)
        list_msg_bindings.append(msg.title)
    return list_msg_bindings


def feed_managment_get_content(request, taxii_message):
    """Returns a feed managment response for a given Poll Request Message"""
    logger = logging.getLogger('taxii.utils.handlers.feed_mangment_get_content')
    logger.debug('Retriving data feed names')

    data_feeds = DataFeed.objects.all()

    feed_information_list = []
    for data_feed in data_feeds:

        push_methods = []
        polling_service_instances = []
        subscription_methods = []
        supported_content_bindings = []

        for subs_method in data_feed.subscription_methods.all():
            subscription_method = tm.FeedInformationResponse.FeedInformation.SubscriptionMethod(subscription_protocol=subs_method.protocol_binding.title,
                                                                                                subscription_address=subs_method.title,
                                                                                                subscription_message_bindings=get_message_bindings(subs_method.message_bindings))
            subscription_methods.append(subscription_method)

        for poll_service_instance in data_feed.poll_service_instances.all():
            poll_service = tm.FeedInformationResponse.FeedInformation.PollingServiceInstance(poll_protocol=poll_service_instance.address,
                                                                                            poll_address=poll_service_instance.address,
                                                                                            poll_message_bindings=get_message_bindings(poll_service_instance.message_bindings))
            polling_service_instances.append(poll_service)

        for push_method in data_feed.push_methods.all():
            push_me = tm.FeedInformationResponse.FeedInformation.PushMethod(push_protocol=push_method.protocol_binding.title,
                    push_message_bindings=[push_method.message_binding.title])
            push_methods.append(push_me)

        for supported_content_binding in data_feed.supported_content_bindings.all():
            sup_cont_bind = supported_content_binding.title
            supported_content_bindings.append(sup_cont_bind)

        feed = tm.FeedInformationResponse.FeedInformation(feed_name = data_feed.name,
                                                        feed_description = data_feed.description,
                                                        supported_contents=supported_content_bindings,
                                                        available=True,
                                                        push_methods=push_methods,
                                                        polling_service_instances=polling_service_instances,
                                                        subscription_methods=subscription_methods)
        feed_information_list.append(feed)

    feed_managment_response_message = tm.FeedInformationResponse(tm.generate_message_id(),
                                                                taxii_message.message_id,
                                                                feed_informations=feed_information_list)

    return create_taxii_response(feed_managment_response_message, use_https=request.is_secure())


def feed_subscription_get_content(request, taxii_message):
    """Returns a feed subscription response for a given subscription feed  Message"""
    logger = logging.getLogger('taxii.utils.handlers.feed_subscription_get_content')
    logger.debug('Retriving data feed names')


    f = tm.ACT_TYPES
    #For now we only accept subscriptions
    if taxii_message.action == f[0]:

        try:
            logger.debug('Getting the data feed [%s]', make_safe(taxii_message.feed_name))
            data_feed = DataFeed.objects.get(name=taxii_message.feed_name)
        except:
            logger.debug('Attempting to subscribe to unknown data feed [%s]', make_safe(taxii_message.feed_name))
            m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type=tm.ST_NOT_FOUND, message='Data feed does not exist [%s]' % (make_safe(taxii_message.feed_name)))
            return create_taxii_response(m, use_https=request.is_secure())

        try:
            binding_id = taxii_message.delivery_parameters.inbox_protocol
            logger.debug('Getting the binding protocol [%s]', make_safe(binding_id))
            protocol_binding = ProtocolBindingId.objects.get(title=binding_id)
            message_binding = taxii_message.delivery_parameters.delivery_message_binding
            logger.debug('Getting the binding message [%s]', make_safe(message_binding))
            message_binding = MessageBindingId.objects.get(title=message_binding)
        except:
            logger.debug('Attempting to subscribe to use unknowon protocol or message bindings')
            m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type=tm.ST_NOT_FOUND, message='Protocol or message bindings does not exist')
            return create_taxii_response(m, use_https=request.is_secure())

        logger.debug("Response message")
        subscr_methods = DataFeedSubscriptionMethod()
        subscr_methods.title = taxii_message.delivery_parameters.inbox_address
        subscr_methods.description = taxii_message.delivery_parameters.inbox_address
        subscr_methods.address = taxii_message.delivery_parameters.inbox_address
        subscr_methods.protocol_binding = protocol_binding

        subscr_methods.save()
        subscr_methods.message_bindings.add(message_binding)
        subscr_methods.save()

        logger.debug("The information was correclty saved")

        user = User.objects.get(id=1)
        logger.debug("Get user")
        data_feed_subscription = DataFeedSubscription()
        data_feed_subscription.active = True
        data_feed_subscription.expires = timezone.now() + datetime.timedelta(days=500)
        data_feed_subscription.data_feed_method = subscr_methods
        data_feed_subscription.data_feed = data_feed
        data_feed_subscription.user = user

        subscription_list = DataFeedSubscription.objects.all()
        if len(subscription_list) == 0:
                id_value = 1
        else:
                id_value = DataFeedSubscription.objects.latest('id').id + 1

        data_feed_subscription.subscription_id = id_value
        data_feed_subscription.save()

        delivery_parameters = tm.DeliveryParameters(inbox_protocol=taxii_message.delivery_parameters.inbox_protocol,
                                inbox_address=taxii_message.delivery_parameters.inbox_address,
                                delivery_message_binding=taxii_message.delivery_parameters.delivery_message_binding,
                                content_bindings=taxii_message.delivery_parameters.content_bindings)

        logger.debug("Return the Poll Service instances")
        poll_instances = []
        for poll_info in data_feed.poll_service_instances.all():
            poll_inst = tm.ManageFeedSubscriptionResponse.PollInstance(poll_protocol = poll_info.protocol_binding.binding_id,
                        poll_address = poll_info.address)

            mbindings = []
            for mbinding_id in poll_info.message_bindings.all():
                mbindings.append(mbinding_id.binding_id)

            poll_inst.poll_message_bindings = mbindings

            poll_instances.append(poll_inst)

        subscription_instances = []

        subscr_instance = tm.ManageFeedSubscriptionResponse.SubscriptionInstance(subscription_id = str(data_feed_subscription.id))
        subscr_instance.delivery_parameters = [delivery_parameters]
        subscr_instance.poll_instances = poll_instances

        subscription_instances.append(subscr_instance)
        logger.debug("Returns the response")
        feed_subscription_response_message = tm.ManageFeedSubscriptionResponse(message_id = tm.generate_message_id(), in_response_to = taxii_message.message_id,
                feed_name = taxii_message.feed_name, message='Subscription succeds', subscription_instances = subscription_instances)

        return create_taxii_response(feed_subscription_response_message, use_https=request.is_secure())
    else:
        logger.debug('Modifing or deleteing subscription is not supported')
        m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type=tm.ST_FAILURE, message='Modifing subscriptions is not allowed')
        return create_taxii_response(m, use_https=request.is_secure())


def poll_get_content(request, taxii_message):
    """Returns a Poll response for a given Poll Request Message"""
    logger = logging.getLogger('taxii.utils.handlers.poll_get_content')
    logger.debug('Polling data from data feed [%s] - begin_ts: %s, end_ts: %s', taxii_message.collection_name,
                taxii_message.exclusive_begin_timestamp_label, taxii_message.inclusive_end_timestamp_label)

    try:
        data_feed = DataFeed.objects.get(name=taxii_message.collection_name)
    except:
        logger.debug('Attempting to poll unknown data feed [%s]', make_safe(taxii_message.collection_name))
        m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type=tm.ST_NOT_FOUND, message='Data feed does not exist [%s]' % (make_safe(taxii_message.collection_name)))
        return create_taxii_response(m, use_https=request.is_secure())

    # build query for poll results
    query_params = {}
    if taxii_message.exclusive_begin_timestamp_label:
        query_params['timestamp_label__gt'] = taxii_message.exclusive_begin_timestamp_label

    current_datetime = datetime.datetime.now(tzutc())
    if taxii_message.inclusive_end_timestamp_label and (taxii_message.inclusive_end_timestamp_label < current_datetime):
        query_params['timestamp_label__lte'] = taxii_message.inclusive_end_timestamp_label
    else:
        query_params['timestamp_label__lte'] = current_datetime

    content_blocks = data_feed.content_blocks.filter(**query_params).order_by('timestamp_label')
    logger.debug('Returned [%d] content blocks from data feed [%s]', len(content_blocks), make_safe(data_feed.name))

    # TAXII Poll Requests have exclusive begin timestamp label fields, while Poll Responses
    # have *inclusive* begin timestamp label fields. To satisfy this, we add one millisecond
    # to the Poll Request's begin timestamp label.
    #
    # This will be addressed in future versions of TAXII
    inclusive_begin_ts = None
    if taxii_message.exclusive_begin_timestamp_label:
        inclusive_begin_ts = taxii_message.exclusive_begin_timestamp_label + datetime.timedelta(milliseconds=1)

    # build poll response
    poll_response_message = tm.PollResponse(tm.generate_message_id(),
                                            taxii_message.message_id,
                                            feed_name=data_feed.name,
                                            inclusive_begin_timestamp_label=inclusive_begin_ts,
                                            inclusive_end_timestamp_label=query_params['timestamp_label__lte'])

    for content_block in content_blocks:
        cb = tm.ContentBlock(content_block.content_binding.binding_id, content_block.content, content_block.timestamp_label)

        if content_block.padding:
            cb.padding = content_block.padding

        poll_response_message.content_blocks.append(cb)

    return create_taxii_response(poll_response_message, use_https=request.is_secure())

def discovery_get_services(request, taxii_message):
    """Returns a Discovery response for a given Discovery Request Message"""
    logger = logging.getLogger('taxii.utils.handlers.discovery_get_services')
    all_services = []

    # Inbox Services
    for inbox in Inbox.objects.all():
        service_type = tm.SVC_INBOX
        inbox_name  = inbox.name
        service_addr   = request.build_absolute_uri(reverse('taxii.views.inbox_service', args=[inbox_name]))
        proto_binding = TAXII_PROTO_HTTP_BINDING_ID
        message_bindings = [x.binding_id for x in inbox.supported_message_bindings.all()]
        content_bindings = [x.binding_id for x in inbox.supported_content_bindings.all()]
        available = True # TODO: this should reflect whether or not the user has access to this inbox

        service_instance = tm.DiscoveryResponse.ServiceInstance(service_type=service_type,
                                                                services_version=TAXII_VERSION_ID,
                                                                protocol_binding=proto_binding,
                                                                service_address=service_addr,
                                                                message_bindings=message_bindings,
                                                                inbox_service_accepted_content=content_bindings,
                                                                available=available)
        all_services.append(service_instance)

    # Poll Service
    all_data_feeds = DataFeed.objects.all()
    if all_data_feeds:
        all_data_feed_msg_bindings = set()
        for data_feed in all_data_feeds:
            poll_svc_instances = data_feed.poll_service_instances.all()

            for poll_svc_instance in poll_svc_instances:
                message_bindings = [x.binding_id for x in poll_svc_instance.message_bindings.all()]
                all_data_feed_msg_bindings.update(message_bindings)


        service_instance = tm.DiscoveryResponse.ServiceInstance(service_type=tm.SVC_POLL,
                                                                services_version=TAXII_VERSION_ID,
                                                                protocol_binding=TAXII_PROTO_HTTP_BINDING_ID,
                                                                service_address=request.build_absolute_uri(reverse('taxii.views.poll_service')),
                                                                message_bindings=all_data_feed_msg_bindings,
                                                                available=True)
        all_services.append(service_instance)


    # Discovery Service
    service_instance = tm.DiscoveryResponse.ServiceInstance(service_type=tm.SVC_DISCOVERY,
                                                            services_version=TAXII_VERSION_ID,
                                                            protocol_binding=TAXII_PROTO_HTTP_BINDING_ID,
                                                            service_address=request.build_absolute_uri(reverse('taxii.views.discovery_service')),
                                                            message_bindings=[TAXII_MESSAGE_XML_BINDING_ID],
                                                            available=True)
    all_services.append(service_instance)
    logger.debug('Returning [%s] services', len(all_services))

    # Build response
    discovery_response_message = tm.DiscoveryResponse(message_id=tm.generate_message_id(),
                                                      in_response_to=taxii_message.message_id,
                                                      service_instances=all_services)

    return create_taxii_response(discovery_response_message, use_https=request.is_secure())

