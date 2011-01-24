from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin

from boundaries.apps.api import views as api_views

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),
    
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT
    }),

    (r'^api/(?P<api_name>1.0)/(?P<resource_name>boundary-set)/(?P<slug>[\w\d_.-]+)/(?P<external_id>[\w\d_.-]+)$', api_views.external_id_redirects),
    (r'^api/', include('api.urls')),
    (r'', include('demo.urls'))
)
