from django.shortcuts import render_to_response
from django.conf import settings

def index(request):
    template_dict = {}
    template_dict['domain'] = settings.MY_SITE_DOMAIN
    
    return render_to_response('/geo-locale.html', template_dict)