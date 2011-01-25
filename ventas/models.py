# -*- coding: utf-8 -*-
import os.path
from itertools import groupby
from django.db import models
from django.conf import settings
from django.contrib.localflavor.ar import ar_provinces

ARP = dict(ar_provinces.PROVINCE_CHOICES)

# Create your models here.
class Producto(models.Model):
    CHOICES = (('Alfajor', 'Alfajor'),
               ('Bombon', 'Bombon'),)

    tipo = models.CharField(choices=CHOICES, max_length=10)
    variedad = models.CharField(max_length=256)
    disponible = models.BooleanField(default=True)
    precio_por_unidad = models.DecimalField(decimal_places=2, max_digits=5)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='productos')
    imagen_thumbnail = models.ImageField(upload_to='productos')


    class Meta:
        unique_together = ('tipo', 'variedad')

    def __unicode__(self):
        return u'%s de %s' % (self.tipo, self.variedad)

    def get_precio_con_fmt(self):
        return u'%.2f' % self.precio_por_unidad

    def json_equivalent(self):
        dictionary = {}
        for field in ('pk', 'tipo', 'variedad', 'descripcion'):
            dictionary[field] = getattr(self, field)

        dictionary['imagen'] = self.imagen.url
        dictionary['imagen_thumbnail'] = self.imagen_thumbnail.url
        dictionary['precio_por_unidad'] = self.get_precio_con_fmt()
        
        return dictionary


class Item(models.Model):
    """
    Representa una asociación entre Producto y Caja, agrega
    información sobre la cantidad de elementos que van en la caja.
    """
    caja = models.ForeignKey('Caja')
    producto = models.ForeignKey(Producto)
    cantidad = models.IntegerField()


class Caja(models.Model):
    CHOICES = (('Alfajor', 'Alfajor'),
               ('Bombon', 'Bombon'),)

    tipo = models.CharField(choices=CHOICES, max_length=10)
    _productos = models.ManyToManyField(Producto, through=Item)

    def __unicode__(self):
        prods = u'\n'.join((u'%s x %d' % (item.producto, item.cantidad)
                            for item in Item.objects.filter(caja=self)))

        return (u'Caja de %ses:\n' % self.tipo) + prods

    def agregar_items(self, producto, cantidad):
        if self.tipo != producto.tipo:
            raise ValueError(u'El tipo del producto no coincide'
                             u' con el tipo de caja')
        Item.objects.create(caja=self, producto=producto, cantidad=cantidad)

    def total_de_productos(self):
        return sum(item.cantidad for item in Item.objects.filter(caja=self))

    def es_valida(self):
        total_de_productos = self.total_de_productos()
        return (total_de_productos == 6 or
                total_de_productos == 12)

    def costo(self):
        return sum(item.cantidad * item.producto.precio_por_unidad
                   for item in Item.objects.filter(caja=self))

    def __iter__(self):
        return (item.producto for item in Item.objects.filter(caja=self)
                              for _ in xrange(item.cantidad)) 


class GastosDeEnvio(models.Model):
    """
    Tabla de gastos de envio.
    """

    precio = models.DecimalField(decimal_places=2, max_digits=5)
    localidad = models.CharField(max_length=50, blank=True)
    provincia = models.CharField(max_length=50)

    def destino(self):
        if not self.localidad:
            return u'%s' % ARP[self.provincia]
        else:
            return u'%s, %s' % (self.localidad, ARP[self.provincia]) 

    def __unicode__(self):
        return self.destino() + u': %s' % self.precio
            
    class Meta:
        unique_together = ('localidad', 'provincia')  
        

class DatosDeEnvio(models.Model):
    """
    Datos del envío.
    """
    nombre_completo = models.CharField(max_length=256)
    email = models.EmailField()
    codigo_de_area = models.CharField(max_length=5)
    telefono = models.CharField(max_length=10)
    direccion = models.CharField(max_length=256)
    codigo_postal = models.CharField(max_length=256)    
    localidad = models.CharField(max_length=256, blank=True)
    provincia = models.CharField(max_length=2)

    def get_nombre_completo(self):
        return u'%s' % (self.nombre_completo,)
    
    def get_telefono(self):
        return u'%s-%s' % (self.codigo_de_area, self.telefono)

    def get_calle_y_numero(self):
        return u'%s' % self.direccion 
        
    def get_direccion(self):
        args = (self.get_calle_y_numero(),
                self.codigo_postal,
                self.localidad,
                self.get_provincia())
        if not self.localidad:
            return u'%s\nCP %s\n%s' % (args[:2] + (args[-1],))

        return u'%s\nCP %s\n%s - %s' % args

    def get_provincia(self):
        return u'%s' % ARP[self.provincia]
    
    def __unicode__(self):
        return u'%s,\n%s' % (self.get_nombre_completo(),
                            self.get_direccion())


class Pedido(models.Model):

    fecha = models.DateTimeField()
    datos_de_envio = models.ForeignKey(DatosDeEnvio, null=True, blank=True)
    gastos_de_envio = models.ForeignKey(GastosDeEnvio, null=True, blank=True)
    cajas = models.ManyToManyField(Caja)
    confirmado = models.BooleanField()
    enviado = models.BooleanField()

    def agregar_caja(self, caja):
        if not caja.es_valida():
            raise ValueError(u'Tamaño de la caja es erroneo')
        self.cajas.add(caja)

    def costo_de_productos(self):
        return sum([caja.costo() for caja in self.cajas.all()])
    
    def costo_de_envio(self):
        if not self.gastos_de_envio:
            return 0
        return self.gastos_de_envio.precio

    def costo_total(self):
       return self.costo_de_envio() + self.costo_de_productos()

    def __unicode__(self):
        if self.datos_de_envio:
            return (u'Pedido a nombre de %s' %
                    self.datos_de_envio.nombre_completo)
        else:
            return u'Pedido sin datos de envio'

