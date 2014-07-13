from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^inbox/(\w+)/$', 'taxii.views.inbox_service'),
    url(r'^poll/$', 'taxii.views.poll_service'),
    url(r'^discovery/$', 'taxii.views.discovery_service'),
    url(r'^feedManagment/$', 'taxii.views.feed_managment_service'),
)

