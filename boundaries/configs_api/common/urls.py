from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin

from boundaries.apps.api import views as api_views

admin.autodiscover()

urlpatterns = patterns('',
    (r'^(?P<api_name>1.0)/(?P<resource_name>boundary-set)/(?P<slug>[\w\d_.-]+)/(?P<external_id>[\w\d_.-]+)$', api_views.external_id_redirects),
    (r'^', include('api.urls')),
)
