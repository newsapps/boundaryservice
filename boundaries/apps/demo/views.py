from django.shortcuts import render_to_response
from django.conf import settings

import re

def index(request):
    template_dict = {}
    try:
        address = request.REQUEST.get('address')
        template_dict['address'] = address
    except KeyError:
        pass

    template_dict['domain'] = settings.MY_SITE_DOMAIN

    mobile = detect_mobile(request)
    if mobile:
        return render_to_response('/geo-location-mobile.html', template_dict)
    else:
        return render_to_response('/geo-location.html', template_dict)
        
def detect_mobile(request):
    ua = request.META["HTTP_USER_AGENT"]
    search = r'mobile'
    mobile = re.search(search, ua, re.IGNORECASE)
    if mobile:
        return True
    else:
        return False