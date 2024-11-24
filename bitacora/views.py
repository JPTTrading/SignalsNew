from django.shortcuts import render, redirect
from django.core.cache import cache
from pathlib import Path
from .models import Bitacora_Principal, Historial_Bitacora
from decimal import Decimal, InvalidOperation
from django.utils import timezone
import smtplib
from email.mime.text import MIMEText
from django.http import HttpResponseServerError, JsonResponse
import traceback
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from datetime import datetime
from django.db import transaction
import yfinance as yf
from django.contrib import messages

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
    try:
        if request.method == "POST":
            with transaction.atomic():

                # tomamos los datos que llegan del formulario
                stop_loss_edit = request.POST['stop_loss_edit']
                target_price_edit = request.POST['target_price_edit']

                if stop_loss_edit and stop_loss_edit.strip():
                    stop_loss_edit = Decimal(stop_loss_edit)

                    # Obtén los datos del formulario
                    symbol_edit = request.POST['symbol_edit'].upper()

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

                            porcentaje_ejecutado=0,
                        )
                        historial_data.save()
                    else:
                        print("No se encontró el símbolo en la bitácora principal")

                if target_price_edit and target_price_edit.strip():
                    target_price_edit = Decimal(target_price_edit)

                    # Obtén los datos del formulario
                    symbol_edit = request.POST['symbol_edit']

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

                            porcentaje_ejecutado=0,
                        )
                        historial_data.save()
                    else:
                        print("No se encontró el símbolo en la bitácora principal")
        
        messages.success(request, '¡Registro creado exitosamente!')
        return redirect('form')

    except Exception as e:
        # Imprime la excepción en la consola o logs
        print(f"Error en la vista: {e}")
        traceback.print_exc()
        # Retorna una respuesta de error 500
        return HttpResponseServerError("Error interno del servidor")


def view_app(request):
    try:
        if request.method == "POST":
            # Obtén los datos del formulario
            symbol = request.POST['symbol'].upper()
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
            
            # Verifica si el símbolo existe en Yahoo Finance
            stock_info = yf.Ticker(symbol)
            if not stock_info.history(period="1d").empty:
                # Si el símbolo existe, continua con la lógica de la bitácora


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

                        # (new_percentage / 100) * ENTRY) / ((existing_percentage / 100) + (new_percentage / 100))
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
                        porcentaje_acumulado=porcentaje_ejecutado
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

                # envía el correo
                data_email(request)

                messages.success(request, '¡Registro creado exitosamente!')
                return redirect('form')
            else    :
                # Si el símbolo no existe en Yahoo Finance, muestra un mensaje de advertencia
                messages.warning(request, f'El símbolo "{symbol}" no existe en Yahoo Finance.')
                return redirect('form')
        
        # Obtener precios de la caché o de Yahoo Finance si no están en caché
        precios = cache.get('precios_symbols')
        if not precios:
            precios = yahoo_finance_price()
        
        messages.success(request, '¡Registro creado exitosamente!')
        return render(request,'bitacora.html')
    except Exception as e:
        # Imprime la excepción en la consola o logs
        print(f"Error en la vista: {e}")
        traceback.print_exc()
        # Retorna una respuesta de error 500
        return HttpResponseServerError("Error interno del servidor")


def ultimos_registros():
    registros = Bitacora_Principal.objects.order_by('-trade_date')[:3]

    resultados_registros = []

    for registro in registros:
        dict_resultados_registros = {}

        dict_resultados_registros['symbol'] = registro.symbol
        dict_resultados_registros['side'] = registro.side
        dict_resultados_registros['entry'] = str(registro.entry)

        resultados_registros.append(dict_resultados_registros)

    return resultados_registros


ultimos_registros()

def yahoo_finance_price():
    symbols = Bitacora_Principal.objects.filter(
        trade_close__isnull=True).values_list('symbol', flat=True)

    precios = {}

    # Actualizar precios para cada símbolo
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            history = ticker.history(period="max")
            ultimo_precio = round(history['Close'].iloc[-1], 2)
        except Exception as e:
            print(f"Error al obtener datos de Yahoo Finance: {e}")
            data_yf = yf.download(symbol, period='1d')
            ultimo_precio = round(data_yf['Close'].iloc[-1], 2)

        precios[symbol] = ultimo_precio

    # Almacenar el diccionario en la caché por 15 minutos
    cache.set('precios_symbols', precios, timeout=15*60)  # 15 minutos

    return precios

# Llamar la función para actualizar la caché
yahoo_finance_price()

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
    bitacoras = cache.get('bit')
    reg = ultimos_registros()
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

