# -*- coding: utf-8 -*-
import StringIO
import random
from itertools import izip

from django.test import TestCase
from django.test.client import Client
from django.utils import simplejson
from django.core import serializers

from ventas.models import Caja, Item, Producto
from ventas.models import Pedido, DatosDeEnvio, GastosDeEnvio

from ventas.repr_constructor import Box, BoxTransmogrifier

from ventas.forms import DatosDeEnvioForm

class AgregarProductosACajaTest(TestCase):

    fixtures = [ 'productos.json' ]

    def test_simple_agregar_producto(self):
        """
        Prueba que se puede agregar un alfajor a una caja de alfajores
        """
        caja = Caja.objects.create(tipo="Alfajor")
        alfajor = Producto.objects.filter(tipo="Alfajor")[0]
        caja.agregar_items(alfajor, 1)

        self.assertEqual(caja._productos.all()[0], alfajor)
        asoc = Item.objects.get(caja=caja, producto=alfajor)
        self.assertEqual(asoc.cantidad, 1)

    def test_agregar_distintos_tipos_lanza_excepcion(self):
        """
        Prueba que si se agregan bombones a una caja de alfajores se
        lanza una excepción, en particular ValueError
        """
        caja = Caja.objects.create(tipo="Alfajor")
        alfajor = Producto.objects.filter(tipo="Alfajor")[0]
        caja.agregar_items(alfajor, 3)

        bombon = Producto.objects.filter(tipo="Bombon")[0]
        self.assertRaises(ValueError, caja.agregar_items, bombon, 1)

    def test_simple_total_de_productos(self):
        caja = Caja.objects.create(tipo="Alfajor")
        productos = Producto.objects.filter(tipo="Alfajor")

        caja.agregar_items(productos[0], 3)
        caja.agregar_items(productos[1], 2)
        caja.agregar_items(productos[1], 1)

        self.assertEqual(caja.total_de_productos(), 6)


class ValidacionTest(TestCase):

    fixtures = ['productos.json', 'gastosdeenvio.json']

    def _randchoice(self, size):
        box = []
        acc, n = 0, size
        while acc < size:
            r = random.randint(1, size)
            while acc+r > size: r = random.randint(1, size)
            box.append(r)
            acc += r
        return box

    def _randbox(self, prods_pk):
        return [(random.choice(prods_pk), amount)
                for amount in
                self._randchoice(random.choice((6, 12)))]

    def _to_string(self, box):
        return ','.join([str(k) for k, v in box for _ in xrange(v)]) + ','

    def randomboxes(self, choices=None, number=2):
        if not choices:
            return None
        return [self._to_string(self._randbox(random.choice(choices)))
                for _ in xrange(number)]
    
    def setUp(self):
        self.a_pk = [p.pk for p in Producto.objects.filter(tipo="Alfajor")]
        self.b_pk = [p.pk for p in Producto.objects.filter(tipo="Bombon")]

        self._data = {'nombre_completo': u'José Perez',
                      'direccion': u'Nicochea 2345',
                      'codigo_postal': '5001',
                      'localidad': u'Villa Urquiza',
                      'provincia': u'C',
                      'email': 'joseperez@test.com',
                      'telefono': '44444444',
                      'codigo_de_area': '11',}


    def test_validar_cajas_simple(self):
        bt = BoxTransmogrifier()
        for x in xrange(1, 10):
            cajas = self.randomboxes(choices=[self.a_pk, self.b_pk], number=x)
            self.assert_(bt.crear_lista_de_cajas_apartir_de_lista_str(cajas))

    def test_crear_cajas_crea_instancias_de_box(self):
        """
        No guardamos cajas en la base de datos, creamos instancias de 'Box'
        """
        
        bt = BoxTransmogrifier()
        for x in xrange(1, 10):
            cajas = self.randomboxes(choices=[self.a_pk, self.b_pk], number=x)
            
            lista_de_cajas = bt.crear_lista_de_cajas_apartir_de_lista_str(cajas)

            # Tiene que ser instancias de caja
            self.assert_(all([isinstance(b, Box) for b in lista_de_cajas]))

    def test_crear_pedido(self):
        
        bt = BoxTransmogrifier()
        bt.datos_de_envio = DatosDeEnvio.objects.create(**self._data)
        bt.gastos_de_envio = GastosDeEnvio.objects.get(provincia="C",
                                                       localidad="")
        for x in xrange(1, 10):
            cajas = self.randomboxes(choices=[self.a_pk, self.b_pk], number=x)
            
            lista_de_cajas = bt.crear_lista_de_cajas_apartir_de_lista_str(cajas)
            

            pedido = bt.crear_pedido()
            self.assert_(pedido)
            self.assert_(pedido.pk)
            
            sk = lambda obj : obj.pk

            # Hay que tener en cuenta que el orden puede ser distinto
            # entonces las vamos a comparar primero viendo si el tamaño
            # de todas las cajas es igual...

            _len = lambda obj : obj.total_de_productos()
            self.assertEqual(sorted(map(_len, lista_de_cajas)),
                             sorted(map(_len, pedido.cajas.all())))

            # Ahora vamos a comparar que todos los elementos de todas las
            # cajas (un flatten) es decir vemos que en total hay en
            # cada caja hay la misma cantidad y que además la lista
            # entera de productos son iguales.
            elems0 = sorted((elem
                             for box in lista_de_cajas
                             for elem in box), key=sk)

            elems1 = sorted((elem
                             for caja in pedido.cajas.all()
                             for elem in caja), key=sk)

            self.assertEqual(list(elems0), list(elems1))

        self.assertEqual(Pedido.objects.all().count(), 9)
            
    def test_crear_pedido_sin_datos_lanza_excepcion(self):
        bt = BoxTransmogrifier()
        self.assertRaises(AttributeError, bt.crear_pedido)



class FormTests(TestCase):

    fixtures = ['productos.json']

    def setUp(self):
        self._data = {'nombre_completo': u'José Perez',
                      'direccion': u'Nicochea 2345',
                      'codigo_postal': '5001',
                      'localidad': u'Villa Urquiza',
                      'provincia': u'C',
                      'email': 'joseperez@test.com',
                      'telefono': '44444444',
                      'codigo_de_area': '11',}

    def test_simple_valid_form(self):
        f = DatosDeEnvioForm(self._data)
        self.assert_(f.is_valid())

    def test_simple_invalid_form(self):
        """
        El formulario debería ser invalido porque el telefono contiene letras
        """
        invalid_data = dict(self._data, telefono='4444a444')
        f = DatosDeEnvioForm(invalid_data)
        self.assert_(not f.is_valid())
        self.assert_(f.errors)

    def test_simple_invalid_form(self):
        """
        El formulario debería ser invalido porque el telefono contiene letras
        """
        invalid_data = dict(self._data, codigo_de_area='a11')
        f = DatosDeEnvioForm(invalid_data)
        self.assert_(not f.is_valid())
        self.assert_(f.errors)


class ViewsTest(TestCase):

    def setUp(self):
        self.c = Client()

    def test_ajax_buscar_todos_los_productos(self):
        pass

