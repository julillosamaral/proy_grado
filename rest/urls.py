from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = patterns('',
    url(r'^alta_informacion/$', 'rest.views.alta_informacion'),
    url(r'^poll_informacion/$', 'rest.views.poll_informacion' ),
    url(r'^test/$', 'rest.views.test')
)

urlpatterns = format_suffix_patterns(urlpatterns)

