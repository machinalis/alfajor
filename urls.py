from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from django.views.generic.simple import redirect_to

urlpatterns = patterns('',
    # Example:
    (r'^alfajor/$', redirect_to, {'url': '/alfajor/pedido/'}),
    (r'^alfajor/', include('alfajor.ventas.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)

try:
    from local_urls import static_pattern
except ImportError:
    pass
else:
    urlpatterns += static_pattern
