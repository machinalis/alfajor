# -*- coding: utf-8 -*-
from datetime import datetime

from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, loader, Context
from django.utils import simplejson
from django.core import serializers
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.conf import settings

from ventas.models import Producto, Caja, Pedido, DatosDeEnvio, GastosDeEnvio
from ventas.repr_constructor import Box, BoxTransmogrifier

from ventas.forms import DatosDeEnvioForm, DumbSelect

SESSION_PEDIDO_KEY = 'pedido'

def ajax_buscar_producto_por_id(request):
    prod_id = int(request.GET.get("idR"))
    producto = Producto.objects.get(pk=prod_id)
    data = simplejson.dumps(producto.json_equivalent())
    response = HttpResponse(data, mimetype='application/json')
    return response

def ajax_buscar_localidades_por_provincia(request):
    provincia = request.GET.get("provincia")
    gastos_de_envio = GastosDeEnvio.objects.filter(provincia=provincia)
    extra = DumbSelect.EMPTY_CHOICES
    localidades = [(item.localidad, item.localidad)
                   for item in gastos_de_envio
                   if item.localidad != ""
                   ] + list(extra)
    data = simplejson.dumps(localidades)
    response = HttpResponse(data, mimetype='application/json')
    return response

def ajax_calcular_costo_de_envio(request):
    provincia = request.GET.get("provincia")
    localidad = request.GET.get("localidad", "")

    # To handle empty strings, I will send "null"
    if localidad and localidad.strip() == "null":
        localidad = ""

    try:
        # If localidad == "" then I will return the province cost,
        # so localidad has blank=True
        gastos_de_envio = GastosDeEnvio.objects.get(localidad=localidad,
                                                    provincia=provincia)
    except GastosDeEnvio.DoesNotExist:
        data = simplejson.dumps("costo desconocido")
    else:
        s = "%.2f" % gastos_de_envio.precio
        data = simplejson.dumps(s)

    response = HttpResponse(data, mimetype='application/json')
    return response

def pedido(request):
    # Context for the first template

    alfajores = Producto.objects.filter(tipo="Alfajor")
    bombones = Producto.objects.filter(tipo="Bombon")

    alfajores_disp = Producto.objects.filter(tipo="Alfajor",
                                             disponible=True).order_by('?')

    if alfajores_disp:
        alfajor = alfajores_disp[0]
    else:
        alfajor = None

    c = { 'date' : datetime.now(),
          'alfajores' : alfajores,
          'bombones' : bombones,
          'init_prod': alfajor, }

    pedido =  request.session.get(SESSION_PEDIDO_KEY, None)
    if pedido:
        c['pedido'] = pedido

    context = RequestContext(request, c)

    if request.method == 'POST':
        cajas = [s for s in request.POST.getlist('cajas[]') if s]
        

        # Object to validate boxes
        bt = BoxTransmogrifier()

        try:
            # before creating an object into the db, validate.
            # If cajas == "", also throw ValueError
            lista_de_cajas = bt.crear_lista_de_cajas_apartir_de_lista_str(cajas)

        except ValueError, e:
            # if error, no order
            pedido = None
        else:
            pedido = bt

        # if there is an order, go to next step
        if pedido:
            request.session[SESSION_PEDIDO_KEY] = pedido
            return HttpResponseRedirect(reverse('datos-de-envio'))

    return render_to_response("main.html", context)

def datos_de_envio(request):

    # instance of BoxTransmogrifier
    pedido = request.session.get(SESSION_PEDIDO_KEY, None)
    if not pedido:
        return HttpResponseRedirect(reverse('pedido'))

    if pedido.datos_de_envio:
        form = DatosDeEnvioForm(instance=pedido.datos_de_envio)
    else:
        form = DatosDeEnvioForm()

    if request.method == 'POST':
        if pedido.datos_de_envio:
            form = DatosDeEnvioForm(request.POST,
                                    instance=pedido.datos_de_envio)
        else:
            form = DatosDeEnvioForm(request.POST)

        if form.is_valid():
            # We don't save the object until we have completed the
            # transaction
            datos_de_envio = form.save(commit=False)

            try:
                gastos_de_envio = GastosDeEnvio.objects.get(
                    localidad=datos_de_envio.localidad,
                    provincia=datos_de_envio.provincia)
            except GastosDeEnvio.DoesNotExist:
                gastos_de_envio = GastosDeEnvio.objects.get(
                    localidad="",
                    provincia=datos_de_envio.provincia)


            pedido.datos_de_envio = datos_de_envio
            pedido.gastos_de_envio = gastos_de_envio
            request.session[SESSION_PEDIDO_KEY] = pedido
            return HttpResponseRedirect(reverse("confirmacion"))

    context = RequestContext(request, { 'date': datetime.now(),
                                        'form': form,
                                        'pedido': pedido, })

    return render_to_response("paso2.html", context)

def confirmacion(request):

    # instance of BoxTransmogrifier
    pedido = request.session.get(SESSION_PEDIDO_KEY, None)

    if not pedido:
        return HttpResponseRedirect(reverse('pedido'))

    if request.method == 'POST':
        # Pedido instance
        pedido_inst = pedido.crear_pedido()

        cajas = u'\n'.join((unicode(caja) for caja in pedido_inst.cajas.all()))
        datos_de_envio = pedido_inst.datos_de_envio

        # Message for owner
        body = (u"Order id: %d\nA: %s\n"
                u"Items:\n %s\nItems cost: %.2f\n"
                u"Shipping cost: %.2f") % (pedido_inst.pk,
                                            datos_de_envio,
                                            cajas,
                                            pedido_inst.costo_de_productos(),
                                            pedido_inst.costo_de_envio())
        subject = u"[Order id %d]" % pedido_inst.pk
        sender = pedido_inst.datos_de_envio.email
        recipients = getattr(settings, 'EMAIL_ADDR_ALFAJOR', '')

        elnaza_msg = EmailMessage(subject, body, sender, (recipients,))

        # Message for customer
        client_msg_body = (u"Thanks for your order. \n\n"
                           u"Order details follow: \n%s\n\n"
                           u"The order will be shipped to the following"
                           u" address: \n%s\n\n"
                           u"Items cost: %.2f\n"
                           u"Shipping cost: %2.f\n\n"
                           u"Total: %2.f\n\n"
                           u"Don't hesitate about contacting us.\n\n"
                           u"Alfajor") % (cajas, datos_de_envio,
                                            pedido_inst.costo_de_productos(),
                                            pedido_inst.costo_de_envio(),
                                            pedido_inst.costo_total(),)
        client_subject = (u"Your Alfajor order has been confirmed!")
        client_msg_recipients = (pedido_inst.datos_de_envio.email,)
        client_msg_sender = getattr(settings, 'EMAIL_ADDR_ALFAJOR', '')

        client_msg = EmailMessage(client_subject, client_msg_body,
                                  client_msg_sender, client_msg_recipients)

        if (settings.EMAIL_HOST and
            settings.EMAIL_PORT and
            settings.EMAIL_ADDR_ALFAJOR):
            elnaza_msg.send()
            client_msg.send()

        return HttpResponseRedirect(reverse("gracias"))

    context = RequestContext(request, { 'date': datetime.now(),
                                        'pedido': pedido })

    return render_to_response("paso3.html", context)

def gracias(request):
    request.session[SESSION_PEDIDO_KEY] = None
    context = RequestContext(request, { 'date': datetime.now(), })
    return render_to_response("gracias.html", context)
