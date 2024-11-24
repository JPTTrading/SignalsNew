from django_plotly_dash import DjangoDash
from dash import html, Input, Output, dcc, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from django.core.cache import cache
from dash.dash_table import DataTable
import pandas as pd
from .models import Bitacora_Principal, Historial_Bitacora
from django.db.models import Sum

trade_date = 'trade date'
stop_loss = 'stop loss'
target_price = 'target price'


app = DjangoDash(name='bitacora_app', external_stylesheets=[
    dbc.themes.BOOTSTRAP])

# Agregar el switch para filtrar posiciones abiertas y cerradas
switch = dbc.CardGroup(
    [
        dbc.RadioItems(
            id="switch-input",
            className='switch',
            options=[
                {"label": "Posiciones abiertas", "value": "open"},
                {"label": "Posiciones cerradas", "value": "closed"},
            ],
            value="open",
        ),
    ],
    className='switch-container'
)

tabla_bitacora = [
    dict(id='trade_date', name=trade_date),
    dict(id='trade_close', name='trade close'),
    dict(id='symbol', name='symbol'),
    dict(id='price', name='price'),
    dict(id='side', name='side'),
    dict(id='entry', name='entry'),
    dict(id='stop_loss', name=stop_loss),
    dict(id='target_price', name=target_price),
    dict(id='porcentaje_acumulado', name='% ' + 'live'),
    dict(id='gl', name='% ' + 'g/l'),
]

tabla_ejecuciones = [
    dict(id='trade_date', name=trade_date, sort_by='asceding'),
    dict(id='symbol', name='symbol'),
    dict(id='side', name='side'),
    dict(id='entry', name='entry'),
    dict(id='stop_loss', name=stop_loss),
    dict(id='target_price', name=target_price),
    dict(id='profit', name='% ' + 'g/l'),
    dict(id='porcentaje_ejecutado', name='% ' + 'executed'),
]

header = dbc.Row(
    [html.Img(src='/static/img/logo_light.png', className="logo")])

rentabilidad = html.Div(
    id='rentabilidad',
    className='rentabilidad-texto', 
    )

bitacora = dcc.Loading(
    type='circle',
    fullscreen=True,
    color="#2F2E2E",
    children=dbc.Row(
        [
            DataTable(
                id='bit_data',
                columns=tabla_bitacora,
                data=[],
                style_header={
                    'color': 'white',
                    'textAlign': 'center',
                    'fontWeight': 'bold',
                    'border': 'none',
                    'background-color': 'Black',
                },
                style_cell={
                    'textAlign': 'center',
                    'border': 'None',
                },
                style_table={
                    'border': '1px solid white',
                    'border-collapse': 'collapse',
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(240,240,240)',
                    },
                    {
                        'if': {
                            'filter_query': '{side} = Buy || {side} = Buy',
                            'column_id': 'side'
                        },
                        'backgroundColor': 'green',
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{side} = "Sell"  || {side} = "Sell"',
                            'column_id': 'side'
                        },
                        'backgroundColor': 'tomato',
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{gl} < 0',
                            'column_id': 'gl'
                        },
                        'backgroundColor': 'LightSalmon',
                        'color': 'red'
                    },
                    {
                        'if': {
                            'filter_query': '{gl} > 0',
                            'column_id': 'gl'
                        },
                        'backgroundColor': 'LightGreen',
                        'color': 'green'
                    },
                    {
                        'if': {
                            'state': 'active'
                        },
                        'backgroundColor': '#FDC500 ',
                        'border': 'none'
                    }
                ],
            )
        ],
        className='tabla',
        id="bitacora_tactical"
    )
)

ejecuciones = dcc.Loading(
    type='circle',
    color="white",
    children=dbc.Row(
        [
            DataTable(
                id='data_ejec',
                data=[],
                columns=tabla_ejecuciones,
                style_header={
                    'backgroundColor': 'black',
                    'color': 'white',
                    'textAlign': 'center',
                    'fontWeight': 'bold',
                    'table-layout': 'auto',
                },
                style_cell={
                    'textAlign': 'center',
                    'border': 'none',
                },
                style_table={
                    'border': '1px solid white',
                    'table-layout': 'auto',
                },
                style_data_conditional=[
                    {
                        'if': {
                            'state': 'active'
                        },
                        'backgroundColor': '#FDC500',
                        'border': 'none'
                    },
                    {
                        'if': {
                            'filter_query': '{side} = Buy  || {side} = Buy',
                            'column_id': 'side'
                        },
                        'backgroundColor': 'green',
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{side} = "Sell"  || {side} = "Sell"',
                            'column_id': 'side'
                        },
                        'backgroundColor': 'tomato',
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{gl} < 0',
                            'column_id': 'profit'
                        },
                        'backgroundColor': 'DarkSalmon',
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{gl} > 0',
                            'column_id': 'profit'
                        },
                        'backgroundColor': 'LightGreen',
                        'color': 'white'
                    },
                ]
            ),
        ],
        className='tabla_ejecucion',
        id='ejecuciones_tactical'
    )
)

app.layout = html.Div(
    children=[
        header,
        switch,  # Añadir el switch al layout
        rentabilidad,
        bitacora,
        ejecuciones,
        dcc.Location(id='url', refresh=False),
    ],
)


@app.callback(
    [
        Output(component_id='bit_data', component_property='data'),
        Output(component_id='bit_data', component_property='columns'),
        Output(component_id='rentabilidad', component_property='children'),
        Output(component_id='rentabilidad', component_property='style'),
    ],
    [
        Input(component_id='url', component_property='href'),
        Input(component_id='switch-input', component_property='value')
    ],
    prevent_initial_call=True
)
def inicio_tabla(href, switch_value):
    try:
        objs = obtener_datos_filtrados(switch_value)
        df = crear_dataframe(objs)

        if df.empty:
            raise PreventUpdate

        precios = cache.get('precios_symbols', {})
        df = calcular_gl(df, precios)
            
        resultados, tabla_bitacora = procesar_resultados(df, switch_value)
        rentabilidad_texto, rentabilidad_style = calcular_rentabilidad(resultados, switch_value)

        return resultados.to_dict('records'), tabla_bitacora, rentabilidad_texto, rentabilidad_style
    except Exception as e:
        print(f"Error in callback: {e}")
        raise PreventUpdate

# Función para filtrar los datos según el switch_value
def obtener_datos_filtrados(switch_value):
    if switch_value == 'open':
        return Bitacora_Principal.objects.filter(trade_close__isnull=True).order_by('trade_date')
    elif switch_value == 'closed':
        return Bitacora_Principal.objects.filter(trade_close__isnull=False).order_by('trade_date') 
    return Bitacora_Principal.objects.all().order_by('-trade_date')


# Función para crear el DataFrame
def crear_dataframe(objs):
    resultados = [
        {
            'uuid': str(obj.uuid),
            'trade_date': obj.trade_date.strftime('%d-%m-%Y'),
            'trade_close': obj.trade_close,
            'symbol': obj.symbol,
            'side': obj.side,
            'entry': obj.entry,
            'stop_loss': obj.stop_loss,
            'target_price': obj.target_price,
            'porcentaje_acumulado': obj.porcentaje_acumulado,
        }
        for obj in objs
    ]
    return pd.DataFrame(resultados)


# Función para calcular g/l
def calcular_gl(df, precios):
    for index, row in df.iterrows():
        symbol = row['symbol']
        price = precios.get(symbol, 'N/A')
        df.at[index, 'price'] = price

        if price != 'N/A':
            entry = float(row['entry'])
            if row['side'] == 'Buy':
                df.at[index, 'gl'] = round(((price - entry) / entry) * 100, 2)
            elif row['side'] == 'Sell':
                df.at[index, 'gl'] = round(((entry - price) / entry) * 100, 2)
        else:
            df.at[index, 'gl'] = 0
    return df


# Función para procesar los resultados y la tabla
def procesar_resultados(df, switch_value):
    if switch_value == 'open':
        resultados = df[df['trade_close'].isnull()]
        tabla_bitacora = [
            {'id': 'trade_date', 'name': 'trade_date'},
            {'id': 'symbol', 'name': 'symbol'},
            {'id': 'price', 'name': 'price'},
            {'id': 'side', 'name': 'side'},
            {'id': 'entry', 'name': 'entry'},
            {'id': 'stop_loss', 'name': 'stop_loss'},
            {'id': 'target_price', 'name': 'target_price'},
            {'id': 'porcentaje_acumulado', 'name': '% ' + 'live'},
            {'id': 'gl', 'name': '% ' + 'g/l'},
        ]
    elif switch_value == 'closed':
        resultados = df[df['trade_close'].notnull()]
        tabla_bitacora = [
            {'id': 'trade_date', 'name': 'trade_date'},
            {'id': 'trade_close', 'name': 'trade_close'},
            {'id': 'symbol', 'name': 'symbol'},
            {'id': 'side', 'name': 'side'},
            {'id': 'entry', 'name': 'entry'},
            {'id': 'stop_loss', 'name': 'stop_loss'},
            {'id': 'target_price', 'name': 'target_price'},
            {'id': 'porcentaje_acumulado', 'name': '% ' + 'live'},
        ]
    return resultados, tabla_bitacora


# Función para calcular la rentabilidad
def calcular_rentabilidad(resultados, switch_value):
    if switch_value == 'open':
        rentabilidad = resultados['gl'].fillna(0).sum() if 'gl' in resultados.columns else 0
        rentabilidad_texto = f"Rentabilidad Total: {rentabilidad:.2f}%"
        rentabilidad_style = {'display': 'block'}
    else:
        # Usar aggregate para obtener el total de profit
        total_profit = Historial_Bitacora.objects.aggregate(total_profit=Sum('profit'))['total_profit']
        rentabilidad_texto = f"Rentabilidad Total: {total_profit:.2f}%"
        rentabilidad_style = {'display': 'block'}
    return rentabilidad_texto, rentabilidad_style


@app.callback(
    Output(component_id='data_ejec', component_property='data'),
    Output(component_id='ejecuciones_tactical', component_property='style'),
    Input(component_id='bit_data', component_property='active_cell'),
    State(component_id='bit_data', component_property='data'),
    prevent_initial_call=True
)
def tabla_ejecuciones(active_cell, data):
    if active_cell is None:
        raise PreventUpdate

    uuid = data[active_cell['row']]['uuid']
    objs_historial = Historial_Bitacora.objects.filter(bitacora_principal__uuid=uuid).order_by('trade_date')

    # Crear una lista para almacenar los resultados individuales
    resultados_historial = []

    for obj_h in objs_historial:
        # Crear un diccionario para cada objeto y agregar los atributos necesarios
        dict_resultado_historial = {}
        dict_resultado_historial['uuid'] = str(obj_h.bitacora_principal.uuid)
        dict_resultado_historial['trade_date'] = obj_h.trade_date.strftime('%d-%m-%Y')
        dict_resultado_historial['symbol'] = obj_h.symbol
        dict_resultado_historial['side'] = obj_h.side
        dict_resultado_historial['entry'] = str(obj_h.entry)  # Serializar Decimal a cadena si es necesario
        dict_resultado_historial['stop_loss'] = str(obj_h.stop_loss)  # Serializar Decimal a cadena si es necesario
        dict_resultado_historial['target_price'] = str(obj_h.target_price)  # Serializar Decimal a cadena si es necesario
        dict_resultado_historial['profit'] = str(obj_h.profit)  # Serializar Decimal a cadena si es necesario
        dict_resultado_historial['porcentaje_ejecutado'] = str(obj_h.porcentaje_ejecutado)  # Serializar Decimal a cadena si es necesario
        # Agregar más atributos según sea necesario
        resultados_historial.append(dict_resultado_historial)

    # Convertir la lista de resultados a DataFrame de pandas
    dfh = pd.DataFrame(resultados_historial)


    if dfh.empty:
        raise PreventUpdate


    ejecuciones_style = {'display': 'block'} if not dfh.empty else {'display': 'none'}

    # Devolver los datos y el estilo para la tabla de ejecuciones
    return dfh.to_dict('records'), ejecuciones_style



def actualizar_gl(objeto):
    # Lógica para calcular o actualizar el campo GL (ganancia/pérdida)
    if objeto.price:
        gl = (objeto.price - objeto.entry) / objeto.entry * 100
        return f"{gl:.2f}%"
    else:
        return "N/A"




if __name__ == '__main__':
    app.run_server()
