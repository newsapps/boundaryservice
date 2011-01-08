import re

from django.conf import settings
from django.shortcuts import render_to_response
from django.template.loader import render_to_string

def index(request):
    context = {}

    try:
        address = request.REQUEST.get('address')
        context['address'] = address
    except KeyError:
        pass

    context['domain'] = settings.MY_SITE_DOMAIN
    context['demo_js'] = render_to_string('demo.js', context)

    mobile = detect_mobile(request)

    if mobile:
        return render_to_response('/geo-location-mobile.html', context)
    else:
        return render_to_response('/geo-location.html', context)
        
def detect_mobile(request):
    ua = request.META["HTTP_USER_AGENT"]
    search = r'mobile'
    mobile = re.search(search, ua, re.IGNORECASE)
    if mobile:
        return True
    else:
        return False
