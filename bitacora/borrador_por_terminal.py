# este codigo sirve para meter datos desde terminal, lo dejo para pruebas

# cuando comente la opción manual debo mover el return para que funcione esta parte
# else:
#     # -------------------Desde aqui ----------------#
#     # En este caso, ingresa los datos por la terminal
#     SYMBOL = input("Ingrese el símbolo: ")
#     SIDE = input("Ingrese el lado (Buy o Sell): ")
#     ENTRY = Decimal(input("Ingrese el precio: "))
#     STOP_LOSS = Decimal(input("Ingrese el stop loss: "))
#     TARGET_PRICE = Decimal(input("Ingrese el precio objetivo: "))
#     PORCENTAJE_EJECUTADO = Decimal(
#         input("Ingrese porcentaje de ejecucion: "))
#     # Verifica si el símbolo ya existe en la tabla BitacoraPrincipal
#     existing_entry = Bitacora_Principal.objects.filter(
#         SYMBOL=SYMBOL).first()

#     print(existing_entry)

#     if existing_entry:
#         # Si el símbolo existe en BitacoraPrincipal, verifica el SIDE

#         # Verifica el SIDE de la nueva operación
#         # Si el SIDE es contrario, suma el porcentaje ejecutado
#         # Si el SIDE es el mismo, resta el porcentaje ejecutado
#         if existing_entry.SIDE != SIDE:
#             Bitacora_Principal.objects.filter(SYMBOL=SYMBOL).update(
#                 PORCENTAJE_EJECUTADO=F(
#                     'PORCENTAJE_EJECUTADO') - PORCENTAJE_EJECUTADO
#             )
#         else:
#             Bitacora_Principal.objects.filter(SYMBOL=SYMBOL).update(
#                 PORCENTAJE_EJECUTADO=F(
#                     'PORCENTAJE_EJECUTADO') + PORCENTAJE_EJECUTADO
#             )

#         # Verifica si se alcanzó el 100% de ejecución en el Bitacora_Principal
#         if existing_entry.PORCENTAJE_EJECUTADO <= 0:
#             existing_entry.TRADE_CLOSE = timezone.now()
#             existing_entry.save()
#         # Si el símbolo existe en BitacoraPrincipal, verifica el SIDE
#         if existing_entry.SIDE == SIDE and existing_entry.SYMBOL == SYMBOL:
#             # Calcula el porcentaje ejecutado de la operación existente
#             existing_percentage = existing_entry.PORCENTAJE_EJECUTADO

#             # Calcula el porcentaje ejecutado de la nueva operación
#             new_percentage = PORCENTAJE_EJECUTADO

#             # Calcula el valor actualizado de ENTRY
#             new_entry = ((existing_percentage / 100) * existing_entry.ENTRY +
#                          (new_percentage / 100) * ENTRY) / ((existing_percentage / 100) + (new_percentage / 100))

#             # Actualiza el valor de ENTRY en la operación existente
#             existing_entry.ENTRY = new_entry
#             existing_entry.PORCENTAJE_EJECUTADO += new_percentage
#             existing_entry.save()
#             historial_data = Historial_Bitacora(
#                 BITACORA_PRINCIPAL=existing_entry,
#                 SYMBOL=SYMBOL,
#                 SIDE=SIDE,
#                 ENTRY=ENTRY,
#                 STOP_LOSS=STOP_LOSS,
#                 TARGET_PRICE=TARGET_PRICE,
#                 PORCENTAJE_EJECUTADO=PORCENTAJE_EJECUTADO
#             )
#             historial_data.save()
#         else:
#             # Si el SIDE es diferente, crea un registro en HistorialBitacora y realiza los cálculos de profit
#             historial_data = Historial_Bitacora(
#                 BITACORA_PRINCIPAL=existing_entry,
#                 SYMBOL=SYMBOL,
#                 SIDE=SIDE,
#                 ENTRY=ENTRY,
#                 STOP_LOSS=STOP_LOSS,
#                 TARGET_PRICE=TARGET_PRICE,
#                 PORCENTAJE_EJECUTADO=PORCENTAJE_EJECUTADO
#             )
#             historial_data.save()
#             # Calcula el profit para el nuevo registro en el historial
#             historial_data.calcular_profit()
#             historial_data.save()
#     else:
#         # Si el símbolo no existe en Bitacora_Principal, crea un nuevo registro
#         # UUID = UUID_Auto
#         new_bitacora = Bitacora_Principal(
#             SYMBOL=SYMBOL,
#             SIDE=SIDE,
#             ENTRY=ENTRY,
#             STOP_LOSS=STOP_LOSS,
#             TARGET_PRICE=TARGET_PRICE,
#             PORCENTAJE_EJECUTADO=PORCENTAJE_EJECUTADO,
#         )
#         new_bitacora.save()

#         # Luego, crea un registro en HistorialBitacora relacionándolo con el nuevo BitacoraPrincipal
#         historial_data = Historial_Bitacora(
#             BITACORA_PRINCIPAL=new_bitacora,
#             SYMBOL=SYMBOL,
#             SIDE=SIDE,
#             ENTRY=ENTRY,
#             STOP_LOSS=STOP_LOSS,
#             TARGET_PRICE=TARGET_PRICE,
#             # Establece el porcentaje inicial como lo ponga en input
#             PORCENTAJE_EJECUTADO=PORCENTAJE_EJECUTADO,
#         )
#         historial_data.save()
#     data = convertir()
#     dataHis = convertirHistoria()
#     cache.set('bit', data)
#     cache.set('his', dataHis)

#     return render(request, 'bitacora.html')
# ---------------Hasta Aqui------------------#
