import re

from django.conf.urls.defaults import url
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from django.core.serializers import json
from django.utils import simplejson
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

class JSONOnlySerializer(Serializer):
    def __init__(self):
        Serializer.__init__(self, formats=['json', 'jsonp'], content_types = {'json': 'application/json', 'jsonp': 'text/javascript'})

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        
        # Go through hackery hell to encode geometries as geojson instead of wkt
        def reencode_shape(obj):
            if 'simple_shape' in obj:
                geom = GEOSGeometry(obj['simple_shape'])
                obj['simple_shape'] = simplejson.loads(geom.geojson)

        # Lists
        if 'objects' in data:
            for obj in data['objects']:
                reencode_shape(obj)
        # Single objects
        elif isinstance(data, dict):
            reencode_shape(data)
        
        return simplejson.dumps(data, cls=json.DjangoJSONEncoder, sort_keys=True)

class BoundarySetResource(SluggedResource):
    boundaries = fields.ToManyField('boundaries.apps.api.resources.BoundaryResource', 'boundaries')

    class Meta:
        queryset = BoundarySet.objects.all()
        serializer = JSONOnlySerializer()
        resource_name = 'boundary-set'
        excludes = ['id', 'singular', 'kind_first']
        allowed_methods = ['get']

class BoundaryResource(SluggedResource):
    set = fields.ForeignKey(BoundarySetResource, 'set')

    class Meta:
        queryset = Boundary.objects.all()
        serializer = JSONOnlySerializer()
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

        if 'sets' in filters:
            sets = filters['sets'].split(',')

            orm_filters.update({'set__slug__in': sets})

        if 'contains' in filters:
            lat, lon = filters['contains'].split(',')
            wkt_pt = 'POINT(%s %s)' % (lon, lat)

            orm_filters.update({'shape__contains': wkt_pt})

        if 'near' in filters:
            lat, lon, range = filters['near'].split(',')
            wkt_pt = 'POINT(%s %s)' % (lon, lat)
            numeral = re.match('([0-9]+)', range).group(1)
            unit = range[len(numeral):]
            numeral = int(numeral)
            kwargs = {unit: numeral}

            orm_filters.update({'shape__distance_lte': (wkt_pt, D(**kwargs))})

        return orm_filters
