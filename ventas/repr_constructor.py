# -*- coding: utf-8 -*-
from datetime import datetime
from ventas.models import Caja, Producto, Pedido
from itertools import groupby

class Box(object):

    def __init__(self, tipo):
        self.tipo = tipo
        self._productos = []

    def __unicode__(self):
        return u'Caja de %es' % self.tipo

    def agregar_items(self, producto, cantidad):
        if self.tipo != producto.tipo:
            raise ValueError(u'El tipo del producto no coincide'
                             u' con el tipo de caja')
        self._productos.extend([producto for _ in xrange(cantidad)])

    def total_de_productos(self):
        return len(self._productos)

    def es_valida(self):
        return (len(self._productos) == 6 or
                len(self._productos) == 12)

    def costo(self):
        return sum(p.precio_por_unidad for p in self._productos)

    def __iter__(self):
        return iter(self._productos)

    def crear_caja(self):
        caja_inst = Caja.objects.create(tipo=self.tipo)
        for k, g in groupby(sorted(self._productos, key=lambda x : x.pk)):
            caja_inst.agregar_items(k, len(list(g)))
        return caja_inst

class BoxList(list):

    def __init__(self, *args, **kwargs):
        super(BoxList, self).__init__(*args, **kwargs)

    def all(self):
        return self

class BoxTransmogrifier(object):
    """
    http://bit.ly/dEhVXv

    Su función es basicamente validar los datos antes de que entren
    en la base de datos. No sé donde podría ir esto, me parecio que
    acá estaba bien.
    """

    def __init__(self):
        self.datos_de_envio = None
        self.gastos_de_envio = None
        self.cajas = BoxList([])

    def _string_a_lista_de_productos(self, s):
        """
        s es de la forma u'7,7,7,7,7,7,' donde los números representan
        un id de un producto
        """
        return [Producto.objects.get(pk=int(pk))
                for pk in s.strip(" ,").split(",")]

    def _lista_de_productos_es_una_caja(self, lp):
        """
        determina si la lista de productos es una caja
        """
        num_prods = len(lp)
        if num_prods != 6 and num_prods != 12:
            return False
        # Ver si son todas del mismo tipo
        producto = lp[0]
        tipo = producto.tipo
        if not all([tipo == p.tipo for p in lp]):
            return False
        return True

    def crear_lista_de_cajas_apartir_de_lista_str(self, ls):
        """
        Acá cajas, no es una instancia de Caja(models.Model) si no
        es una lista de productos que representa una Caja valida
        Esto es lo que viene en los datos del post:
        [
          u'7,7,7,7,7,7,',
          u'7,7,7,7,7,7,',
          u'17,17,17,17,17,17,17,17,17,17,17,17,'
         ]
        Esta función transforma lo de arriba en:
        [
         [Producto(pk=7), Producto(pk=7) ...],
         ...
         [Producto(pk=17), ... ]
        ]
        """
        if not ls:
            raise ValueError("No hay cajas")

        cajas = BoxList([])
        for elem in ls:
            lista_de_prods = self._string_a_lista_de_productos(elem)
            if not self._lista_de_productos_es_una_caja(lista_de_prods):
                raise ValueError("No es una caja valida :%s" % lista_de_prods)
            tipo = lista_de_prods[0].tipo
            b = Box(tipo=tipo)
            b._productos = lista_de_prods
            cajas.append(b)
        self.cajas = cajas
        return cajas


    def costo_de_productos(self):
        if not self.cajas:
            ValueError("No hay cajas en el pedido")
        return sum([caja.costo() for caja in self.cajas])

    def costo_de_envio(self):
        if not self.gastos_de_envio:
            ValueError("No hay gastos de envio asociados")
        return self.gastos_de_envio.precio

    def costo_total(self):
        return self.costo_de_envio() + self.costo_de_productos()

    def __unicode__(self):
        if self.datos_de_envio:
            return u'Pedido a nombre de %s %s' % (self.datos_de_envio.nombre,
                                                  self.datos_de_envio.apellido)
        else:
            return u'Pedido sin datos de envio'


    def crear_pedido(self, instance=None):
        """
        Toma una lista de cajas, es decir una lista de Box que
        representa una futura instancia de Caja(models.Model) y
        devuelve un pedido Pedido(models.Model) con sus cajas

        Si no se seteo previamente los atributos datos_de_envio y
        gastos_de_envio con los objectos correspondientes (DatosDeEnvio() y
        GastosDeEnvio() respectivamente) la función lanzara AttributeError

        Crea una instancia si no se le pasa una mediante el 'instance'
        """

        if not (self.datos_de_envio and self.gastos_de_envio):
            raise AttributeError("Se espera que antes haya "
                                 "agregado los datos a los atributos "
                                 "datos_de_envio y gastos_de_envio.")

        if not instance:
            pedido = Pedido.objects.create(fecha=datetime.now())
        else:
            pedido = instance

        for caja in self.cajas:
            caja_inst = caja.crear_caja()
            pedido.agregar_caja(caja_inst)

        self.datos_de_envio.save()
        pedido.datos_de_envio = self.datos_de_envio
        pedido.gastos_de_envio = self.gastos_de_envio
        pedido.confirmado = True
        
        pedido.save()
        return pedido

