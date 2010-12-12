import csv
import json
from optparse import make_option
import os
import sys

from django.core.management.base import NoArgsCommand, CommandError
from django.contrib.gis.gdal import CoordTransform
from django.contrib.gis.geos import MultiPolygon
from django.db import connections, DEFAULT_DB_ALIAS

from boundaries.apps.api.models import Boundary
#from dave.lib.gis import polygon_to_multipolygon, get_first_layer

SHAPEFILES_DIR = "data/shapefiles"
GEOMETRY_COLUMN = 'shape'

class Command(NoArgsCommand):
    help = 'Import boundaries described by shapefiles.'
    option_list= NoArgsCommand.option_list + (
        make_option('-c', '--clear', action='store_true', dest='clear',
            help='Clear all jurisdictions in the DB.'),
        make_option('-e', '--except', action='store', dest='except',
            help="Don't load these kinds of Areas, comma-delimitted."),
        make_option('-o', '--only', action='store', dest='only',
            help="Only load these kinds of Areas, comma-delimitted."),
    )

    def get_version(self):
        return "0.1"

    def handle_noargs(self, **options):
        if options['clear']:
            print "Clearing all saved boundaries."
            Boundary.objects.all().delete()

        mapping = (
            ('NEIGHBORHOOD',
             simple_namer(('PRI_NEIGH',)),
             simple_namer(("PRI_NEIGH_",)),
             os.path.abspath(os.path.join(MAPS_DIR, 'neighborhoods/Neighborhoods.shp'))
            ),
            ('COMMUNITY_AREA',
             simple_namer(('COMMUNITY',)),
             simple_namer(("AREA_NUMBE",)),
             os.path.abspath(os.path.join(MAPS_DIR, 'community_areas/CommAreas.shp'))
            ),
        )

        if options['only']:
            sources = options['only'].upper().split(',')
        elif options['except']:
            exceptions = options['except'].upper().split(',')
            sources = [source[0] for source in mapping if not source[0] in exceptions]
        elif options['all']:
            sources = [source[0] for source in mapping]
        else:
            sources = ['NEIGHBORHOOD', 'COMMUNITY_AREA']
        
        # Get spatial reference system for the postgis geometry field
        geometry_field = Area._meta.get_field_by_name(GEOMETRY_COLUMN)[0]
        SpatialRefSys = connections[DEFAULT_DB_ALIAS].ops.spatial_ref_sys()
        db_srs = SpatialRefSys.objects.get(srid=geometry_field.srid).srs

        for source in mapping:
            kind,name_func,id_func,source_path = source
            if not kind in sources:
                print "Skipping %s" % kind
                continue

            lyr = get_first_layer(source_path)

            # Create a convertor to turn the source data into
            transformer = CoordTransform(lyr.srs, db_srs) 

            saved = 0
            for l in lyr:
                try:
                    name = name_func(l)
                    alt_id = id_func(l)

                    # Transform the geometry to the correct SRS
                    geometry = polygon_to_multipolygon(l.geom)
                    geometry.transform(transformer)

                    j = Area.objects.create(
                            kind = kind,
                            name = name,
                            external_id = "%s_%s" % (kind,alt_id),
                            geom = geometry.wkt,
                            pickled_meta = pickle_layer(l)
                        )
                    saved += 1
                except ValueError:
                    print 'Skipped %s "%s"' % (kind,name)
            print "%s saved %i" % (kind,saved)
            


