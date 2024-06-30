from django.shortcuts import render, redirect, get_object_or_404
import pandas as pd
from django.core.cache import cache
from pathlib import Path
from .models import Bitacora_Principal, Historial_Bitacora
from datetime import date
from decimal import Decimal, InvalidOperation
from django.utils import timezone
import logging
import smtplib
from email.mime.text import MIMEText
from django.http import HttpResponseServerError, JsonResponse
import traceback
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from datetime import datetime
from django.db import transaction

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def calculate_take_profit(entry, new_percentage, existing_entry):
    return (((existing_entry * (new_percentage / 100)) / (entry * (new_percentage / 100))) - 1)*100

# nueva funcion para calcular el precio promedio


def price_promedio(entry, new_percentage, existing_entry, existing_percentage):
    total_value = (existing_entry * (existing_percentage / 100)
                   ) + (entry * (new_percentage / 100))
    total_percentage = existing_percentage + new_percentage
    return total_value / (total_percentage / 100)


def edit_stop(request):
    print("entramos a la funcion")
    print(request.POST)
    try:
        if request.method == "POST":
            with transaction.atomic():

                # tomamos los datos que llegan del formulario
                stop_loss_edit = request.POST['stop_loss_edit']
                target_price_edit = request.POST['target_price_edit']

                if stop_loss_edit and stop_loss_edit.strip():
                    stop_loss_edit = Decimal(stop_loss_edit)

                    # Obtén los datos del formulario
                    symbol_edit = request.POST['symbol_edit'].lower()

                    # Verifica si el símbolo ya existe en la tabla BitacoraPrincipal
                    existing_entry = Bitacora_Principal.objects.filter(
                        symbol=symbol_edit, trade_close__isnull=True).first()

                    if existing_entry:
                        existing_entry.stop_loss = stop_loss_edit
                        existing_entry.target_price = existing_entry.target_price
                        existing_entry.save()

                        historial_data = Historial_Bitacora(
                            bitacora_principal=existing_entry,
                            symbol=symbol_edit,
                            side=existing_entry.side,
                            entry=existing_entry.entry,
                            type="EDIT STOP LOSS",
                            stop_loss=stop_loss_edit,
                            target_price=existing_entry.target_price,
                            # PORCENTAJE_EJECUTADO=existing_entry.PORCENTAJE_ACUMULADO,
                            porcentaje_ejecutado=0,
                        )
                        historial_data.save()
                    else:
                        print("No se encontró el símbolo en la bitácora principal")

                if target_price_edit and target_price_edit.strip():
                    target_price_edit = Decimal(target_price_edit)

                    # Obtén los datos del formulario
                    symbol_edit = request.POST['symbol_edit'].lower()

                    # Verifica si el símbolo ya existe en la tabla BitacoraPrincipal
                    existing_entry = Bitacora_Principal.objects.filter(
                        symbol=symbol_edit, trade_close__isnull=True).first()

                    if existing_entry:
                        existing_entry.stop_loss = existing_entry.stop_loss
                        existing_entry.target_price = target_price_edit
                        existing_entry.save()

                        historial_data = Historial_Bitacora(
                            bitacora_principal=existing_entry,
                            symbol=symbol_edit,
                            side=existing_entry.side,
                            entry=existing_entry.entry,
                            type="EDIT TARGET PRICE",
                            stop_loss=existing_entry.stop_loss,
                            target_price=target_price_edit,
                            # PORCENTAJE_EJECUTADO=existing_entry.PORCENTAJE_ACUMULADO,
                            porcentaje_ejecutado=0,
                        )
                        historial_data.save()
                    else:
                        print("No se encontró el símbolo en la bitácora principal")
            data = convertir()
            data_his = convertir_historia()
            cache.set('bit', data)
            cache.set('his', data_his)
        return redirect('form')

    except Exception as e:
        # Imprime la excepción en la consola o logs
        print(f"Error en la vista: {e}")
        traceback.print_exc()
        # Retorna una respuesta de error 500
        return HttpResponseServerError("Error interno del servidor")


def view_app(request):
    print("entramos a la vista")
    print(request.POST)
    try:
        if request.method == "POST":
            # Obtén los datos del formulario
            symbol = request.POST['symbol'].lower()
            side = request.POST['side']
            entry = Decimal(request.POST['entry'])
            type = request.POST['type']
            porcentaje_ejecutado = Decimal(
                request.POST['porcentaje_ejecutado'])

            # Función para convertir a Decimal o devolver None si está vacío
            def to_decimal(value):
                try:
                    return Decimal(value)
                except (InvalidOperation, ValueError):
                    return None

            stop_loss = to_decimal(request.POST.get('stop_loss', '').strip())
            target_price = to_decimal(
                request.POST.get('target_price', '').strip())

            # Verifica si el símbolo ya existe en la tabla BitacoraPrincipal
            existing_entry = Bitacora_Principal.objects.filter(
                symbol=symbol, trade_close__isnull=True).first()

            if existing_entry:
                # Si no se proporcionan nuevos valores, usa los existentes
                if stop_loss is None:
                    stop_loss = existing_entry.stop_loss
                if target_price is None:
                    target_price = existing_entry.target_price

                # Actualiza entry si el side es el mismo
                if existing_entry.side == side:
                    existing_percentage = existing_entry.porcentaje_ejecutado
                    new_percentage = porcentaje_ejecutado
                    new_entry = price_promedio(
                        entry, new_percentage, existing_entry.entry, existing_percentage)
                    # new_entry = ((existing_percentage / 100) * existing_entry.ENTRY +
                    #              (new_percentage / 100) * ENTRY) / ((existing_percentage / 100) + (new_percentage / 100))
                    existing_entry.entry = new_entry
                    existing_entry.porcentaje_ejecutado += new_percentage
                    existing_entry.save()

                # Verifica el side de la nueva operación y ajusta el porcentaje acumulado
                if existing_entry.side != side:
                    new_percent_acum = round(
                        existing_entry.porcentaje_acumulado * (1 - (porcentaje_ejecutado / 100)), 2)
                else:
                    new_percent_acum = round(
                        existing_entry.porcentaje_acumulado * (1 + porcentaje_ejecutado / 100), 2)

                existing_entry.porcentaje_acumulado = new_percent_acum
                existing_entry.stop_loss = stop_loss
                existing_entry.target_price = target_price
                existing_entry.save()

                # Verifica si se alcanzó el 100% de ejecución en el Bitacora_Principal
                if existing_entry.porcentaje_acumulado <= 0:
                    existing_entry.trade_close = timezone.now().date()
                    existing_entry.save()

                # Registra en Historial_Bitacora
                historial_data = Historial_Bitacora(
                    bitacora_principal=existing_entry,
                    symbol=symbol,
                    side=side,
                    entry=entry,
                    type=type,
                    stop_loss=stop_loss,
                    target_price=target_price,
                    porcentaje_ejecutado=porcentaje_ejecutado,
                )

                # Calcula el profit si el side es diferente
                if existing_entry.side != side:
                    existing_entry = existing_entry.entry
                    profit = calculate_take_profit(
                        existing_entry, porcentaje_ejecutado, entry)
                    historial_data.profit = profit

                historial_data.save()
            else:
                # Si el símbolo no existe en Bitacora_Principal, crea un nuevo registro
                new_bitacora = Bitacora_Principal(
                    symbol=symbol,
                    side=side,
                    entry=entry,
                    stop_loss=stop_loss if stop_loss is not None else Decimal(
                        '0.00'),  # Asigna valor predeterminado
                    target_price=target_price if target_price is not None else Decimal(
                        '0.00'),  # Asigna valor predeterminado
                    porcentaje_acumulado=100
                )
                new_bitacora.save()

                # Luego, crea un registro en HistorialBitacora relacionándolo con el nuevo BitacoraPrincipal
                historial_data = Historial_Bitacora(
                    bitacora_principal=new_bitacora,
                    symbol=symbol,
                    side=side,
                    type=type,
                    entry=entry,
                    stop_loss=stop_loss if stop_loss is not None else Decimal(
                        '0.00'),  # Asigna valor predeterminado
                    target_price=target_price if target_price is not None else Decimal(
                        '0.00'),  # Asigna valor predeterminado
                    porcentaje_ejecutado=porcentaje_ejecutado,
                )
                historial_data.save()

            # Actualiza los datos en caché y envía el correo
            data = convertir()
            data_his = convertir_historia()
            cache.set('bit', data)
            cache.set('his', data_his)
            data_email(request)

        return render(request, 'bitacora.html')
    except Exception as e:
        # Imprime la excepción en la consola o logs
        print(f"Error en la vista: {e}")
        traceback.print_exc()
        # Retorna una respuesta de error 500
        return HttpResponseServerError("Error interno del servidor")


def convertir():
    objs = Bitacora_Principal.objects.all().order_by('trade_date')

    # Crea una lista para almacenar los resultados individuales
    resultados = []

    for obj in objs:
        # Crea un diccionario para cada objeto y agrega los atributos que necesitas
        dict_resultado = {}
        dict_resultado['uuid'] = str(obj.uuid)
        dict_resultado['trade_date'] = obj.trade_date.strftime('%d-%m-%Y')
        dict_resultado['trade_close'] = obj.trade_close
        dict_resultado['symbol'] = obj.symbol
        dict_resultado['side'] = obj.side
        dict_resultado['entry'] = str(obj.entry)  # Serializa Decimal a cadena
        dict_resultado['stop_loss'] = str(
            obj.stop_loss)  # Serializa Decimal a cadena
        dict_resultado['target_price'] = str(
            obj.target_price)  # Serializa Decimal a cadena
        dict_resultado['porcentaje_acumulado'] = str(
            obj.porcentaje_acumulado)  # Serializa Decimal a cadena
        # Agrega más atributos según sea necesario
        resultados.append(dict_resultado)
        cache.set('bit', resultados)

    # Devuelve la lista de resultados
    return resultados


def convertir_historia():
    objs_historial = Historial_Bitacora.objects.order_by('trade_date').all()

    resultados_historial = []

    for obj_h in objs_historial:
        # Crea un diccionario para cada objeto y agrega los atributos que necesitas
        dict_resultado_historial = {}
        dict_resultado_historial['uuid'] = str(obj_h.bitacora_principal.uuid)
        dict_resultado_historial['trade_date'] = obj_h.trade_date.strftime(
            '%d-%m-%Y')
        dict_resultado_historial['symbol'] = obj_h.symbol
        dict_resultado_historial['side'] = obj_h.side
        dict_resultado_historial['entry'] = str(
            obj_h.entry)  # Serializa Decimal a cadena
        dict_resultado_historial['stop_loss'] = str(
            obj_h.stop_loss)  # Serializa Decimal a cadena
        dict_resultado_historial['target_price'] = str(
            obj_h.target_price)  # Serializa Decimal a cadena
        # Agrega más atributos según sea necesario
        dict_resultado_historial['profit'] = str(
            obj_h.profit)
        dict_resultado_historial['porcentaje_ejecutado'] = str(
            obj_h.porcentaje_ejecutado)
        resultados_historial.append(dict_resultado_historial)
        cache.set('his', resultados_historial)

    return resultados_historial


convertir()
convertir_historia()


def convertir_registros():
    registros = Bitacora_Principal.objects.order_by('trade_date')[:3]

    resultados_registros = []

    for registro in registros:
        dict_resultados_registros = {}

        dict_resultados_registros['symbol'] = registro.symbol
        dict_resultados_registros['side'] = registro.side
        dict_resultados_registros['entry'] = str(registro.entry)

        resultados_registros.append(dict_resultados_registros)

        cache.set('reg', resultados_registros)

    return resultados_registros


convertir_registros()


def data_email(request):

    now = datetime.now()

    data = {}

    if request.method == "POST":
        # Obtén los datos del formulario
        symbol = request.POST.get('symbol')
        side = request.POST.get('side')
        entry = str(request.POST.get('entry'))
        type = request.POST.get('type')
        stop_loss = str(request.POST.get('stop_loss'))
        target_price = str(request.POST.get('target_price'))
        porcentaje_ejecutado = str(request.POST.get('porcentaje_ejecutado'))

        # Crea un diccionario con los datos del formulario
        data = {
            'symbol': symbol,
            'side': side,
            'entry': entry,
            'type': type,
            'stop_loss': stop_loss,
            'target_price': target_price,
            'porcentaje_ejecutado': porcentaje_ejecutado,
        }
        email(data, 'jpttapps@gmail.com', 'Nuevo trade')


def email(data, destinatario, asunto):
    server = smtplib.SMTP('smtp.gmail.com', 587)

    server.starttls()
    server.login('valeria.martinez@ttrading.co', 'wntnzaykdxpgdvzp')

    # Convierte el diccionario en una cadena de texto formateada
    message_body = "\n".join(
        [f"{key}: {value}" for key, value in data.items()])

    message = MIMEText(message_body)
    message['Subject'] = asunto
    message['From'] = 'valeria.martinez@ttrading.co'
    message['To'] = destinatario

    # Envía el correo electrónico.
    server.sendmail(message['From'], message['To'], message.as_string())

    # Cierra la conexión con el servidor.
    server.quit()
    return print("correo enviado")


@login_required
def form(request):
    bitacoras = Bitacora_Principal.objects.filter(
        trade_close__isnull=True).order_by('trade_date')
    # bitacoras = cache.get('bit')
    reg = convertir_registros()
    cache.set('reg', reg)
    return render(request, 'form.html', {'reg': reg, 'bitacoras': bitacoras})


def get_symbol_details(request):
    symbol = request.GET.get('symbol', None)
    if symbol:
        bitacoras = cache.get('bit')
        for bitacora in bitacoras:
            if bitacora.symbol == symbol:
                return JsonResponse({
                    'entry': bitacora.entry,
                    # Agrega aquí cualquier otro detalle que quieras devolver
                })
    return JsonResponse({'error': 'Symbol not found'}, status=404)


def salir(request):
    logout(request)
    return redirect('/')
