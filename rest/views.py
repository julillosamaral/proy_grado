from django.shortcuts import render
import logging
import StringIO
from taxii.models import Inbox, RemoteInbox, DataFeed, RemoteDataFeed, MessageBindingId, ContentBindingId, ContentBlock, ProtocolBindingId, DataFeedPushMethod, DataFeedPollInformation,RemoteDataFeedPollInformation, DataFeedSubscriptionMethod, DataFeedSubscription, ContentBlockRTIR, TAXIIServices
from rest_framework.response import Response
from rest_framework import viewsets
from taxii.serializers import UserSerializer, GroupSerializer, InboxSerializer, RemoteInboxSerializer, DataFeedSerializer, RemoteDataFeedSerializer, MessageBindingIdSerializer, ContentBindingIdSerializer, ContentBlockSerializer, ProtocolBindingIdSerializer, DataFeedPushMethodSerializer, DataFeedPollInformationSerializer, RemoteDataFeedPollInformationSerializer, DataFeedSubscriptionMethodSerializer, DataFeedSubscriptionSerializer, ContentBlockRTIRSerializer, TAXIIServicesSerializer
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
from tasks import poll_request, envio_informacion as envio_info_task
from urlparse import urlparse
import libtaxii.messages as tm
import libtaxii.clients as tc
import libtaxii as t
import json
from django.http import HttpResponse


INBOX_SERVICES_URL= "http://192.168.0.103:8000/services/inbox"


class UserViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates users.
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ProtocolBindingIdViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates ProtocolBindingIds
    queryset = ProtocolBindingId.objects.all()
    serializer_class = ProtocolBindingIdSerializer

class ContentBindingIdViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates ContentBindingIds
    queryset = ContentBindingId.objects.all()
    serializer_class = ContentBindingIdSerializer

class MessageBindingIdViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates MessageBindingIds
    queryset = MessageBindingId.objects.all()
    serializer_class = MessageBindingIdSerializer

class DataFeedPushMethodViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates DataFeedPushMethods
    queryset = DataFeedPushMethod.objects.all()
    serializer_class = DataFeedPushMethodSerializer

class DataFeedPollInformationViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates DataFeedPollInformations
    queryset = DataFeedPollInformation.objects.all()
    serializer_class = DataFeedPollInformationSerializer

class RemoteDataFeedPollInformationViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates RemoteDataFeedPollInformations
    queryset = RemoteDataFeedPollInformation.objects.all()
    serializer_class = RemoteDataFeedPollInformationSerializer

class DataFeedSubscriptionMethodViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates DataFeedSubscriptionMethods
    queryset = DataFeedSubscriptionMethod.objects.all()
    serializer_class = DataFeedSubscriptionMethodSerializer

class ContentBlockViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates ContentBlocks
    queryset = ContentBlock.objects.all()
    serializer_class = ContentBlockSerializer

class DataFeedViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates DataFeeds
    queryset = DataFeed.objects.all()
    serializer_class = DataFeedSerializer

class RemoteDataFeedViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates RemoteDataFeeds
    queryset = RemoteDataFeed.objects.all()
    serializer_class = RemoteDataFeedSerializer

class DataFeedSubscriptionViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates SubscriptionFeeds
    queryset = DataFeedSubscription.objects.all()
    serializer_class = DataFeedSubscriptionSerializer

class InboxViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates Inboxes
    queryset = Inbox.objects.all()
    serializer_class = InboxSerializer

class RemoteInboxViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates RemoteInboxes
    queryset = RemoteInbox.objects.all()
    serializer_class = RemoteInboxSerializer

class ContentBlockRTIRViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates ContentBlockRTIRs
    queryset = ContentBlockRTIR.objects.all()
    serializer_class = ContentBlockRTIRSerializer

class TAXIIServicesViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates TAXIIServices
    queryset = TAXIIServices.objects.all()
    serializer_class = TAXIIServicesSerializer

class FeedManagmentServicesViewSet(viewsets.ModelViewSet):
    #Gets, lists, creates or updates FeedManagementServices
    queryset = TAXIIServices.objects.exclude(feed_managment__isnull=True).exclude(feed_managment__exact='')
    serializer_class = TAXIIServicesSerializer

@api_view(['GET', 'POST'])
def obtener_remote_data_feeds(request):
    #Given the id of a TAXII Service we make a FeedInformation request to that service address.
    #The response is a list of the feed names of the TAXII client and a list of all protocol bindings, content binding and message binding.
    feed_managment = TAXIIServices.objects.get(id = request.DATA.get('id'))
    urlParsed = urlparse(feed_managment.feed_managment)

    logger = logging.getLogger('TAXIIApplication.rest.tasks.obtener_remote_data_feeds')

    logger.debug('We get the server data feeds')
    logger.debug('Host: ' + urlParsed.hostname)
    logger.debug('Path: ' + urlParsed.path)
    logger.debug('Port: ' + str(urlParsed.port))

    host = urlParsed.hostname
    path = urlParsed.path
    port = str(urlParsed.port)

    feed_information = tm.FeedInformationRequest(message_id=tm.generate_message_id())
    feed_info_xml = feed_information.to_xml()
    logger.debug('The following message is sent: ' + feed_info_xml)
    client = tc.HttpClient()
    resp = client.callTaxiiService2(host, path, t.VID_TAXII_XML_10, feed_info_xml, port)

    response_message = t.get_message_from_http_response(resp, '0')
    logger.debug("The response was: " + response_message.to_xml())
    try:
        taxii_message = tm.get_message_from_xml(response_message.to_xml())

        logger.debug("The JSON is: " + taxii_message.to_json())

        feed_informations = taxii_message.feed_informations

        feed_names = []
        for feed in feed_informations:
            feed_names.append({"name" : feed.feed_name})

        protocolBindings = ProtocolBindingId.objects.all()
        protocol_bindings = []
        for proto in protocolBindings:
            protocol_bindings.append({"binding_id" : proto.binding_id})

        contentBindings = ContentBindingId.objects.all()
        content_bindings = []
        for content in contentBindings:
            content_bindings.append({"binding_id" : content.binding_id})

        messageBindings = MessageBindingId.objects.all()
        message_bindings = []
        for message in messageBindings:
            message_bindings.append({"binding_id" : message.binding_id})

        json_data = json.dumps({ "items" : feed_names, "protocol_bindings" : protocol_bindings, "content_bindings" : content_bindings, "message_bindings" : message_bindings })

        logger.debug("The response is the following JSON: " + json_data)
        return HttpResponse(json_data, content_type="application/json")
    except Exception as ex:
        logger.debug('The message could not be parsed:s', ex.message)



@api_view(['GET', 'POST'])
def registrar_remote_data_feeds(request):
    #Given the id of a TAXII service we get the data feeds of the TAXII Client and copy them to the current system.
    feed_managment = TAXIIServices.objects.get(id = request.DATA.get('id'))
    urlParsed = urlparse(feed_managment.feed_managment)

    logger = logging.getLogger('TAXIIApplication.rest.tasks.obtener_remote_data_feeds')

    logger.debug('We get the server data feeds')
    logger.debug('Host: ' + urlParsed.hostname)
    logger.debug('Path: ' + urlParsed.path)
    logger.debug('Port: ' + str(urlParsed.port))

    host = urlParsed.hostname
    path = urlParsed.path
    port = str(urlParsed.port)

    feed_information = tm.FeedInformationRequest(message_id=tm.generate_message_id())
    feed_info_xml = feed_information.to_xml()
    logger.debug('The following message is sent: ' + feed_info_xml)
    client = tc.HttpClient()
    resp = client.callTaxiiService2(host, path, t.VID_TAXII_XML_10, feed_info_xml, port)

    response_message = t.get_message_from_http_response(resp, '0')
    logger.debug("The response was: " + response_message.to_xml())
    try:
        taxii_message = tm.get_message_from_xml(response_message.to_xml())

        logger.debug("Feed Information iteration")
        feed_informations = taxii_message.feed_informations
        for feed in feed_informations:
            logger.debug("Create a new Remote Data Feed")
            remote_df = RemoteDataFeed()
            remote_df.name = feed.feed_name
            logger.debug(feed.feed_name)
            if feed.feed_description == None:
                remote_df.description = "None"
            else:
                remote_df.description = feed.feed_description

            remote_df.save()
            i = 0
            logger.debug('We get the subscription methods')
            for sm in feed.subscription_methods:
                protocol_binding = ProtocolBindingId(binding_id = sm.subscription_protocol)
                protocol_binding.save()

                dfsm = DataFeedSubscriptionMethod()
                dfsm.title = feed.feed_name + "_"+str(i)
                dfsm.address = sm.subscription_address
                dfsm.protocol_binding=protocol_binding

                dfsm.save()
                for mb in sm.subscription_message_bindings:
                    msgb = MessageBindingId(binding_id = mb)
                    msgb.save()
                    dfsm.message_bindings.add(msgb)
                dfsm.save()
                remote_df.subscription_methods.add(dfsm)

            logger.debug('We get the Content Bindings')
            for sc in feed.supported_contents:
                cb = ContentBindingId(binding_id = sc )
                cb.save()
                remote_df.supported_content_bindings.add(cb)

            logger.debug('Obtengo los push methods')
            for pm in feed.push_methods:
                pb = ProtocolBindingId(binding_id = pm.push_protocol)
                pb.save()
                mb = MessageBindingId(binding_id = pm.push_message_bindings)
                mb.save()
                dpm = DataFeedPushMethod(protocol_binding = pb, message_binding = mb)
                dpm.save()

                remote_df.push_methods.add(dpm)


            poll_service_instances = []
            logger.debug('We get the Poll Service Instances')
            for psi in feed.polling_service_instances:

                rdfpi = RemoteDataFeedPollInformation()
                rdfpi.address = psi.poll_address

                pb = ProtocolBindingId(binding_id = psi.poll_protocol)
                pb.save()
                rdfpi.protocol_binding = pb
                rdfpi.save()

                logger.debug(psi.poll_message_bindings)
                for msg in psi.poll_message_bindings:
                    msgb = MessageBindingId(binding_id = msg)
                    msgb.save()
                    rdfpi.message_bindings.add(msgb)
                
                rdfpi.save()
                remote_df.poll_service_instances.add(rdfpi)
            logger.debug("Save the remote data feed")
            remote_df.save()

        return Response(status=status.HTTP_201_CREATED)
    except Exception as ex:
        logger.debug( ex)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
def alta_informacion(request):
    #"""
    #When in GET method return all the Content Blocks.
    #When in POST method, given a content binding id, a title, description and content we create a Content Block.
    #"""
    logger = logging.getLogger('TAXIIApplication.rest.views.alta_informacion')
    logger.debug('Entering alta_informacion')
    logger.debug(request.method)
    if request.method == 'GET':
        content = ContentBlock.objects.all()
        serializer = ContentBlockSerializer(content, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
    	content_binding = ContentBindingId.objects.get(id=request.DATA.get('content_binding'))
    	cb = ContentBlock(title=request.DATA.get('title'), description=request.DATA.get('description') ,content_binding=content_binding, content=request.DATA.get('content'))
    	cb.save()
	return Response(status=status.HTTP_201_CREATED)


@api_view(['POST'])
def envio_informacion(request):
    #Given the id of a DataFeed Subscription we get the Data Feeds for that subscription.
    logger = logging.getLogger('TAXIIApplication.taxii.views.envio_informacion')
    logger.debug('Start the sending of information')
    logger.debug(request.DATA)
    sub_service_id = request.DATA.get('inbox_information')
    logger.debug('El inbox al que voy a mandar es el de id: ' + str(sub_service_id))

    subscription_service = DataFeedSubscription.objects.get(id = sub_service_id)

    urlParsed = urlparse(subscription_service.data_feed_method.address)
    envio_info_task.delay(data_feed = subscription_service.data_feed, host = urlParsed.hostname, path = urlParsed.path, port = urlParsed.port)
    return Response(status = status.HTTP_200_OK)

@api_view(['POST'])
def poll_informacion(request):
    #Given the id of a remote data feed, we get the poll service instances and for each make a poll request.
    logger = logging.getLogger('TAXIIApplication.taxii.views.poll_informacion')
    logger.debug('Start the poll of information')
    logger.debug('Request data is: ')
    logger.debug(request.DATA)

    selected_item = request.DATA.get('id_data_feed')
    data_feed = RemoteDataFeed.objects.get(id = selected_item)
    logger.debug('The data feed gotten is:' + data_feed.name)

    data_feed_poll_info = data_feed.poll_service_instances

    for dfpi in data_feed_poll_info.all():
        urlParsed = urlparse(dfpi.address)

        logger.debug('The conection data are: ' + urlParsed.hostname + ' ' + str(urlParsed.port) + ' ' + urlParsed.path)
        poll_request.delay(collection_name = data_feed.name, subscription_id = '1', host = urlParsed.hostname, path = urlParsed.path, port = urlParsed.port)

    return Response(status = status.HTTP_200_OK)


@api_view(['GET'])
def obtener_data_feed_subscriptions(request):
    #We get all the date feed subsctiptions and return the id, adress and data feed name of each.
    logger = logging.getLogger('TAXIIApplication.taxii.views.obtener_data_feed_subscriptions')
    logger.debug('We get the subscriptions to the data feeds')

    subscriptions = DataFeedSubscription.objects.all()

    subs = []
    for sub in subscriptions:
        subs.append({"id" : sub.id, "address" : sub.data_feed_method.address, "data_feed_name" : sub.data_feed.name})


    json_data = json.dumps({ "items" : subs })
    logger.debug("The JSON to return is:" + json_data)
    return HttpResponse(json_data, content_type="application/json")

@api_view(['POST'])
def subscripcion_data_feed(request):
    #Given the id of a TAXII Service and the id of a Data Feed and the service id we make a Manage Feed Subscription request for that Data Feed.
    logger = logging.getLogger('TAXIIApplication.taxii.views.subscripcion_data_feed')
    logger.debug('The data feed subscription starts')
    logger.debug(request.DATA)

    data_feed = request.DATA.get('data_feed')
    service = request.DATA.get('id')

    inbox_protocol = request.DATA.get('protocol_binding')
    message_binding = request.DATA.get('message_binding')
    content_binding = request.DATA.get('content_binding')

    feed_managment = TAXIIServices.objects.get(id = service)
    urlParsed = urlparse(feed_managment.subscription)

    logger.debug('Host: ' + urlParsed.hostname)
    logger.debug('Path: ' + urlParsed.path)
    logger.debug('Port: ' + str(urlParsed.port))

    host = urlParsed.hostname
    path = urlParsed.path
    port = str(urlParsed.port)

    delivery_parameters = tm.DeliveryParameters(inbox_protocol=inbox_protocol, inbox_address=INBOX_SERVICES_URL,
            delivery_message_binding=message_binding, content_bindings=content_binding)

    f = tm.ACT_TYPES

    feed_subscription = tm.ManageFeedSubscriptionRequest(message_id=tm.generate_message_id(), feed_name=data_feed,
                    action= f[0], subscription_id='1', delivery_parameters=delivery_parameters)
    feed_subscription_xml = feed_subscription.to_xml()

    client = tc.HttpClient()
    resp = client.callTaxiiService2(host, path, t.VID_TAXII_XML_10, feed_subscription_xml, port)
    logger.debug("The server responds")
    return Response(status = status.HTTP_200_OK)
