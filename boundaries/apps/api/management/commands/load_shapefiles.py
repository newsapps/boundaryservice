import csv
import logging 
log = logging.getLogger('boundaries.api.load_shapefiles')
import json
from optparse import make_option
import os
import sys

from django.core.management.base import CommandError, NoArgsCommand
from django.contrib.gis.gdal import CoordTransform, DataSource, OGRGeometry, OGRGeomType
from django.contrib.gis.geos import MultiPolygon
from django.db import connections, DEFAULT_DB_ALIAS

from boundaries.apps.api.models import BoundarySet, Boundary

SHAPEFILES_DIR = 'data/shapefiles'
GEOMETRY_COLUMN = 'shape'

class Command(NoArgsCommand):
    help = 'Import boundaries described by shapefiles.'
    option_list= NoArgsCommand.option_list + (
        make_option('-c', '--clear', action='store_true', dest='clear',
            help='Clear all jurisdictions in the DB.'),
        make_option('-e', '--except', action='store', dest='except',
            help='Don\'t load these kinds of Areas, comma-delimitted.'),
        make_option('-o', '--only', action='store', dest='only',
            help='Only load these kinds of Areas, comma-delimitted.'),
    )

    def get_version(self):
        return '0.1'

    def handle_noargs(self, **options):
        if options['clear']:
            log.info('Clearing all saved boundaries.')
            Boundary.objects.all().delete()
            BoundarySet.objects.all().delete()

        # Load configuration
        sys.path.append(os.path.abspath(SHAPEFILES_DIR))
        from definitions import SHAPEFILES

        if options['only']:
            only = options['only'].split(',')
            sources = [s for s in SHAPEFILES if s in only]
        elif options['except']:
            exceptions = options['except'].upper().split(',')
            sources = [s for s in SHAPEFILES if s not in exceptions]
        else:
            sources = [s for s in SHAPEFILES]
        
        # Get spatial reference system for the postgis geometry field
        geometry_field = Boundary._meta.get_field_by_name(GEOMETRY_COLUMN)[0]
        SpatialRefSys = connections[DEFAULT_DB_ALIAS].ops.spatial_ref_sys()
        db_srs = SpatialRefSys.objects.get(srid=geometry_field.srid).srs

        for name, config in SHAPEFILES.items():
            if name not in sources:
                log.info('Skipping %s.' % name)
                continue

            log.info('Processing %s.' % name)

            path = os.path.join(SHAPEFILES_DIR, config['file'])
            datasource = DataSource(path)

            # Assume only a single-layer in shapefile
            if datasource.layer_count > 1:
                log.warn('%s shapefile has multiple layers, using first.' % name)

            layer = datasource[0]

            # Create a convertor to turn the source data into
            transformer = CoordTransform(layer.srs, db_srs)

            # Create BoundarySet
            set = BoundarySet.objects.create(
                name=name,
                singular=config['singular'],
                authority=config['authority'],
                last_updated=config['last_updated'],
                href=config['href'],
                notes=config['notes'],
                count=len(layer),
                metadata_fields=layer.fields)

            for feature in layer:
                # Transform the geometry to the correct SRS
                geometry = self.polygon_to_multipolygon(feature.geom)
                geometry.transform(transformer)

                # Extract metadata into a dictionary
                metadata = {}

                for field in layer.fields:
                    metadata[field] = feature.get(field)

                Boundary.objects.create(
                    set=set,
                    external_id=config['ider'](feature),
                    name=config['namer'](feature),
                    metadata=metadata,
                    shape=geometry.wkt)

            log.info('Saved %i %s.' % (set.count, name))

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
