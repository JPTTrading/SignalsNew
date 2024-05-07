from django_plotly_dash import DjangoDash
import dash
from dash import html, Input, Output, dcc, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash.dash_table import DataTable, FormatTemplate
from dash.dash_table.Format import Format
from django.core.cache import cache
import plotly.express as px
import pandas as pd
from .views import convertir
from datetime import date
import yfinance as yf


app = DjangoDash(name='bitacora_app', external_stylesheets=[
                 dbc.themes.BOOTSTRAP])


tabla_bitacora = [
    dict(id='TRADE_DATE', name='TRADE DATE'),
    dict(id='TRADE_CLOSE', name='TRADE CLOSE'),
    dict(id='SYMBOL', name='SYMBOL'),
    dict(id='PRICE', name='PRICE'),
    dict(id='SIDE', name='SIDE'),
    dict(id='ENTRY', name='ENTRY'),
    dict(id='STOP_LOSS', name='STOP LOSS'),
    dict(id='TARGET_PRICE', name='TARGET PRICE'),
    dict(id='PORCENTAJE_ACUMULADO', name='% ' + 'LIVE'),
    dict(id='GL', name='% ' + 'G/L'),
]

tabla_ejecuciones = [
    dict(id='TRADE_DATE', name='TRADE DATE'),
    dict(id='SYMBOL', name='SYMBOL'),
    dict(id='SIDE', name='SIDE'),
    dict(id='ENTRY', name='PRICE'),
    dict(id='STOP_LOSS', name='STOP LOSS'),
    dict(id='TARGET_PRICE', name='TARGET PRICE'),
    dict(id='PROFIT', name='% ' + 'G/L'),
    dict(id='PORCENTAJE_EJECUTADO', name='% ' + 'EXECUTE'),
]


header = dbc.Row(
    [
        html.Img(src='/static/img/logo_light.png', className="logo")
    ]
)

bitacora = dbc.Row(
    [
        DataTable(
            id='bit_data',
            columns=tabla_bitacora,
            # Aquí configura tus datos para la tabla bitacora
            data=[],
            style_header={
                'color': 'white',
                'textAlign': 'center',
                'fontWeight': 'bold',
                'border': 'none',  # Elimina los bordes del encabezado
                'background-color': 'Black',  # Color de fondo del encabezado
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
                        'filter_query': '{SIDE} = BUY  || {SIDE} = Buy',
                        'column_id': 'SIDE'
                    },
                    'backgroundColor': 'green',
                    'color': 'white'
                },
                {
                    'if': {
                        'filter_query': '{SIDE} = "SELL"  || {SIDE} = "Sell"',
                        'column_id': 'SIDE'
                    },
                    'backgroundColor': 'tomato',
                    'color': 'white'
                },
                {
                    'if': {
                        'filter_query': '{GL} < 0',
                        'column_id': 'GL'
                    },
                    'backgroundColor': 'tomato',
                    'color': 'white'
                },
                {
                    'if': {
                        'filter_query': '{GL} > 0',
                        'column_id': 'GL'
                    },
                    'backgroundColor': 'green',
                    'color': 'white'
                },
                {
                    'if': {
                        'state': 'active'  # 'active' | 'selected'
                    },
                    'backgroundColor': '#FDC500 ',
                    'border': 'none'
                }
            ],
        )
    ], className='tabla', id="bitacora_tactical"
)

ejecuciones = dbc.Row(
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
                        'state': 'active'  # 'active' | 'selected'
                    },
                    'backgroundColor': '#FDC500',
                    'border': 'none'
                },
                {
                    'if': {
                        'filter_query': '{SIDE} = BUY  || {SIDE} = Buy',
                        'column_id': 'SIDE'
                    },
                    'backgroundColor': 'green',
                    'color': 'white'
                },
                {
                    'if': {
                        'filter_query': '{SIDE} = "SELL"  || {SIDE} = "Sell"',
                        'column_id': 'SIDE'
                    },
                    'backgroundColor': 'tomato',
                    'color': 'white'
                },
            ]
        ),
    ], className='tabla_ejecucion', id='ejecuciones_tactical'
)

app.layout = html.Div(
    children=[
        header,
        bitacora,
        ejecuciones,
        dcc.Location(id='url', refresh=False),
    ],
)

# callback tabla bitacora, datos sin ejecución


@app.callback(
    Output(component_id='bit_data', component_property='data'),
    Input(component_id='url', component_property='href'),
    prevent_initial_call=True
)
def inicio_tabla(valor):
    df = cache.get('bit')
    if df is None or not df:
        raise PreventUpdate

    # Obtener los símbolos únicos de la bitácora
    symbols = set(row['SYMBOL'] for row in df)

    # Actualizar precios para cada símbolo
    for symbol in symbols:
        # Obtener precios del último día
        data_yf = yf.download(symbol, period='1d')
        ultimo_precio = round(data_yf['Close'].iloc[-1], 2)

        # Actualizar la columna 'PRICE' en la data
        for row in df:
            if row['SYMBOL'] == symbol:
                row['PRICE'] = ultimo_precio

                # Convertir la columna 'ENTRY' a tipo numérico
                row['ENTRY'] = pd.to_numeric(row['ENTRY'], errors='coerce')
                # Calcular G/L y redondear a dos decimales
                if row['SIDE'] == "Buy":
                    # se calcula cualdo es buy
                    row['GL'] = round(
                        (row['PRICE'] - row['ENTRY']) / row['ENTRY'] * 100, 2)
                else:
                    # se calcula cuando es sell
                    row['GL'] = round(
                        (row['ENTRY'] - row['PRICE']) / row['ENTRY'] * 100, 2)

    return df


# callback tabla de ejecucion
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

    dfh = cache.get('his')
    dfh = pd.DataFrame(dfh)
    df = cache.get('bit')
    df = pd.DataFrame(df)

    if dfh is None or df is None:
        # Manejar el caso en el que los datos no se encuentran en la caché
        raise PreventUpdate  # O manejo personalizado de acuerdo a tus necesidades

    # Obtener el SYMBOL seleccionado
    selected_uuid = data[active_cell['row']]['UUID']

    # Filtra los registros de Historial_Bitacora por el UUID seleccionado
    filtered_data = dfh[dfh['UUID'] == selected_uuid]

    # Cambia el estilo de la tabla de ejecuciones
    ejecuciones_style = {'display': 'block'} if not filtered_data.empty else {
        'display': 'none'}

    return filtered_data.to_dict('records'), ejecuciones_style


if __name__ == '__main__':
    app.run_server()
