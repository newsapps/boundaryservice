from django.conf.urls.defaults import url
from tastypie import fields
from tastypie.resources import ModelResource

from boundaries.apps.api.models import BoundarySet, Boundary

class SluggedResource(ModelResource):
    """
    ModelResource subclass that handles looking up models by slugs rather than IDs.
    """
    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            ]

class BoundarySetResource(SluggedResource):
    class Meta:
        queryset = BoundarySet.objects.all()
        resource_name = 'boundary-set'
        excludes = ['id', 'singular']
        allowed_methods = ['get']

class BoundaryResource(SluggedResource):
    set = fields.ForeignKey(BoundarySetResource, 'set')

    class Meta:
        queryset = Boundary.objects.all()
        resource_name = 'boundary'
        excludes = ['id', 'shape']
        allowed_methods = ['get']
