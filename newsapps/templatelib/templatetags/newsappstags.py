from django import template
from django.conf import settings
from urlparse import urljoin
from urllib import quote_plus

register = template.Library()
 
# Infrastructure Stuff
@register.inclusion_tag("newsapps/_analytics_header.html")
def analytics_header():
    return { "settings": settings }

@register.inclusion_tag("newsapps/_analytics_footer.html")
def analytics_footer(page_name):
    context = {}
    context['settings'] = settings

    if getattr(settings, 'ENABLE_OMNITURE', False):
        # Omniture page names are limited to 100 characters
        context['page_name'] = ('Chicago Tribune - %s - %s' % (settings.OMNITURE_APP_NAME, page_name))[:100]

    return context 
    
@register.simple_tag
def build_media_url(uri):
    """
       Take a bit of url (uri) and put it together with the media url
       urljoin doesn't work like you think it would work. It likes to
       throw bits of the url away unless things are just right.
    """
    uri = "/".join(map(quote_plus,uri.split("/")))
    if getattr(settings,'MEDIA_URL',False):
        if uri.startswith('/'):
            return urljoin(settings.MEDIA_URL,uri[1:])
        else:
            return urljoin(settings.MEDIA_URL,uri)
    else:
        return uri
