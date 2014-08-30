import sys
import libtaxii as t
import libtaxii.messages_11 as tm11
import libtaxii.messages as tm
import libtaxii.clients as tc
import logging
from taxii.models import DataFeedSubscriptionMethod, ContentBlock, ContentBindingId
from urlparse import urlparse
from stix.core import STIXPackage, STIXHeader


def poll_request(collection_name, subscription_id, host, path, port):
    #Given the collection name, subscription id, host, path and port we make a poll request to 
    #the client TAXII associated with the host, path and port for the subscription and collection given.
    logger = logging.getLogger('TAXIIApplication.rest.tasks.poll_request')
    logger.debug('Poll information starts')
    logger.debug('Parameters are: ')
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
    logger.debug('The following Poll Request message was generated')
    logger.debug('###########################################')
    logger.debug(poll_req_xml)
    logger.debug('###########################################')

    client = tc.HttpClient()
    resp = client.callTaxiiService2(host, path, t.VID_TAXII_XML_10, poll_req_xml, port)
    response_message = t.get_message_from_http_response(resp, '0')

    logger.debug('The response got from the sistem was: ')
    logger.debug('#########################################')
    logger.debug(response_message.to_xml())
    logger.debug('#########################################')

    try:
        taxii_message = tm.get_message_from_xml(response_message.to_xml())
    except Exception as ex:
        logger.debug('The message could not be parsed:s', ex.message)

    if taxii_message.message_type != tm.MSG_POLL_RESPONSE:
        logger.debug('The message is not a TAXII response')
    else:
        logger.debug(taxii_message)
        content_blocks = taxii_message.content_blocks
        logger.debug('We process the Content Blocks')

        for cb in content_blocks:
            p = ContentBlock()

            stix_package = STIXPackage()
            stix_package.from_xml(xml_file=cb.content)

            p.description = stix_package.stix_header.description
            p.title = stix_package.stix_header.title
            p.message_id = taxii_message.message_id

            c = ContentBindingId(binding_id=cb.content_binding)
            c.save()
            p.content_binding = c
            p.content = cb.content
            p.save()


def envio_informacion(data_feed, host, path, port):
    #Given the host, port and path of a TAXII client we sent the data_feed to that client.
    logger = logging.getLogger('TAXIIApplication.rest.tasks.envio_informacion')
    logger.debug('Get the subscription methods')
    logger.debug('The parameters are: ')
    logger.debug('Host: ' + host)
    logger.debug('Path: ' + path)
    logger.debug('Port: ' + str(port))
    logger.debug('Data Feed name:' + data_feed.name)

    content_blocks = data_feed.content_blocks

    content = []
    for content_block in content_blocks.all():
	cb = tm11.ContentBlock(tm11.ContentBinding(content_block.content_binding.binding_id), content_block.content)
        content.append(cb)

    inbox_message = tm11.InboxMessage(message_id = tm11.generate_message_id(), content_blocks=content)

    inbox_xml = inbox_message.to_xml()
    logger.debug('The message to be sent is: '+ inbox_xml)

    client = tc.HttpClient()
    client.setProxy('noproxy')

    resp = client.callTaxiiService2(host, path, t.VID_TAXII_XML_10, inbox_xml, port)
    response_message = t.get_message_from_http_response(resp, '0')
    logger.debug('The response message was: ' + response_message.to_xml())
    #Con la respuesta creo que no hago nada. Queda loggeada nomas

def obtener_data_feeds(host, port, path):
    #Given the host, port and path of a TAXII client we get the data feeds of that client
    logger = logging.getLogger('TAXIIApplication.rest.tasks.obtener_data_feeds')
    logger.debug('We get the server data feeds')
    logger.debug('Host: ' + host)
    logger.debug('Path: ' + path)
    logger.debug('Port: ' + str(port))

    feed_information = tm.FeedInformationRequest(message_id=tm.generate_message_id())
    feed_info_xml = feed_information.to_xml()
    logger.debug('The following message is sent: ' + feed_info_xml)
    client = tc.HttpClient()
    resp = client.callTaxiiService2(host, path, t.VID_TAXII_XML_10, feed_info_xml, port)

    response_message = t.get_message_from_http_response(resp, '0')
    logger.debug('We get the following response: '+response_message.to_xml())



