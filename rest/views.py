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
from tasks import poll_request, envio_informacion
from urlparse import urlparse
import libtaxii.messages as tm
import libtaxii.clients as tc
import libtaxii as t
import json
from django.http import HttpResponse


INBOX_SERVICES_URL= "http://192.168.0.103:8000/services/inbox"


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ProtocolBindingIdViewSet(viewsets.ModelViewSet):
    queryset = ProtocolBindingId.objects.all()
    serializer_class = ProtocolBindingIdSerializer

class ContentBindingIdViewSet(viewsets.ModelViewSet):
    queryset = ContentBindingId.objects.all()
    serializer_class = ContentBindingIdSerializer

class MessageBindingIdViewSet(viewsets.ModelViewSet):
    queryset = MessageBindingId.objects.all()
    serializer_class = MessageBindingIdSerializer

class DataFeedPushMethodViewSet(viewsets.ModelViewSet):
    queryset = DataFeedPushMethod.objects.all()
    serializer_class = DataFeedPushMethodSerializer

class DataFeedPollInformationViewSet(viewsets.ModelViewSet):
    queryset = DataFeedPollInformation.objects.all()
    serializer_class = DataFeedPollInformationSerializer

class RemoteDataFeedPollInformationViewSet(viewsets.ModelViewSet):
    queryset = RemoteDataFeedPollInformation.objects.all()
    serializer_class = RemoteDataFeedPollInformationSerializer

class DataFeedSubscriptionMethodViewSet(viewsets.ModelViewSet):
    queryset = DataFeedSubscriptionMethod.objects.all()
    serializer_class = DataFeedSubscriptionMethodSerializer

class ContentBlockViewSet(viewsets.ModelViewSet):
    queryset = ContentBlock.objects.all()
    serializer_class = ContentBlockSerializer

class DataFeedViewSet(viewsets.ModelViewSet):
    queryset = DataFeed.objects.all()
    serializer_class = DataFeedSerializer

class RemoteDataFeedViewSet(viewsets.ModelViewSet):
    queryset = RemoteDataFeed.objects.all()
    serializer_class = RemoteDataFeedSerializer

class DataFeedSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = DataFeedSubscription.objects.all()
    serializer_class = DataFeedSubscriptionSerializer

class InboxViewSet(viewsets.ModelViewSet):
    queryset = Inbox.objects.all()
    serializer_class = InboxSerializer

class RemoteInboxViewSet(viewsets.ModelViewSet):
    queryset = RemoteInbox.objects.all()
    serializer_class = RemoteInboxSerializer

class ContentBlockRTIRViewSet(viewsets.ModelViewSet):
    queryset = ContentBlockRTIR.objects.all()
    serializer_class = ContentBlockRTIRSerializer

class TAXIIServicesViewSet(viewsets.ModelViewSet):
    queryset = TAXIIServices.objects.all()
    serializer_class = TAXIIServicesSerializer

class FeedManagmentServicesViewSet(viewsets.ModelViewSet):
    queryset = TAXIIServices.objects.exclude(feed_managment__isnull=True).exclude(feed_managment__exact='')
    serializer_class = TAXIIServicesSerializer

@api_view(['GET', 'POST'])
def obtener_remote_data_feeds(request):

    feed_managment = TAXIIServices.objects.get(id = request.DATA.get('id'))
    urlParsed = urlparse(feed_managment.feed_managment)

    logger = logging.getLogger('TAXIIApplication.rest.tasks.obtener_remote_data_feeds')

    logger.debug('Obtengo los data feeds en el servidor')
    logger.debug('Host: ' + urlParsed.hostname)
    logger.debug('Path: ' + urlParsed.path)
    logger.debug('Port: ' + str(urlParsed.port))

    host = urlParsed.hostname
    path = urlParsed.path
    port = str(urlParsed.port)

    feed_information = tm.FeedInformationRequest(message_id=tm.generate_message_id())
    feed_info_xml = feed_information.to_xml()
    logger.debug('Se envia el siguiente mensaje: ' + feed_info_xml)
    client = tc.HttpClient()
    resp = client.callTaxiiService2(host, path, t.VID_TAXII_XML_10, feed_info_xml, port)

    response_message = t.get_message_from_http_response(resp, '0')
    logger.debug("La respuesta fue: " + response_message.to_xml())
    try:
        taxii_message = tm.get_message_from_xml(response_message.to_xml())

        logger.debug("El json es: " + taxii_message.to_json())

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

        logger.debug("El json que quiero devolver es:" + json_data)
        return HttpResponse(json_data, content_type="application/json")
    except Exception as ex:
        logger.debug('El mensaje no pudo ser parseado:s', ex.message)

@api_view(['GET', 'POST'])
def alta_informacion(request):
    """
    List all snippets, or create a new snippet.
    """
    logger = logging.getLogger('TAXIIApplication.rest.views.alta_informacion')
    logger.debug('Entering Inbox service')
    logger.debug(request.method)
    if request.method == 'GET':
        content = ContentBlock.objects.all()
        serializer = ContentBlockSerializer(content, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = ContentBlockSerializer(data=request.DATA)
        if serializer.is_valid():
            serializer.save()
            logger.debug('Request de rt id' + str(request.DATA.get('rt_id')))
            logger.debug('Taxii id' + str(serializer.data.get('id')))
            taxii_id = serializer.data.get('id')
            rtir_id = request.DATA.get('rt_id')
            logger.debug('Creo el nuevo objeto de ContentBlockRTIR')
            contentB = ContentBlockRTIR(rtir_id = rtir_id, content_block = ContentBlock.objects.get(id=taxii_id))
            logger.debug('Serializo el nuevo objeto creado para que sea devuelto')
            serializerRT = ContentBlockRTIRSerializer(contentB, many = False)
            serializerRT.save()
            logger.debug('Retorno el nuevo objeto creado')
            return Response(serializerRT.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def obtener_data_feeds(request):
    logger = logging.getLogger('TAXIIApplication.taxii.views.obtener_data_feeds')
    logger.debug('Se comienza la obtencion de data feeds')

    url = request.DATA.get('url')
    urlParsed = urlparse(url)

    obtener_data_feeds.delay(urlParsed.hostname, urlParsed.port, urlParsed.path)

@api_view(['POST'])
def envio_informacion(request):
    logger = logging.getLogger('TAXIIApplication.taxii.views.envio_informacion')
    logger.debug('Se comienza el envio de informacion')
    inbox_id = request.DATA.get('id')

    inbox_service = RemoteInbox.objects.get(id = inbox_id)

    urlParsed = urlparse(inbox_service.address)
    envio_informacion.delay(data_feed = inbox_service.data_feed, host = urlparse.hostname, path = urlParsed.path, port = urlParsed.port)

@api_view(['POST'])
def poll_informacion(request):
    logger = logging.getLogger('TAXIIApplication.taxii.views.poll_informacion')
    logger.debug('Se comienza el poll de informacion')
    logger.debug('Los datos que llegan al request son: ')
    logger.debug(request.DATA)

    selected_item = request.DATA.get('id')
    data_feed = RemoteDataFeed.objects.get(id = selected_item)
    logger.debug('El data feed obtenido es:' + data_feed.name)

    data_feed_poll_info = data_feed.poll_service_instance
    urlParsed = urlparse(data_feed_poll_info.address)

    logger.debug('Los datos de conexion son: ' + urlParsed.hostname + ' ' + str(urlParsed.port) + ' ' + urlParsed.path)
    poll_request.delay(collection_name = data_feed.name, subscription_id = '1', host = urlParsed.hostname, path = urlParsed.path, port = urlParsed.port)
    return Response(status = status.HTTP_200_OK)


@api_view(['POST'])
def test(request):
    logger = logging.getLogger('TAXIIApplication.rest.views.test')
    logger.debug('Hice la llamada rest a test')
    logger.debug(request.method)
    data = request.DATA
    logger.debug('TEST' + str(data))
    return Response(status = status.HTTP_200_OK)

@api_view(['POST'])
def subscripcion_data_feed(request):
    logger = logging.getLogger('TAXIIApplication.taxii.views.subscripcion_data_feed')
    logger.debug('Se comienza la subscripcion de data feeds')
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
    logger.debug("Me responde el servidor")
#    response_message = t.get_message_from_http_response(resp, '0')
    return Response(status = status.HTTP_200_OK)
