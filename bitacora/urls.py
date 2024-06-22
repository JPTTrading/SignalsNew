from django.urls import path, include
from .views import view_app, form, salir, get_symbol_details, edit_stop
from django.conf import settings
from django.conf.urls.static import static
from . import bitacora_app
from bitacora.bitacora_app import *
# app_name = 'bitacora'

urlpatterns = [
    path('', view_app, name='view_app'),  # URL de la bitácora
    path('formulario/', form, name='form'),  # URL para el formulario
    path('salir/', salir, name='salir'),
    path('bitacora/detalles/', get_symbol_details, name='get_symbol_details'),
    path('edit_stop/', edit_stop, name='edit_stop'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
