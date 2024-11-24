from django.db import models
import uuid
from datetime import date
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal
from django.db.models import Avg, Sum
from django.core.cache import cache
import yfinance as yf
# Create your models here.


class Meta:
    db_table = 'bitacora_bitacora_principal'


class Bitacora_Principal(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    trade_date = models.DateTimeField(
        default=date.today().strftime('%Y-%m-%d'))
    trade_close = models.DateField(default=None, blank=True, null=True)
    symbol = models.CharField(max_length=255, default=None)
    side = models.CharField(max_length=4, default=None)  # BUY or SELL
    entry = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    stop_loss = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0, blank=True, null=True)
    last_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)
    target_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0, blank=True, null=True)
    porcentaje_acumulado = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, null=True)  # Campo para el porcentaje ejecutado
    # Otras columnas necesarias
    porcentaje_ejecutado = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, null=True)


class Historial_Bitacora(models.Model):
    id = models.AutoField(primary_key=True)
    bitacora_principal = models.ForeignKey(
        Bitacora_Principal,  # Modelo al que hace referencia
        on_delete=models.CASCADE,  # Qué hacer cuando se borra el objeto relacionado
        # Nombre opcional para acceder a este conjunto de historiales desde un Bitacora_Principal
        related_name='historial',
        db_column='bitacora_principal_uuid',  # Nombre de la columna en la base de datos
    )
    trade_date = models.DateTimeField(auto_now_add=True)
    symbol = models.CharField(max_length=255, default=None)
    side = models.CharField(max_length=4, default=None)  # BUY or SELL
    entry = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    stop_loss = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)
    last_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)
    target_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)
    porcentaje_ejecutado = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00)
    profit = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)
    type = models.CharField(max_length=255, default=None,
                            null=True)  # Tipo de operación

    # def calcular_take_profit(self, new_trade_date, new_take_profit_entry, new_percentage, new_stop_loss=None, new_last=None, new_target_price=None):
    #     # Realizar el cálculo
    #     existing_entry = self.ENTRY
    #     existing_percentage = self.PORCENTAJE_EJECUTADO
    #     take_profit = 1 - ((existing_entry * (new_percentage/100)) /
    #                        (new_take_profit_entry * (new_percentage/100)))

    #     # Actualizar el modelo actual
    #     self.TARGET_PRICE = new_target_price
    #     self.PORCENTAJE_EJECUTADO = 100  # Establecer el PORCENTAJE_EJECUTADO en 100%
    #     self.save()

    #     # Crear un nuevo registro en HistorialBitacora
    #     Historial_Bitacora.objects.create(
    #         BITACORA_PRINCIPAL=self,
    #         TRADE_DATE=new_trade_date,
    #         SYMBOL=self.SYMBOL,
    #         # Otras columnas necesarias en el historial
    #     )


@receiver(pre_save, sender=Bitacora_Principal)
def set_trade_close(sender, instance, **kwargs):
    if instance.porcentaje_acumulado == 0 and not instance.trade_close:
        # Obtener el UUID antes de asignar TRADE_CLOSE
        existing_uuid = instance.uuid

        # Asignar TRADE_CLOSE con timezone.now()
        instance.trade_close = timezone.now()

        # Imprimir el UUID
        print(f"UUID para TRADE_CLOSE {existing_uuid}: {instance.trade_close}")

        # Lógica adicional para actualizar el historial y ENTRY
        historial_entry = Historial_Bitacora.objects.filter(
            bitacora_principal__uuid=existing_uuid
        ).order_by('trade_date').first()

        if historial_entry:
            if historial_entry.side == 'SELL':
                # Si el registro es "Sell", calcular el precio promedio ponderado de los registros "Buy"
                buy_entries = Historial_Bitacora.objects.filter(
                    bitacora_principal=instance, side='BUY')

                if buy_entries.exists():
                    total_weight_buy = buy_entries.aggregate(Sum('porcentaje_ejecutado'))[
                        'porcentaje_ejecutado__sum']
                    weighted_average_price_buy = buy_entries.aggregate(
                        Avg('entry', weight='porcentaje_ejecutado'))['entry__avg']

                    # Actualizar el ENTRY del Bitacora_Principal con el precio promedio ponderado de "Buy"
                    instance.entry = weighted_average_price_buy

                    # Actualizar el PRICE del Bitacora_Principal con el primer ENTRY del historial
                    instance.precio_actual = historial_entry.entry

                    # Guardar la instancia actualizada
                    # instance.save()

                else:
                    # Si no hay registros "Buy", podrías manejar este caso según tus necesidades
                    pass

            else:
                # Si el registro es "Buy", calcular el precio promedio ponderado de los registros "Sell"
                sell_entries = Historial_Bitacora.objects.filter(
                    bitacora_principal=instance, side='SELL')

                if sell_entries.exists():
                    total_weight_sell = sell_entries.aggregate(Sum('porcentaje_ejecutado'))[
                        'porcentaje_ejecutado__sum']
                    weighted_average_price_sell = sell_entries.aggregate(
                        Avg('entry', weight='porcentaje_ejecutado'))['entry__avg']

                    # Actualizar el ENTRY del Bitacora_Principal con el precio promedio ponderado de "Sell"
                    instance.entry = weighted_average_price_sell

                    # Actualizar el PRICE del Bitacora_Principal con el primer ENTRY del historial
                    instance.precio_actual = historial_entry.entry

                    # Guardar la instancia actualizada
                    # instance.save()

                else:
                    # Si no hay registros "Sell", podrías manejar este caso según tus necesidades
                    pass

        else:
            # Si no se encuentra el historial_entry, podrías manejar este caso según tus necesidades
            pass
    else:
        # Filtrar los registros que cumplen con las condiciones
        bitacoras_to_update = Bitacora_Principal.objects.filter(
            porcentaje_acumulado__gt=0,
            trade_close__isnull=True
        )

        # Utilizar el símbolo de la operación para obtener datos de precios desde Yahoo Finance
        for bitacora_to_update in bitacoras_to_update:
            uuid = bitacora_to_update.uuid
            symbol = bitacora_to_update.symbol

            cache_key = f"yahoo_data_{symbol}"
            data = cache.get(cache_key)
            if data is not None and not data.empty and 'Close' in data:
                # Verificar si hay datos disponibles antes de intentar acceder a 'Close'
                last_close_price = data['Close'].iloc[-1]
                # Precio de cierre actual
                Bitacora_Principal.objects.filter(uuid=uuid).update(
                    precio_actual=last_close_price
                )
                print(
                    f"Precio actualizado para {symbol}: {last_close_price}")
            else:
                print(f"No se encontraron datos de precios para {symbol}")
