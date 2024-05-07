import pandas as pd
from datetime import date


def take_profit(take_profit_Symbol: str,
                take_profit_side: str,
                take_profit_entry: float,
                new_stop_loss: float,
                new_last: float,
                new_target_price: float,
                new_percentage: float):

    # def take_profit():
    #     # Entrada de nuevos datos
    #     take_profit_Symbol = input("Ingrese el nuevo símbolo: ").upper()
    #     take_profit_side = input("Ingrese el lado (BUY o SELL): ").upper()
    #     take_profit_entry = float(input("Ingrese el nuevo valor de ENTRY: "))
    #     new_stop_loss = float(input("Ingrese el nuevo valor de STOP LOSS: "))
    #     new_last = float(input("Ingrese el nuevo valor de LAST: "))
    #     new_target_price = float(input("Ingrese el nuevo valor de TARGET PRICE: "))
    #     new_percentage = float(
    #         input("Ingrese el nuevo porcentaje de participación: "))

    # Leer el archivo Excel existente
    existing_df = pd.read_excel("Bitacora.xlsx")

    # Verificar si el símbolo ya existe en el DataFrame
    if take_profit_Symbol in existing_df["SYMBOL"].values:
        # Obtener las columnas relevantes existentes
        relevant_columns = [col for col in existing_df.columns if col.startswith(
            ('PRICE_PROFIT_', 'TAKE_PROFIT_', '%_PROFIT_', 'TRAILING_STOP_'))]

        # Encontrar el número máximo en las columnas relevantes existentes
        max_number = max([int(col.split('_')[2]) for col in relevant_columns])

        # Verificar si todas las columnas relevantes están llenas
        if all(existing_df[existing_df["SYMBOL"] == take_profit_Symbol][col].notna().all() for col in relevant_columns):
            # Obtener el número máximo en las columnas relevantes existentes
            max_number = max([int(col.split('_')[2])
                             for col in relevant_columns])

            # Realizar el cálculo para el nuevo ENTRY
            existing_entry = existing_df.loc[existing_df["SYMBOL"]
                                             == take_profit_Symbol, "ENTRY"].values[0]
            existing_percentage = existing_df.loc[existing_df["SYMBOL"]
                                                  == take_profit_Symbol, "%_EXECUTE"].values[0]
            target_price = existing_df.loc[existing_df["SYMBOL"]
                                           == new_target_price, "TARGET_PRICE"].values[0]
            take_profit = 1 - ((existing_entry * (new_percentage/100)) /
                               (take_profit_entry * (new_percentage/100)))
            # Crear las nuevas columnas a partir del último número encontrado
            new_profit_price_column = f"PRICE_PROFIT_{max_number+ 1 }"
            new_take_profit_column = f"TAKE_PROFIT_{max_number + 1}"
            new_profit_column = f"%_PROFIT_{max_number + 1}"
            new_trailing_stop_column = f"TRAILING_STOP_{max_number + 1}"

            # Asignar los nuevos datos a las columnas correspondientes
            existing_df.loc[existing_df["SYMBOL"] == take_profit_Symbol,
                            new_take_profit_column] = take_profit
            existing_df.loc[existing_df["SYMBOL"] ==
                            take_profit_Symbol, new_profit_column] = new_percentage
            existing_df.loc[existing_df["SYMBOL"] == take_profit_Symbol,
                            new_trailing_stop_column] = new_stop_loss
            existing_df.loc[existing_df["SYMBOL"] == take_profit_Symbol,
                            new_profit_price_column] = take_profit_entry

        else:
            # Realizar el cálculo para el nuevo ENTRY
            existing_entry = existing_df.loc[existing_df["SYMBOL"]
                                             == take_profit_Symbol, "ENTRY"].values[0]
            existing_percentage = existing_df.loc[existing_df["SYMBOL"]
                                                  == take_profit_Symbol, "%_EXECUTE"].values[0]
            take_profit = 1 - ((existing_entry * (new_percentage/100)) /
                               (take_profit_entry * (new_percentage/100)))
            # En caso de que no todas las columnas estén llenas, buscar la primera columna vacía de cada tipo y llenarla
            for suffix in ['%_PROFIT_', 'TRAILING_STOP_', 'TAKE_PROFIT_', 'PRICE_PROFIT_']:
                empty_column = None
                for i in range(1, max_number + 2):
                    column_name = f"{suffix}{i}"
                    if column_name not in relevant_columns:
                        empty_column = column_name
                        break
                    elif existing_df[existing_df["SYMBOL"] == take_profit_Symbol][column_name].isna().any():
                        empty_column = column_name
                        break
                if empty_column:
                    if suffix == '%_PROFIT_':
                        existing_df.loc[existing_df["SYMBOL"] ==
                                        take_profit_Symbol, empty_column] = new_percentage
                    elif suffix == 'TRAILING_STOP_':
                        existing_df.loc[existing_df["SYMBOL"] ==
                                        take_profit_Symbol, empty_column] = new_stop_loss
                    elif suffix == 'TAKE_PROFIT_':
                        existing_df.loc[existing_df["SYMBOL"] ==
                                        take_profit_Symbol, empty_column] = take_profit
                    elif suffix == 'PRICE_PROFIT_':
                        existing_df.loc[existing_df["SYMBOL"] ==
                                        take_profit_Symbol, empty_column] = take_profit_entry

    else:
        fecha_hora = date.today()
        # Agregar nuevos datos al DataFrame
        new_data = {
            "TRADE_DATE": fecha_hora,
            "SYMBOL": take_profit_Symbol,
            "SIDE": take_profit_side,
            "ENTRY": take_profit_entry,
            "STOP_LOSS": new_stop_loss,
            "LAST": new_last,
            "TARGET_PRICE": new_target_price,
        }

        existing_df = existing_df._append(new_data, ignore_index=True)

    # Guardar el DataFrame actualizado en el archivo Excel
    existing_df.to_excel("Bitacora.xlsx", index=False)


def new_entry(new_symbol: str,
              new_side: str,
              new_entry: float,
              new_stop_loss: float,
              new_last: float,
              new_target_price: float,
              new_percentage: float):

    # Leer el archivo Excel existente
    existing_df = pd.read_excel("Bitacora.xlsx")

    # Entrada de nuevos datos
    # new_symbol = input("Ingrese el nuevo símbolo: ").upper()
    # new_trade_date = input("Ingrese la fecha de operación (dd/mm/aaaa): ")
    # new_trade_close = input("Ingrese la fecha de cierre (dd/mm/aaaa): ")
    # new_side = input("Ingrese el lado (BUY o SELL): ").upper()
    # new_entry = float(input("Ingrese el nuevo valor de ENTRY: "))
    # new_stop_loss = float(input("Ingrese el nuevo valor de STOP LOSS: "))
    # new_last = float(input("Ingrese el nuevo valor de LAST: "))
    # new_target_price = float(input("Ingrese el nuevo valor de TARGET PRICE: "))
    # new_percentage = float(input("Ingrese el nuevo porcentaje de participación: "))

    # Verificar si el nuevo símbolo ya existe en la columna "SYMBOL"
    if new_symbol in existing_df["SYMBOL"].values:
        # Encontrar la fila correspondiente al símbolo existente
        existing_entry = existing_df.loc[existing_df["SYMBOL"]
                                         == new_symbol, "ENTRY"].values[0]
        existing_percentage = existing_df.loc[existing_df["SYMBOL"]
                                              == new_symbol, "%_EXECUTE"].values[0]

        # Realizar la operación de cálculo para el nuevo ENTRY
        new_entry = (((existing_percentage/100)-(new_percentage/100)) * existing_entry) + \
            (new_entry * (new_percentage/100))
        new_percentage = 100  # Establecer el %_EXECUTE en 100%

        # Actualizar el DataFrame con los nuevos valores
        existing_df.loc[existing_df["SYMBOL"]
                        == new_symbol, "ENTRY"] = new_entry
        existing_df.loc[existing_df["SYMBOL"]
                        == new_symbol, "TARGET_PRICE"] = new_target_price
        existing_df.loc[existing_df["SYMBOL"] ==
                        new_symbol, "%_EXECUTE"] = new_percentage

    else:
        # Agregar nuevos datos al DataFrame
        new_data = {
            "SYMBOL": new_symbol,
            "SIDE": new_side,
            "ENTRY": new_entry,
            "STOP_LOSS": new_stop_loss,
            "LAST": new_last,
            "TARGET_PRICE": new_target_price,
            "%_EXECUTE": 1,
        }
        existing_df = existing_df._append(new_data, ignore_index=True)

    # Guardar el DataFrame actualizado en el archivo Excel
    existing_df.to_excel("Bitacora.xlsx", index=False, mode='a', header=False)


if __name__ == "__main__":
    take_profit()
