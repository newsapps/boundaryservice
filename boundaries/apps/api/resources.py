from tastypie.resources import ModelResource
from boundaries.apps.api.models import Boundary

class BoundaryResource(ModelResource):
    class Meta:
        queryset = Boundary.objects.all()
        resource_name = 'boundary'
