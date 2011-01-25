from django import template
from django.template.defaultfilters import stringfilter
from django.utils.encoding import force_unicode

register = template.Library()

@register.inclusion_tag('templatetags/productos.html')
def show_productos(caja):
    try:
        productos = list(caja)
    except Exception, e:
        print "[show_products] %s" % e
        return {'productos': []}
    else:
        return {'productos': productos}

@register.inclusion_tag('templatetags/datos-de-envio.html')
def show_datos_de_envio(pedido):
    datos_de_envio = pedido.datos_de_envio
    return {'nombre': datos_de_envio.get_nombre_completo(),
            'direccion': datos_de_envio.get_calle_y_numero(),
            'codigo_postal': datos_de_envio.codigo_postal,
            'localidad': datos_de_envio.localidad,
            'provincia': datos_de_envio.get_provincia(),
            'telefono': datos_de_envio.get_telefono(),
            'email': datos_de_envio.email,}
    
    
@register.inclusion_tag('templatetags/carrito_de_compra.html')
def show_carrito_de_compra(pedido):
    num_cajas = len(pedido.cajas.all())
    lista_de_productos = zip([list(caja) for caja in pedido.cajas.all()],
                              range(num_cajas))
    return {'pedido': pedido,
            'lista_de_productos': lista_de_productos}
    
@register.inclusion_tag('templatetags/inputs.html')
def show_hidden_fields(pedido):
    try:
        vals = [(caja.tipo, (','.join([str(x.pk) for x in caja]) + ','))
                for caja in pedido.cajas.all()]
    except Exception, e:
        print "[show_hidden_fields] %s" % e
        vals = []
    return {'vals': vals,
            'siguiente_caja': len(pedido.cajas.all()) + 1,}

@register.filter
def decimalfmt(value):
    return u"%.2f" % value
decimalfmt.is_safe = True
