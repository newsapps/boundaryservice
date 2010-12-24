import re

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect

from boundaries.apps.api.models import Boundary

def external_id_redirects(request, api_name, resource_name, slug, external_id):
    """
    Redirects /boundary-set/external_id paths to the proper canonical boundary path.
    """
    if resource_name != 'boundary-set':
        raise Http404 

    boundary = get_object_or_404(Boundary, set__slug=slug, external_id=external_id)

    return redirect('api_dispatch_detail', api_name=api_name, resource_name='boundary', slug=boundary.slug, permanent=True)

