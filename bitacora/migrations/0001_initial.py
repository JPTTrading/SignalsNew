# Generated by Django 5.0.6 on 2024-06-30 19:27

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bitacora_Principal',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False,
                 primary_key=True, serialize=False, unique=True)),
                ('trade_date', models.DateTimeField(default='2024-06-30')),
                ('trade_close', models.DateField(
                    blank=True, default=None, null=True)),
                ('symbol', models.CharField(default=None, max_length=255)),
                ('side', models.CharField(default=None, max_length=4)),
                ('entry', models.DecimalField(
                    decimal_places=2, default=0.0, max_digits=10)),
                ('stop_loss', models.DecimalField(blank=True,
                 decimal_places=2, default=0.0, max_digits=10, null=True)),
                ('last_price', models.DecimalField(
                    decimal_places=2, default=0.0, max_digits=10)),
                ('target_price', models.DecimalField(blank=True,
                 decimal_places=2, default=0.0, max_digits=10, null=True)),
                ('porcentaje_acumulado', models.DecimalField(
                    decimal_places=2, default=0.0, max_digits=5, null=True)),
                ('porcentaje_ejecutado', models.DecimalField(
                    decimal_places=2, default=0.0, max_digits=5, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Historial_Bitacora',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('trade_date', models.DateTimeField(auto_now_add=True)),
                ('symbol', models.CharField(default=None, max_length=255)),
                ('side', models.CharField(default=None, max_length=4)),
                ('entry', models.DecimalField(
                    decimal_places=2, default=0.0, max_digits=10)),
                ('stop_loss', models.DecimalField(
                    decimal_places=2, default=0.0, max_digits=10)),
                ('last_price', models.DecimalField(
                    decimal_places=2, default=0.0, max_digits=10)),
                ('target_price', models.DecimalField(
                    decimal_places=2, default=0.0, max_digits=10)),
                ('porcentaje_ejecutado', models.DecimalField(
                    decimal_places=2, default=0.0, max_digits=5)),
                ('profit', models.DecimalField(
                    decimal_places=2, default=0.0, max_digits=10)),
                ('type', models.CharField(default=None, max_length=255, null=True)),
                ('bitacora_principal', models.ForeignKey(db_column='bitacora_principal_uuid',
                 on_delete=django.db.models.deletion.CASCADE, related_name='historial', to='bitacora.bitacora_principal')),
            ],
        ),
    ]
