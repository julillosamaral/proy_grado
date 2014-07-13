from django.shortcuts import render
import logging
import StringIO
from taxii.models import Inbox, RemoteInbox, DataFeed, RemoteDataFeed, MessageBindingId, ContentBindingId, ContentBlock, ProtocolBindingId, DataFeedPushMethod, DataFeedPollInformation,RemoteDataFeedPollInformation, DataFeedSubscriptionMethod, DataFeedSubscription, ContentBlockRTIR
from rest_framework.response import Response
from rest_framework import viewsets
from taxii.serializers import UserSerializer, GroupSerializer, InboxSerializer, RemoteInboxSerializer, DataFeedSerializer, RemoteDataFeedSerializer, MessageBindingIdSerializer, ContentBindingIdSerializer, ContentBlockSerializer, ProtocolBindingIdSerializer, DataFeedPushMethodSerializer, DataFeedPollInformationSerializer, RemoteDataFeedPollInformationSerializer, DataFeedSubscriptionMethodSerializer, DataFeedSubscriptionSerializer, ContentBlockRTIRSerializer
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
from tasks import poll_request, envio_informacion
from urlparse import urlparse


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
            logger.debug('Retorno el nuevo objeto creado')
            return Response(serializerRT.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#ESTE YA LO TENGO DE LO CREADO AL PRINCIPIO.
#@api_view(['GET','POST'])
#def listar_data_feeds(request):

#ESTE TENGO QUE VER COMO CARAJO LO HAGO
#@api_view(['GET','POST'])
#def subscripcion_data_feed(request):

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


#@api_view(['GET','POST'])
#def alta_servicios(request):


#@api_view(['GET','POST'])
#def listado_servicios(request):


#@api_view(['GET','POST'])
#def baja_servicios(request):


#@api_view(['GET','POST'])
#def obtener_info_servicios(request):


#@api_view(['GET','POST'])
#def modificar_servicios(request):

#Casos de uso de subscribirse a data feeds en otros clientes

