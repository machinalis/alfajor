from django.contrib import admin
from ventas.models import Producto, Caja, DatosDeEnvio, GastosDeEnvio, Pedido
from ventas.models import ARP
from ventas.forms import DatosDeEnvioForm
from ventas.forms import GastosDeEnvioForm, ARProvinceSelect


class ProductoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'variedad', 'precio_por_unidad', 'disponible',
                    'imagen', 'imagen_thumbnail')
    ordering = ('tipo', 'variedad',)
    search_fields = ('tipo', 'variedad',)


class GastosDeEnvioAdmin(admin.ModelAdmin):
    form = GastosDeEnvioForm

    list_display = ('destino', 'precio')
    ordering = ('localidad', 'provincia', 'precio')
    search_fields = ('localidad', 'provincia')


class DatosDeEnvioAdmin(admin.ModelAdmin):
    form = DatosDeEnvioForm

    list_display = ('nombre_completo', 'direccion', 'localidad',
                    'provincia', 'codigo_postal',)

    search_fields = ('nombre_completo', 'direccion',
                     'localidad', 'provincia', 'codigo_postal')


class PedidoAdmin(admin.ModelAdmin):

    readonly_fields = ('datos_de_envio', 'gastos_de_envio',)

    list_display = ('fecha', 'nombre_completo', 'direccion', 'localidad',
                    'provincia', 'codigo_postal', 'confirmado', 'enviado',
                    'productos', 'costo_de_productos', 'costo_de_envio')

    search_fields = ('datos_de_envio.direccion', 'datos_de_envio.localidad',
                     'datos_de_envio.provincia', 'datos_de_envio.codigo_postal',
                     )

    exclude = ('cajas',)

    def nombre_completo(self, obj):
        if not obj.datos_de_envio:
            return u'sin datos'
        return u'%s' % (obj.datos_de_envio.nombre_completo)
    nombre_completo.admin_order_field = 'pedido__datos_de_envio'

    def direccion(self, obj):
        if not obj.datos_de_envio:
            return u'sin datos'
        return u'%s' % (obj.datos_de_envio.direccion)
    direccion.admin_order_field = 'pedido__datos_de_envio'

    def localidad(self, obj):
        if not obj.datos_de_envio:
            return u'sin datos'
        ret = (obj.datos_de_envio.localidad or '----')
        return u'%s' % ret
    localidad.admin_order_field = 'pedido__datos_de_envio'

    def provincia(self, obj):
        if not obj.datos_de_envio:
            return u'sin datos'
        return u'%s' % (ARP[obj.datos_de_envio.provincia])
    provincia.admin_order_field = 'pedido__datos_de_envio'

    def codigo_postal(self, obj):
        if not obj.datos_de_envio:
            return u'sin datos'
        return u'%s' % (obj.datos_de_envio.codigo_postal)
    codigo_postal.admin_order_field = 'pedido__datos_de_envio'

    def productos(self, obj):
        s = u''.join((u'<p>' + unicode(caja) + u'</p>'
                        for caja in obj.cajas.all()))
        return s
    productos.admin_order_field = 'pedido__cajas'
    productos.allow_tags = True


admin.site.register(Pedido, PedidoAdmin)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(GastosDeEnvio, GastosDeEnvioAdmin)
admin.site.register(DatosDeEnvio, DatosDeEnvioAdmin)
