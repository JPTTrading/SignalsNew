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


class Bitacora_Principal(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    TRADE_DATE = models.DateTimeField(
        default=date.today().strftime('%Y-%m-%d'))
    TRADE_CLOSE = models.DateField(default=None, blank=True, null=True)
    SYMBOL = models.CharField(max_length=255, default=None)
    SIDE = models.CharField(max_length=4, default=None)  # BUY or SELL
    ENTRY = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    STOP_LOSS = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0, blank=True, null=True)
    LAST = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    TARGET_PRICE = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0, blank=True, null=True)
    PORCENTAJE_ACUMULADO = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00)  # Campo para el porcentaje ejecutado
    # Otras columnas necesarias
    PORCENTAJE_EJECUTADO = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00)

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


class Historial_Bitacora(models.Model):
    BITACORA_PRINCIPAL = models.ForeignKey(
        Bitacora_Principal, on_delete=models.CASCADE)
    TRADE_DATE = models.DateTimeField(
        default=date.today().strftime('%Y-%m-%d'))
    SYMBOL = models.CharField(max_length=255, default=None)
    SIDE = models.CharField(max_length=4, default=None)  # BUY or SELL
    ENTRY = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    STOP_LOSS = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)
    LAST = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    TARGET_PRICE = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)
    PORCENTAJE_EJECUTADO = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00)
    PROFIT = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)
    type = models.CharField(max_length=255, default=None,
                            null=True)  # Tipo de operación


@receiver(pre_save, sender=Bitacora_Principal)
def set_trade_close(sender, instance, **kwargs):
    if instance.PORCENTAJE_ACUMULADO == 0 and not instance.TRADE_CLOSE:
        # Obtener el UUID antes de asignar TRADE_CLOSE
        existing_uuid = instance.uuid

        # Asignar TRADE_CLOSE con timezone.now()
        instance.TRADE_CLOSE = timezone.now()

        # Imprimir el UUID
        print(f"UUID para TRADE_CLOSE {existing_uuid}: {instance.TRADE_CLOSE}")

        # Lógica adicional para actualizar el historial y ENTRY
        historial_entry = Historial_Bitacora.objects.filter(
            BITACORA_PRINCIPAL__uuid=existing_uuid
        ).order_by('TRADE_DATE').first()

        if historial_entry:
            if historial_entry.SIDE == 'SELL':
                # Si el registro es "Sell", calcular el precio promedio ponderado de los registros "Buy"
                buy_entries = Historial_Bitacora.objects.filter(
                    BITACORA_PRINCIPAL=instance, SIDE='BUY')

                if buy_entries.exists():
                    total_weight_buy = buy_entries.aggregate(Sum('PORCENTAJE_EJECUTADO'))[
                        'PORCENTAJE_EJECUTADO__sum']
                    weighted_average_price_buy = buy_entries.aggregate(
                        Avg('ENTRY', weight='PORCENTAJE_EJECUTADO'))['ENTRY__avg']

                    # Actualizar el ENTRY del Bitacora_Principal con el precio promedio ponderado de "Buy"
                    instance.ENTRY = weighted_average_price_buy

                    # Actualizar el PRICE del Bitacora_Principal con el primer ENTRY del historial
                    instance.PRECIO_ACTUAL = historial_entry.ENTRY

                    # Guardar la instancia actualizada
                    # instance.save()

                else:
                    # Si no hay registros "Buy", podrías manejar este caso según tus necesidades
                    pass

            else:
                # Si el registro es "Buy", calcular el precio promedio ponderado de los registros "Sell"
                sell_entries = Historial_Bitacora.objects.filter(
                    BITACORA_PRINCIPAL=instance, SIDE='SELL')

                if sell_entries.exists():
                    total_weight_sell = sell_entries.aggregate(Sum('PORCENTAJE_EJECUTADO'))[
                        'PORCENTAJE_EJECUTADO__sum']
                    weighted_average_price_sell = sell_entries.aggregate(
                        Avg('ENTRY', weight='PORCENTAJE_EJECUTADO'))['ENTRY__avg']

                    # Actualizar el ENTRY del Bitacora_Principal con el precio promedio ponderado de "Sell"
                    instance.ENTRY = weighted_average_price_sell

                    # Actualizar el PRICE del Bitacora_Principal con el primer ENTRY del historial
                    instance.PRECIO_ACTUAL = historial_entry.ENTRY

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
            PORCENTAJE_ACUMULADO__gt=0,
            TRADE_CLOSE__isnull=True
        )

        # Utilizar el símbolo de la operación para obtener datos de precios desde Yahoo Finance
        for bitacora_to_update in bitacoras_to_update:
            uuid = bitacora_to_update.uuid
            symbol = bitacora_to_update.SYMBOL

            cache_key = f"yahoo_data_{symbol}"
            data = cache.get(cache_key)
            if data is not None and not data.empty and 'Close' in data:
                # Verificar si hay datos disponibles antes de intentar acceder a 'Close'
                last_close_price = data['Close'].iloc[-1]
                # Precio de cierre actual
                Bitacora_Principal.objects.filter(uuid=uuid).update(
                    PRECIO_ACTUAL=last_close_price
                )
                print(
                    f"Precio actualizado para {symbol}: {last_close_price}")
            else:
                print(f"No se encontraron datos de precios para {symbol}")
