from django.conf.urls.defaults import url
from django.contrib.gis.measure import D
from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.resources import ModelResource
from tastypie.serializers import Serializer

from boundaries.apps.api.models import BoundarySet, Boundary

class SluggedResource(ModelResource):
    """
    ModelResource subclass that handles looking up models by slugs rather than IDs.
    """
    def override_urls(self):
        """
        Add slug-based url pattern.
        """
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            ]

    def get_resource_uri(self, bundle_or_obj):
        """
        Override URI generation to use slugs.
        """
        kwargs = {
            'resource_name': self._meta.resource_name,
        }
        
        if isinstance(bundle_or_obj, Bundle):
            kwargs['slug'] = bundle_or_obj.obj.slug
        else:
            kwargs['slug'] = bundle_or_obj.slug
        
        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name
        
        return self._build_reverse_url("api_dispatch_detail", kwargs=kwargs)

class BoundarySetResource(SluggedResource):
    boundaries = fields.ToManyField('boundaries.apps.api.resources.BoundaryResource', 'boundaries')

    class Meta:
        queryset = BoundarySet.objects.all()
        serializer = Serializer(formats=['json', 'jsonp'], content_types = {'json': 'application/json', 'jsonp': 'text/javascript'})
        resource_name = 'boundary-set'
        excludes = ['id', 'singular', 'kind_first']
        allowed_methods = ['get']

class BoundaryResource(SluggedResource):
    set = fields.ForeignKey(BoundarySetResource, 'set')

    class Meta:
        queryset = Boundary.objects.all()
        serializer = Serializer(formats=['json', 'jsonp'], content_types = {'json': 'application/json', 'jsonp': 'text/javascript'})
        resource_name = 'boundary'
        excludes = ['id', 'display_name', 'shape']
        allowed_methods = ['get']

    def build_filters(self, filters=None):
        """
        Override build_filters to support geoqueries.
        """
        if filters is None:
            filters = {}

        orm_filters = super(BoundaryResource, self).build_filters(filters)

        if 'contains' in filters:
            lat, lon = filters['contains'].split(',')
            wkt_pt = 'POINT(%s %s)' % (lon, lat)

            orm_filters = {"shape__contains": wkt_pt}

        if 'near' in filters:
            lat, lon = filters['near'].split(',')
            wkt_pt = 'POINT(%s %s)' % (lon, lat)

            orm_filters = {"shape__distance_lte": (wkt_pt, D(mi=1))}

        return orm_filters
