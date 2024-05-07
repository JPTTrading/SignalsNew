
from django.shortcuts import render, redirect, get_object_or_404
import pandas as pd
from django.core.cache import cache
from pathlib import Path
from .models import Bitacora_Principal, Historial_Bitacora
from datetime import date
from decimal import Decimal
from django.utils import timezone
import logging
import smtplib
from email.mime.text import MIMEText
from django.http import HttpResponseServerError
import traceback
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .forms import EdicionBitacoraForm
from datetime import datetime

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def calculate_take_profit(ENTRY, new_percentage, existing_ENTRY):
    return (((existing_ENTRY * (new_percentage / 100)) / (ENTRY * (new_percentage / 100))) - 1)*100


def view_app(request):
    try:
        if request.method == "POST":
            # Obtén los datos del formulario
            SYMBOL = request.POST['SYMBOL']
            SIDE = request.POST['SIDE']
            ENTRY = Decimal(request.POST['ENTRY'])
            STOP_LOSS = Decimal(request.POST['STOP_LOSS'])
            TARGET_PRICE = Decimal(request.POST['TARGET_PRICE'])
            PORCENTAJE_EJECUTADO = Decimal(
                request.POST['PORCENTAJE_EJECUTADO'])

            # Verifica si el símbolo ya existe en la tabla BitacoraPrincipal
            existing_entry = Bitacora_Principal.objects.filter(
                SYMBOL=SYMBOL, TRADE_CLOSE__isnull=True).first()

            if existing_entry:

                existing_entry.STOP_LOSS = STOP_LOSS
                existing_entry.TARGET_PRICE = TARGET_PRICE
                existing_entry.save()

                # Verifica el SIDE de la nueva operación
                # Si el SIDE es contrario, suma el porcentaje ejecutado
                # Si el SIDE es el mismo, resta el porcentaje ejecutado
                if existing_entry.SIDE != SIDE:
                    new_percent_acum = existing_entry.PORCENTAJE_ACUMULADO - PORCENTAJE_EJECUTADO

                    # Actualiza el valor de PORCENTAJE_ACUMULADO
                    existing_entry.PORCENTAJE_ACUMULADO = new_percent_acum

                    existing_entry.save()

                else:
                    new_percent_acum = existing_entry.PORCENTAJE_ACUMULADO + PORCENTAJE_EJECUTADO

                    # Actualiza el valor de PORCENTAJE_ACUMULADO
                    existing_entry.PORCENTAJE_ACUMULADO = new_percent_acum

                    existing_entry.save()

                # Verifica si se alcanzó el 100% de ejecución en el Bitacora_Principal
                if existing_entry.PORCENTAJE_ACUMULADO <= 0:
                    existing_entry.TRADE_CLOSE = timezone.now().date()
                    existing_entry.save()
                # Si el símbolo existe en BitacoraPrincipal, verifica el SIDE
                if existing_entry.SIDE == SIDE and existing_entry.SYMBOL == SYMBOL:
                    # Calcula el porcentaje ejecutado de la operación existente
                    existing_percentage = existing_entry.PORCENTAJE_EJECUTADO

                    # Calcula el porcentaje ejecutado de la nueva operación
                    new_percentage = PORCENTAJE_EJECUTADO

                    # Calcula el valor actualizado de ENTRY
                    new_entry = ((existing_percentage / 100) * existing_entry.ENTRY +
                                 (new_percentage / 100) * ENTRY) / ((existing_percentage / 100) + (new_percentage / 100))

                    # Actualiza el valor de ENTRY en la operación existente
                    existing_entry.ENTRY = new_entry
                    existing_entry.PORCENTAJE_EJECUTADO += new_percentage
                    existing_entry.save()

                if existing_entry.SIDE != SIDE and existing_entry.SYMBOL == SYMBOL:
                    # Calcula el porcentaje ejecutado de la operación existente
                    existing_ENTRY = existing_entry.ENTRY
                    print(f'entramos a esta parte?{existing_ENTRY}')
                    # Calcula el porcentaje ejecutado de la nueva operación
                    new_percentage = PORCENTAJE_EJECUTADO

                    PROFIT = calculate_take_profit(
                        existing_ENTRY, new_percentage, ENTRY)

                    existing_entry.save()

                    historial_data = Historial_Bitacora(
                        BITACORA_PRINCIPAL=existing_entry,
                        SYMBOL=SYMBOL,
                        SIDE=SIDE,
                        ENTRY=ENTRY,
                        STOP_LOSS=STOP_LOSS,
                        TARGET_PRICE=TARGET_PRICE,
                        PORCENTAJE_EJECUTADO=PORCENTAJE_EJECUTADO,
                        PROFIT=PROFIT
                    )
                    historial_data.save()
                else:
                    # Si el SIDE es diferente, crea un registro en HistorialBitacora y realiza los cálculos de profit
                    historial_data = Historial_Bitacora(
                        BITACORA_PRINCIPAL=existing_entry,
                        SYMBOL=SYMBOL,
                        SIDE=SIDE,
                        ENTRY=ENTRY,
                        STOP_LOSS=STOP_LOSS,
                        TARGET_PRICE=TARGET_PRICE,
                        PORCENTAJE_EJECUTADO=PORCENTAJE_EJECUTADO,
                    )
                    historial_data.save()
                    # Calcula el profit para el nuevo registro en el historial no revisado, no funcional
                    # historial_data.calcular_profit()
                    historial_data.save()
            else:
                # Si el símbolo no existe en Bitacora_Principal, crea un nuevo registro
                # UUID = UUID_Auto
                new_bitacora = Bitacora_Principal(
                    SYMBOL=SYMBOL,
                    SIDE=SIDE,
                    ENTRY=ENTRY,
                    STOP_LOSS=STOP_LOSS,
                    TARGET_PRICE=TARGET_PRICE,
                    PORCENTAJE_ACUMULADO=100
                )
                new_bitacora.save()

                # Luego, crea un registro en HistorialBitacora relacionándolo con el nuevo BitacoraPrincipal
                historial_data = Historial_Bitacora(
                    BITACORA_PRINCIPAL=new_bitacora,
                    SYMBOL=SYMBOL,
                    SIDE=SIDE,
                    ENTRY=ENTRY,
                    STOP_LOSS=STOP_LOSS,
                    TARGET_PRICE=TARGET_PRICE,
                    # Establece el porcentaje inicial como lo ponga en el input(o automatica si aquí le pongo el 100)
                    PORCENTAJE_EJECUTADO=100,
                )
                historial_data.save()
            data = convertir()
            dataHis = convertirHistoria()
            cache.set('bit', data)
            cache.set('his', dataHis)

            data_email(request)
        return render(request, 'bitacora.html')
    except Exception as e:
        # Imprime la excepción en la consola o logs
        print(f"Error en la vista: {e}")
        traceback.print_exc()
        # Retorna una respuesta de error 500
        return HttpResponseServerError("Error interno del servidor")


def convertir():
    objs = Bitacora_Principal.objects.all()

    # Crea una lista para almacenar los resultados individuales
    resultados = []

    for obj in objs:
        # Crea un diccionario para cada objeto y agrega los atributos que necesitas
        dict_resultado = {}
        dict_resultado['UUID'] = str(obj.uuid)
        dict_resultado['TRADE_DATE'] = obj.TRADE_DATE.strftime('%d-%m-%Y')
        dict_resultado['TRADE_CLOSE'] = obj.TRADE_CLOSE
        dict_resultado['SYMBOL'] = obj.SYMBOL
        dict_resultado['SIDE'] = obj.SIDE
        dict_resultado['ENTRY'] = str(obj.ENTRY)  # Serializa Decimal a cadena
        dict_resultado['STOP_LOSS'] = str(
            obj.STOP_LOSS)  # Serializa Decimal a cadena
        dict_resultado['TARGET_PRICE'] = str(
            obj.TARGET_PRICE)  # Serializa Decimal a cadena
        dict_resultado['PORCENTAJE_ACUMULADO'] = str(
            obj.PORCENTAJE_ACUMULADO)  # Serializa Decimal a cadena
        # Agrega más atributos según sea necesario
        resultados.append(dict_resultado)
        cache.set('bit', resultados)

    # Devuelve la lista de resultados
    return resultados


def convertirHistoria():
    objsHistorial = Historial_Bitacora.objects.all()

    resultadosHistorial = []

    for objH in objsHistorial:
        # Crea un diccionario para cada objeto y agrega los atributos que necesitas
        dict_resultadoHistorial = {}
        dict_resultadoHistorial['UUID'] = str(objH.BITACORA_PRINCIPAL.uuid)
        dict_resultadoHistorial['TRADE_DATE'] = objH.TRADE_DATE.strftime(
            '%d-%m-%Y')
        dict_resultadoHistorial['SYMBOL'] = objH.SYMBOL
        dict_resultadoHistorial['SIDE'] = objH.SIDE
        dict_resultadoHistorial['ENTRY'] = str(
            objH.ENTRY)  # Serializa Decimal a cadena
        dict_resultadoHistorial['STOP_LOSS'] = str(
            objH.STOP_LOSS)  # Serializa Decimal a cadena
        dict_resultadoHistorial['TARGET_PRICE'] = str(
            objH.TARGET_PRICE)  # Serializa Decimal a cadena
        # Agrega más atributos según sea necesario
        dict_resultadoHistorial['PROFIT'] = str(
            objH.PROFIT)
        dict_resultadoHistorial['PORCENTAJE_EJECUTADO'] = str(
            objH.PORCENTAJE_EJECUTADO)
        resultadosHistorial.append(dict_resultadoHistorial)
        cache.set('his', resultadosHistorial)

    return resultadosHistorial


convertir()
convertirHistoria()


def convertirRegistros():
    registros = Bitacora_Principal.objects.order_by('TRADE_DATE')[:3]

    resultadosRegistros = []

    for registro in registros:
        dict_resultadosRegistros = {}

        dict_resultadosRegistros['SYMBOL'] = registro.SYMBOL
        dict_resultadosRegistros['SIDE'] = registro.SIDE
        dict_resultadosRegistros['ENTRY'] = str(registro.ENTRY)

        resultadosRegistros.append(dict_resultadosRegistros)

        cache.set('reg', resultadosRegistros)

    return resultadosRegistros


convertirRegistros()


def data_email(request):

    now = datetime.now()

    data = {}

    if request.method == "POST":
        # Obtén los datos del formulario
        SYMBOL = request.POST.get('SYMBOL')
        SIDE = request.POST.get('SIDE')
        ENTRY = str(request.POST.get('ENTRY'))
        STOP_LOSS = str(request.POST.get('STOP_LOSS'))
        TARGET_PRICE = str(request.POST.get('TARGET_PRICE'))
        PORCENTAJE_EJECUTADO = str(request.POST.get('PORCENTAJE_EJECUTADO'))

        # Crea un diccionario con los datos del formulario
        data = {
            'SYMBOL': SYMBOL,
            'SIDE': SIDE,
            'ENTRY': ENTRY,
            'STOP_LOSS': STOP_LOSS,
            'TARGET_PRICE': TARGET_PRICE,
            'PORCENTAJE_EJECUTADO': PORCENTAJE_EJECUTADO,
        }
        email(data, 'kudacorapps@gmail.com', 'Nuevo trade')


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

    reg = convertirRegistros()
    # cache.set('reg', reg)
    return render(request, 'form.html', {'reg': reg})


def salir(request):
    logout(request)
    return redirect('/')
