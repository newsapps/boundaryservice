from django.conf.urls.defaults import url
from django.contrib.gis.geos import GEOSGeometry
from django.core.serializers import json
from django.utils import simplejson

from tastypie.bundle import Bundle
from tastypie.fields import ApiField, CharField
from tastypie.resources import ModelResource
from tastypie.serializers import Serializer
from tastypie.utils import trailing_slash

from boundaries.lib.fields import ListField, JSONField

class ListApiField(ApiField):
    """
    Custom ApiField for dealing with data from custom ListFields.
    """
    dehydrated_type = 'list'
    help_text = 'Delimited list of items.'
    
    def dehydrate(self, obj):
        return self.convert(super(ListApiField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None
        
        return value

class JSONApiField(ApiField):
    """
    Custom ApiField for dealing with data from custom JSONFields.
    """
    dehydrated_type = 'json'
    help_text = 'JSON structured data.'
    
    def dehydrate(self, obj):
        return self.convert(super(JSONApiField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None
        
        return value

class SluggedResource(ModelResource):
    """
    ModelResource subclass that handles looking up models by slugs rather than IDs.
    """
    def override_urls(self):
        """
        Add slug-based url pattern.
        """
        return [
            url(r"^(?P<resource_name>%s)/schema%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_schema'), name="api_get_schema"),
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

    @classmethod
    def api_field_from_django_field(cls, f, default=CharField):
        """
        Overrides default field handling to support custom ListField and JSONField.
        """
        if isinstance(f, ListField):
            return ListApiField
        elif isinstance(f, JSONField):
            return JSONApiField
    
        return super(SluggedResource, cls).api_field_from_django_field(f, default)

class JSONOnlySerializer(Serializer):
    def __init__(self):
        Serializer.__init__(self, formats=['json', 'jsonp'], content_types = {'json': 'application/json', 'jsonp': 'text/javascript'})

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        
        # Go through hackery hell to encode geometries as geojson instead of wkt
        def process_geojson(obj):
            if 'simple_shape' in obj:
                geom = GEOSGeometry(obj['simple_shape'])
                obj['simple_shape'] = simplejson.loads(geom.geojson)
            
            if 'centroid' in obj:
                geom = GEOSGeometry(obj['centroid'])
                obj['centroid'] = simplejson.loads(geom.geojson)

        # Lists
        if 'objects' in data:
            for obj in data['objects']:
                process_geojson(obj)
        # Single objects
        elif isinstance(data, dict):
            process_geojson(data)
        
        return simplejson.dumps(data, cls=json.DjangoJSONEncoder, sort_keys=True)
