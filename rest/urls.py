from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = patterns('',
#    url(r'^get_feed_managment_services/$', 'rest.views.get_feed_managment_services'),
    url(r'^subscripcion_data_feed/$', 'rest.views.subscripcion_data_feed'),
    url(r'^obtener_data_feeds/$',  'rest.views.obtener_remote_data_feeds'),
    url(r'^alta_informacion/$', 'rest.views.alta_informacion'),
    url(r'^poll_informacion/$', 'rest.views.poll_informacion' ),
    url(r'^data_feed_subscriptions/$', 'rest.views.obtener_data_feed_subscriptions'),
    url(r'^registrar_remote_data_feeds/$', 'rest.views.registrar_remote_data_feeds'),
    url(r'^test/$', 'rest.views.test')
)

urlpatterns = format_suffix_patterns(urlpatterns)

