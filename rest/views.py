from django.shortcuts import render
import logging
import StringIO
from taxii.models import Inbox, DataFeed, MessageBindingId, ContentBindingId, ContentBlock, ProtocolBindingId, DataFeedPushMethod, DataFeedPollInformation, DataFeedSubscriptionMethod, DataFeedSubscription, ContentBlockRTIR, ServerServices, Services
from rest_framework.response import Response
from rest_framework import viewsets
from taxii.serializers import UserSerializer, GroupSerializer, InboxSerializer, DataFeedSerializer, MessageBindingIdSerializer, ContentBindingIdSerializer, ContentBlockSerializer, ProtocolBindingIdSerializer, DataFeedPushMethodSerializer, DataFeedPollInformationSerializer, DataFeedSubscriptionMethodSerializer, DataFeedSubscriptionSerializer, ContentBlockRTIRSerializer, ServerServicesSerializer, ServicesSerializer
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

class DataFeedSubscriptionMethodViewSet(viewsets.ModelViewSet):
    queryset = DataFeedSubscriptionMethod.objects.all()
    serializer_class = DataFeedSubscriptionMethodSerializer

class ContentBlockViewSet(viewsets.ModelViewSet):
    queryset = ContentBlock.objects.all()
    serializer_class = ContentBlockSerializer

class DataFeedViewSet(viewsets.ModelViewSet):
    queryset = DataFeed.objects.all()
    serializer_class = DataFeedSerializer

class DataFeedSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = DataFeedSubscription.objects.all()
    serializer_class = DataFeedSubscriptionSerializer

class InboxViewSet(viewsets.ModelViewSet):
    queryset = Inbox.objects.all()
    serializer_class = InboxSerializer

class ContentBlockRTIRViewSet(viewsets.ModelViewSet):
    queryset = ContentBlockRTIR.objects.all()
    serializer_class = ContentBlockRTIRSerializer

class ServerServicesViewSet(viewsets.ModelViewSet):
    queryset = ServerServices.objects.all()
    serializer_class = ServerServicesSerializer

class ServicesViewSet(viewsets.ModelViewSet):
    queryset = Services.objects.all()
    serializer_class = ServicesSerializer

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
def envio_informacion(request):
    logger = logging.getLogger('TAXIIApplication.taxii.views.envio_informacion')
    logger.debug('Se comienza el envio de informacion')
    envio_informacion.delay(data_feed_id = request.data_feed_id)

@api_view(['POST'])
def poll_informacion(request):

    logger = logging.getLogger('TAXIIApplication.taxii.views.poll_informacion')
    logger.debug('Se comienza el poll de informacion')
    logger.debug('Los datos que llegan al request son: ')
    logger.debug(request.DATA)

    selected_item = request.DATA.get('id_data_feed').split('-')
    data_feed = DataFeed.objects.get(id = selected_item[0])
    logger.debug('El data feed obtenido es:' + data_feed.name)

    subscription_method =  DataFeedSubscriptionMethod.objects.get(id = selected_item[1])
    logger.debug('El subscription method es: ' + subscription_method.title)

    urlParsed = urlparse(subscription_method.address)

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

