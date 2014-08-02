from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^inbox/(\w+)/$', 'taxii.views.inbox_service'), 				#Url to access the inboxes
    url(r'^poll/$', 'taxii.views.poll_service'),						#Url to poll the information
    url(r'^discovery/$', 'taxii.views.discovery_service'),				#Url to make the discovery requests
    url(r'^feedManagment/$', 'taxii.views.feed_managment_service'),		#Url to make the feed management requests
    url(r'^feedSubscription/$', 'taxii.views.subscription_service'),	#Url to make the feed subscription requests
)

