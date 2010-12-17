from django.shortcuts import render_to_response
from django.conf import settings

def index(request):
    template_dict = {}
    try:
        address = request.REQUEST.get('address')
        template_dict['address'] = address
    except KeyError:
        pass

    template_dict['domain'] = settings.MY_SITE_DOMAIN
    
    return render_to_response('/geo-location.html', template_dict)