from json import loads

from django.contrib.gis.db import models
from newsapps.db.models import SluggedModel

from boundaries.lib.fields import ListField, JSONField

class BoundarySet(SluggedModel):
    """
    A set of related boundaries, such as all Wards or Neighborhoods.
    """
    name = models.CharField(max_length=64, unique=True
        help_text="Category of boundaries, e.g. \"Community Areas\".")
    singular = models.CharField(max_length=64,
        help_text="Name of a single boundary, e.g. \"Community Area\".")
    authority = models.CharField(max_length=256,
        help_text="The entity responsible for this data's accuracy, e.g. \"City of Chicago\".")
    last_updated = models.DateField(
        help_text="The last time this data was updated by its authority.")
    href = models.URLField(blank=True,
        help_text="The url this data was found at, if any.")
    notes = models.TextField(blank=True,
        help_text="Notes about loading this data, including any transformations that were applied to it.")
    count = models.IntegerField(
        help_text="Total number of features in this boundary set.")
    metadata_fields = ListField()

    def __unicode__(self):
        """
        Print plural names.
        """
        return self.name

class Boundary(SluggedModel):
    """
    A boundary object, such as a Ward or Neighborhood.
    """
    kind = models.CharField(max_length=64, db_index=True,
        help_text="A category, e.g. \"Community Area\".")
    external_id = models.CharField(max_length=64,
        help_text="The boundaries' unique id in the source dataset, or a generated one.")
    name = models.CharField(max_length=256, db_index=True,
        help_text="The name of this boundary, e.g. \"Austin\".")
    json_metadata = models.JSONField(blank=True,
        help_text="The complete contents of the attribute table for this boundary in the source , structured as json.")
    shape = models.MultiPolygonField(srid=4269,
        help_text="The geometry of this boundary in EPSG:4269.")
    
    objects = models.GeoManager()
    
    __metadata = None
    
    def __unicode__(self):
        """
        Print names are formatted like "Austin Community Area"
        and will slug like "austin-community-area".
        """
        return unicode(" ".join((self.name, self.kind)))

    @property
    def metadata(self):
        """
        Fetch de-jsonified metadata.
        """
        if self.__metadata is None:
            self.__metadata = loads(self.json_metadata)
        return self.__metadata
