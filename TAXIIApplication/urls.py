from django.conf.urls import patterns, url, include
from rest_framework import routers
#from taxii import views
from rest import views
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns
from django.conf.urls import patterns, url


admin.autodiscover()

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'protocolBindingId', views.ProtocolBindingIdViewSet)
router.register(r'contentBindingId', views.ContentBindingIdViewSet)
router.register(r'messageBindingId', views.MessageBindingIdViewSet)
router.register(r'dataFeedPushMethod', views.DataFeedPushMethodViewSet)
router.register(r'dataFeedPollInformation', views.DataFeedPollInformationViewSet)
router.register(r'remoteDataFeedPollInformation', views.RemoteDataFeedPollInformationViewSet)
router.register(r'dataFeedSubscriptionMethod', views.DataFeedSubscriptionMethodViewSet)
router.register(r'contentBlock', views.ContentBlockViewSet)
router.register(r'dataFeed', views.DataFeedViewSet)
router.register(r'dataFeedSubscription', views.DataFeedSubscriptionViewSet)
router.register(r'remoteDataFeed', views.RemoteDataFeedViewSet)
router.register(r'inbox', views.InboxViewSet)
router.register(r'remoteInbox', views.RemoteInboxViewSet)
router.register(r'contentBlockRTIR', views.ContentBlockRTIRViewSet)

#urlpatterns = router.urls

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.

urlpatterns = patterns('',
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^services/', include('taxii.urls')),
    url(r'^rest_services/', include('rest.urls'))
)

