# Generated by Django 4.2.5 on 2023-12-29 14:58

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bitacora_Principal',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('TRADE_DATE', models.DateTimeField(default='2023-12-29')),
                ('TRADE_CLOSE', models.DateField(blank=True, default=None, null=True)),
                ('SYMBOL', models.CharField(default=None, max_length=255)),
                ('SIDE', models.CharField(default=None, max_length=4)),
                ('ENTRY', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('STOP_LOSS', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('LAST', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('TARGET_PRICE', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('PORCENTAJE_ACUMULADO', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('PORCENTAJE_EJECUTADO', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
            ],
        ),
        migrations.CreateModel(
            name='Historial_Bitacora',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('TRADE_DATE', models.DateTimeField(default='2023-12-29')),
                ('SYMBOL', models.CharField(default=None, max_length=255)),
                ('SIDE', models.CharField(default=None, max_length=4)),
                ('ENTRY', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('STOP_LOSS', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('LAST', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('TARGET_PRICE', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('PORCENTAJE_EJECUTADO', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('PROFIT', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('BITACORA_PRINCIPAL', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bitacora.bitacora_principal')),
            ],
        ),
    ]
