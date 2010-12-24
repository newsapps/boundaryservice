from django.conf import settings
from django.conf.urls.defaults import *
from boundaries.apps.demo import views

urlpatterns = patterns('',
    url(r'^$', views.index, name="location"),
)
