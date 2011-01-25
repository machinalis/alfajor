# -*- coding: utf-8 -*-
from django import forms
from django.contrib.localflavor.ar.forms import ARPostalCodeField
from django.contrib.localflavor.ar.forms import ARProvinceSelect
from django.forms.util import ErrorList

from ventas.models import DatosDeEnvio, GastosDeEnvio, ARP


class DumbSelect(forms.Select):
    EMPTY_CHOICES = [('Otra', 'Otra'),]

    def __init__(self, attrs=None, choices=None):
        if choices:
            choices += DumbSelect.EMPTY_CHOICES
        else:
            choices = DumbSelect.EMPTY_CHOICES
        super(DumbSelect, self).__init__(attrs=attrs, choices=choices)


class GastosDeEnvioSelect(forms.Select):

    def __init__(self, gastos_de_envio, attrs=None, choices=None):
        """
            Shipping costs is a queryset from models.GastosDeEnvio.
            Assuming that provinces are being saved with province select
        """
        choices_of_prov = [(p.provincia, ARP.get(p.provincia))
                           for p in gastos_de_envio]
        if choices:
            choices += list(choices)
        else:
            choices = choices_of_prov
        super(GastosDeEnvioSelect, self).__init__(attrs=attrs, choices=choices)


def add_css_classes(f, **kwargs):
    """
    From: http://djangosnippets.org/snippets/2097/
    """
    field = f.formfield(**kwargs)
    if field and field.required:
        attrs = field.widget.attrs
        attrs['class'] = attrs.get('class', '') + 'required'
    return field


class DatosDeEnvioForm(forms.ModelForm):

    formfield_callback = add_css_classes

    direccion = forms.CharField(label=u'Dirección', required=True,
                                widget=forms.TextInput(attrs={'class':
                                                              'required'
                                                              }))
    localidad = forms.CharField(widget=DumbSelect(), required=False)
    codigo_de_area = forms.CharField(label=u'Código de Área',
                                     widget=forms.TextInput(attrs={'class':
                                                                   'required'
                                                                   ' telefono'}
                                                            ))
    telefono = forms.CharField(label=u'Teléfono',
                               widget=forms.TextInput(attrs={'class':
                                                             'required'
                                                             ' telefono'
                                                             }))
    codigo_postal = ARPostalCodeField(label=u'Código Postal',
                                      widget=forms.TextInput(attrs={'class':
                                                                    'required'
                                                                    }))

    def _add_msg_to_error_fields(self, fieldlist, msg):
        for fieldname in fieldlist:
            errorlist = self._errors.get(fieldname)
            if errorlist:
                errorlist.append(msg)
            else:
                self._errors[fieldname] = ErrorList([msg])

    def clean(self, *args, **kwargs):
        super(DatosDeEnvioForm, self).clean()

        cleaned_data = self.cleaned_data

        codigo_de_area = cleaned_data.get('codigo_de_area')
        telefono = cleaned_data.get('telefono')

        if not (codigo_de_area and telefono):
            msg = u"Este campo sólo acepta números"
            self._add_msg_to_error_fields(('telefono',), msg)
            raise forms.ValidationError(msg)

        if not (codigo_de_area.isdigit() and telefono.isdigit()):
            msg = u"Este campo sólo acepta números"
            self._add_msg_to_error_fields(('telefono',), msg)
            raise forms.ValidationError(msg)

        return cleaned_data

    class Meta:
        model = DatosDeEnvio
        widgets = {
            'provincia': GastosDeEnvioSelect(
                GastosDeEnvio.objects.filter(localidad="")
                ),
            }


class GastosDeEnvioForm(forms.ModelForm):

    class Meta:
        model = GastosDeEnvio
        widgets = {
            'provincia': ARProvinceSelect(),
            }
