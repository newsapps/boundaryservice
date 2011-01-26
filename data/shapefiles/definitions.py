"""
Configuration describing the shapefiles to be loaded.
"""
from datetime import date

from django.contrib.humanize.templatetags.humanize import ordinal

import utils

SHAPEFILES = {
    'Neighborhoods': {
        'file': 'neighborhoods/Neighboorhoods.shp',
        'singular': 'Neighborhood',
        'kind_first': False,
        'ider': utils.simple_namer(['PRI_NEIGH_']),
        'namer': utils.simple_namer(['PRI_NEIGH']),
        'authority': 'City of Chicago',
        'domain': 'Chicago',
        'last_updated': date(2010, 12, 12),
        'href': 'http://www.cityofchicago.org/city/en/depts/doit/supp_info/gis_data.html',
        'notes': ''
    },
}
