from django.conf.urls.defaults import *
from boundaries.apps.api.resources import BoundaryResource

boundary_resource = BoundaryResource()

urlpatterns = patterns('',
    (r'^boundaries/', include(boundary_resource.urls)),
)
