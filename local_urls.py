import os.path

from django.conf.urls.defaults import *

STATIC_DOC_ROOT = os.path.join(os.path.dirname(__file__), "static")

static_pattern = patterns('django.views.static',
    url(r'^static/(?P<path>.*)$', 'serve',
        {'document_root': STATIC_DOC_ROOT}),
)
