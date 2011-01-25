from django.conf.urls.defaults import *

urlpatterns = patterns('ventas.views',
    url(r'^pedido/$', 'pedido', name='pedido'),
    url(r'^datos-de-envio/$', 'datos_de_envio', name='datos-de-envio'),
    url(r'^confirmacion/$', 'confirmacion', name='confirmacion'),
    url(r'^gracias/$', 'gracias', name='gracias'),
                       
    # -- AJAX URLs --
    url(r'^ajax/producto-por-id/$', 'ajax_buscar_producto_por_id',
        name='producto-por-id'),
    url(r'^ajax/localidades/$', 'ajax_buscar_localidades_por_provincia',
        name='localidades-por-provincia'),
    url(r'^ajax/costo-de-envio/$', 'ajax_calcular_costo_de_envio',
        name='costo-de-envio'),
)
