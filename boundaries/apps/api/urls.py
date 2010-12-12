from django.conf.urls.defaults import *
from tastypie.api import Api

from boundaries.apps.api.resources import BoundarySetResource, BoundaryResource

v1_api = Api(api_name='v1')
v1_api.register(BoundarySetResource())
v1_api.register(BoundaryResource())

urlpatterns = patterns('',
    (r'', include(v1_api.urls)),
)
