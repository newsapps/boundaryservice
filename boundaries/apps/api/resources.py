import re

from django.contrib.gis.db import models
from django.contrib.gis.measure import D
from tastypie import fields

from boundaries.apps.api.authentication import NoOpApiKeyAuthentication
from boundaries.apps.api.models import BoundarySet, Boundary
from boundaries.apps.api.tastyhacks import JSONOnlySerializer, SluggedResource
from boundaries.apps.api.throttle import AnonymousThrottle

class BoundarySetResource(SluggedResource):
    boundaries = fields.ToManyField('boundaries.apps.api.resources.BoundaryResource', 'boundaries')

    class Meta:
        queryset = BoundarySet.objects.all()
        serializer = JSONOnlySerializer()
        resource_name = 'boundary-set'
        excludes = ['id', 'singular', 'kind_first']
        allowed_methods = ['get']
        authentication = NoOpApiKeyAuthentication()
        throttle = AnonymousThrottle(throttle_at=100) 

class BoundaryResource(SluggedResource):
    set = fields.ForeignKey(BoundarySetResource, 'set')

    class Meta:
        queryset = Boundary.objects.all()
        serializer = JSONOnlySerializer()
        resource_name = 'boundary'
        excludes = ['id', 'display_name', 'shape']
        allowed_methods = ['get']
        authentication = NoOpApiKeyAuthentication()
        throttle = AnonymousThrottle(throttle_at=100) 

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

        if 'intersects' in filters:
            slug = filters['intersects']
            bounds = Boundary.objects.get(slug=slug)

            orm_filters.update({'shape__intersects': bounds.shape})            

        return orm_filters
