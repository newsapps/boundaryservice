import csv
import logging 
log = logging.getLogger('boundaries.api.load_shapefiles')
import json
from optparse import make_option
import os
import sys

from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.gdal import CoordTransform, DataSource, OGRGeometry, OGRGeomType
from django.contrib.gis.geos import MultiPolygon
from django.db import connections, DEFAULT_DB_ALIAS

from boundaries.apps.api.models import BoundarySet, Boundary

SHAPEFILES_DIR = 'data/shapefiles'
GEOMETRY_COLUMN = 'shape'

class Command(BaseCommand):
    help = 'Import boundaries described by shapefiles.'
    option_list = BaseCommand.option_list + (
        make_option('-c', '--clear', action='store_true', dest='clear',
            help='Clear all jurisdictions in the DB.'),
        make_option('-e', '--except', action='store', dest='except',
            help='Don\'t load these kinds of Areas, comma-delimitted.'),
        make_option('-o', '--only', action='store', dest='only',
            help='Only load these kinds of Areas, comma-delimitted.'),
    )

    def get_version(self):
        return '0.1'

    def handle(self, *args, **options):
        if options['clear']:
            log.info('Clearing all saved boundaries.')
            Boundary.objects.all().delete()
            BoundarySet.objects.all().delete()

        # Load configuration
        sys.path.append(os.path.abspath(SHAPEFILES_DIR))
        from definitions import SHAPEFILES

        if options['only']:
            only = options['only'].split(',')
            # TODO: stripping whitespace here because optparse doesn't handle it correclty
            sources = [s for s in SHAPEFILES if s.replace(' ', '') in only]
        elif options['except']:
            exceptions = options['except'].upper().split(',')
            # See above
            sources = [s for s in SHAPEFILES if s.replace(' ', '') not in exceptions]
        else:
            sources = [s for s in SHAPEFILES]
        
        # Get spatial reference system for the postgis geometry field
        geometry_field = Boundary._meta.get_field_by_name(GEOMETRY_COLUMN)[0]
        SpatialRefSys = connections[DEFAULT_DB_ALIAS].ops.spatial_ref_sys()
        db_srs = SpatialRefSys.objects.get(srid=geometry_field.srid).srs

        for kind, config in SHAPEFILES.items():
            if kind not in sources:
                log.info('Skipping %s.' % kind)
                continue

            log.info('Processing %s.' % kind)

            path = os.path.join(SHAPEFILES_DIR, config['file'])
            datasource = DataSource(path)

            # Assume only a single-layer in shapefile
            if datasource.layer_count > 1:
                log.warn('%s shapefile has multiple layers, using first.' % kind)

            layer = datasource[0]

            # Create a convertor to turn the source data into
            transformer = CoordTransform(layer.srs, db_srs)

            # Create BoundarySet
            set = BoundarySet.objects.create(
                name=kind,
                singular=config['singular'],
                kind_first=config['kind_first'],
                authority=config['authority'],
                domain=config['domain'],
                last_updated=config['last_updated'],
                href=config['href'],
                notes=config['notes'],
                count=len(layer),
                metadata_fields=layer.fields)

            for feature in layer:
                # Transform the geometry to the correct SRS
                geometry = self.polygon_to_multipolygon(feature.geom)
                geometry.transform(transformer)
    
                # Create simplified geometry field by collapsing points within 1/1000th of a degree.
                # Since Chicago is at approx. 42 degrees latitude this works out to an margin of 
                # roughly 80 meters latitude and 112 meters longitude.
                # Preserve topology prevents a shape from ever crossing over itself.
                simple_geometry = geometry.geos.simplify(0.0001, preserve_topology=True)
                
                # Conversion may force multipolygons back to being polygons
                simple_geometry = self.polygon_to_multipolygon(simple_geometry.ogr)

                # Extract metadata into a dictionary
                metadata = {}

                for field in layer.fields:
                    metadata[field] = feature.get(field)

                external_id = config['ider'](feature)
                feature_name = config['namer'](feature)

                if config['kind_first']:
                    display_name = '%s %s' % (config['singular'], feature_name)
                else:
                    display_name = '%s %s' % (feature_name, config['singular'])

                Boundary.objects.create(
                    set=set,
                    kind=config['singular'],
                    external_id=external_id,
                    name=feature_name,
                    display_name=display_name,
                    metadata=metadata,
                    shape=geometry.wkt,
                    simple_shape=simple_geometry.wkt)

            log.info('Saved %i %s.' % (set.count, kind))

    def polygon_to_multipolygon(self, geom):
        """
        Convert polygons to multipolygons so all features are homogenous in the database.
        """
        if geom.__class__.__name__ == 'Polygon':
            g = OGRGeometry(OGRGeomType('MultiPolygon'))
            g.add(geom)
            return g
        elif geom.__class__.__name__ == 'MultiPolygon':
            return geom
        else:
            raise ValueError('Geom is neither Polygon nor MultiPolygon.')
