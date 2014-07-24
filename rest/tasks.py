from celery.decorators import task
import sys
import libtaxii as t
import libtaxii.messages_11 as tm11
import libtaxii.messages as tm
import libtaxii.clients as tc
import logging
from taxii.models import DataFeedSubscriptionMethod
from urlparse import urlparse

@task()
def poll_request(collection_name, subscription_id, host, path, port):
    logger = logging.getLogger('TAXIIApplication.rest.tasks.poll_request')
    logger.debug('Se comienza el poll de informacion en el sistema')
    logger.debug('Los parametros recibidos son: ')
    logger.debug('Collection Name: ' + collection_name)
    logger.debug('Subscription Id: ' + str(subscription_id))
    logger.debug('Host: ' + str(host))
    logger.debug('Path: ' + path)
    logger.debug('Port: ' + str(port))

    begin_ts = None
    end_ts = None

    poll_req = tm11.PollRequest(message_id = tm11.generate_message_id(),
                                collection_name = collection_name,
                                exclusive_begin_timestamp_label = begin_ts,
                                inclusive_end_timestamp_label = end_ts,
                                subscription_id = subscription_id)

    poll_req_xml = poll_req.to_xml()
    logger.debug('Se genero el siguiente mensaje Poll Request')
    logger.debug('###########################################')
    logger.debug(poll_req_xml)
    logger.debug('###########################################')

    client = tc.HttpClient()
    resp = client.callTaxiiService2(host, path, t.VID_TAXII_XML_10, poll_req_xml, port)
    response_message = t.get_message_from_http_response(resp, '0')

    logger.debug('Se obtuvo la respuesta del sistema origen')
    logger.debug('#########################################')
    logger.debug(response_message.to_xml())
    logger.debug('#########################################')

    try:
        taxii_message = tm.get_message_from_xml(response_message.to_xml())
    except Exception as ex:
        logger.debug('El mensaje no pudo ser parseado:s', ex.message)

    if taxii_message.message_type != tm.MG_POLL_RESPONSE:
        logger.debug('El mensage recibio no es una respuesta TAXII')
    else:
        content_blocks = taxii_message.content_blocks
        logger.debug('Se procesan los content blocks')

        for cb in content_blocks:
            p = ContentBlock()
            p.description = 'Recibido por el inbox service'
            p.message_id = taxii_message.message_id
           #Ver si esta bien lo de abajo
            p.content_binding = taxii_message.content_binding
            p.content = cb
            p.save()

@task()
def envio_informacion(data_feed, host, path, port):
    logger = logging.getLogger('TAXIIApplication.rest.tasks.envio_informacion')
    logger.debug('Obtengo los subscription Methods')
    logger.debug('Los parametros recibidos son: ')
    logger.debug('Host: ' + host)
    logger.debug('Path: ' + path)
    logger.debug('Port: ' + str(port))
    logger.debug('El data feed es id y titulo' + str(data_feed.id) + data_feed.title)

    content_blocks = data_feed.content_blocks

    content = []
    for content_block in content_blocks:
        content.append(content_block.content)

    inbox_message = tm11.InboxMessage(message_id = tm11.generate_message_id(), content_blocks=content)

    inbox_xml = inbox_message.to_xml()
    logger.debug('El mensaje a enviar es: '+ inbox_xml)

    client = tc.HttpClient()
    client.setProxy('noproxy')

    resp = client.callTaxiiService2(hostname, path, t.VID_TAXII_XML_10, inbox_xml, port)
    response_message = t.get_message_from_http_response(resp, '0')
    logger.debug('El mensaje de respuesta fue: ' + response_message)
    #Con la respuesta creo que no hago nada. Queda loggeada nomas

@task()
def obtener_data_feeds(host, port, path):
    logger = logging.getLogger('TAXIIApplication.rest.tasks.obtener_data_feeds')
    logger.debug('Obtengo los data feeds en el servidor')
    logger.debug('Host: ' + host)
    logger.debug('Path: ' + path)
    logger.debug('Port: ' + str(port))

    feed_information = tm.FeedInformationRequest(message_id=tm.generate_message_id())
    feed_info_xml = feed_information.to_xml()
    logger.debug('Se envia el siguiente mensaje: ' + feed_info_xml)
    client = tc.HttpClient()
    resp = client.callTaxiiService2(host, path, t.VID_TAXII_XML_10, feed_info_xml, port)

    response_message = t.get_message_from_http_response(resp, '0')
    logger.debug('Se obtiene la siguiente respuesta: '+response_message)



