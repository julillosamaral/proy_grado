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
def registrar_remote_data_feeds(request):
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

        logger.debug("Comiendo a iterar entre los feed informations")
        feed_informations = taxii_message.feed_informations
        for feed in feed_informations:
            logger.debug("Creo nuevo remote data feed")
            remote_df = RemoteDataFeed()
            remote_df.name = feed.feed_name
            logger.debug(feed.feed_name)
            if feed.feed_description == None:
                remote_df.description = "None"
            else:
                remote_df.description = feed.feed_description

            remote_df.save()
            i = 0
            logger.debug('Obtengo los subscription methods')
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

            logger.debug('Obtengo los content bindings')
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
            logger.debug('Obtengo las poll service instances')
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
                logger.debug("Aca agrego")
                rdfpi.save()
                remote_df.poll_service_instances.add(rdfpi)
            logger.debug("Guardo el remote data feed")
            remote_df.save()
            logger.debug("Guarde el remote data feed y voy a insertar otro")

        return Response(status=status.HTTP_201_CREATED)
    except Exception as ex:
        logger.debug( ex)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
def alta_informacion(request):
    """
    List all snippets, or create a new snippet.
    """
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
	#taxii_id = serializer.data.get('id')
	#rtir_id = request.DATA.get('rt_id')
        #logger.debug('Creo el nuevo objeto de ContentBlockRTIR')
        #contentB = ContentBlockRTIR(rtir_id = rtir_id, content_block = ContentBlock.objects.get(id=taxii_id))
        #logger.debug('Serializo el nuevo objeto creado para que sea devuelto')
        #serializerRT = ContentBlockRTIRSerializer(contentB, many = False)
        #serializerRT.save()
        #logger.debug('Retorno el nuevo objeto creado')
	return Response(status=status.HTTP_201_CREATED)


@api_view(['POST'])
def envio_informacion(request):
    logger = logging.getLogger('TAXIIApplication.taxii.views.envio_informacion')
    logger.debug('Se comienza el envio de informacion')
    sub_service_id = request.DATA.get('id')

    subscription_service = DataFeedSubscription.objects.get(id = sub_service_id)

    urlParsed = urlparse(subscription_service.data_feed_subscription.address)
    envio_informacion.delay(data_feed = subscription_service.data_feed.name, host = urlparse.hostname, path = urlParsed.path, port = urlParsed.port)

@api_view(['POST'])
def poll_informacion(request):
    logger = logging.getLogger('TAXIIApplication.taxii.views.poll_informacion')
    logger.debug('Se comienza el poll de informacion')
    logger.debug('Los datos que llegan al request son: ')
    logger.debug(request.DATA)

    selected_item = request.DATA.get('id_data_feed')
    data_feed = RemoteDataFeed.objects.get(id = selected_item)
    logger.debug('El data feed obtenido es:' + data_feed.name)

    data_feed_poll_info = data_feed.poll_service_instances

    for dfpi in data_feed_poll_info.all():
        urlParsed = urlparse(dfpi.address)

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


@api_view(['GET'])
def obtener_data_feed_subscriptions(request):
    logger = logging.getLogger('TAXIIApplication.taxii.views.obtener_data_feed_subscriptions')
    logger.debug('Se obtienen las subscripciones a los data feeds')

    subscriptions = DataFeedSubscription.objects.all()

    subs = []
    for sub in subscriptions:
        subs.append({"id" : sub.id, "address" : sub.data_feed_method.address, "data_feed_name" : sub.data_feed.name})


    json_data = json.dumps({ "items" : subs })
    logger.debug("El json que quiero devolver es:" + json_data)
    return HttpResponse(json_data, content_type="application/json")

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
