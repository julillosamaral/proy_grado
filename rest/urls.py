from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = patterns('',
    url(r'^subscripcion_data_feed/$', 'rest.views.subscripcion_data_feed'), 			#url to suscribe to data feeds
    url(r'^obtener_data_feeds/$',  'rest.views.obtener_remote_data_feeds'), 			#url to get data feed
    url(r'^alta_informacion/$', 'rest.views.alta_informacion'),							#url to add informaction to the system
    url(r'^poll_informacion/$', 'rest.views.poll_informacion' ),						#url to make a poll information
    url(r'^data_feed_subscriptions/$', 'rest.views.obtener_data_feed_subscriptions'), 	#url to make a subscription to a data feed
    url(r'^registrar_remote_data_feeds/$', 'rest.views.registrar_remote_data_feeds'),	#url to register to a remote data feed
    url(r'^envio_informacion/$', 'rest.views.envio_informacion')
)

urlpatterns = format_suffix_patterns(urlpatterns)



