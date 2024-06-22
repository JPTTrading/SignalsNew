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
            # inline=True,
        ),
    ],
    className='switch-container'
)

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
    dict(id='TRADE_DATE', name='TRADE DATE', sort_by='asceding'),
    dict(id='SYMBOL', name='SYMBOL'),
    dict(id='SIDE', name='SIDE'),
    dict(id='ENTRY', name='PRICE'),
    dict(id='STOP_LOSS', name='STOP LOSS'),
    dict(id='TARGET_PRICE', name='TARGET PRICE'),
    dict(id='PROFIT', name='% ' + 'G/L'),
    dict(id='PORCENTAJE_EJECUTADO', name='% ' + 'EXECUTE'),
]

header = dbc.Row(
    [html.Img(src='/static/img/logo_light.png', className="logo")])

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
                            'column_id': 'PROFIT'
                        },
                        'backgroundColor': 'tomato',
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{GL} > 0',
                            'column_id': 'PROFIT'
                        },
                        'backgroundColor': 'green',
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
        bitacora,
        ejecuciones,
        dcc.Location(id='url', refresh=False),
    ],
)


@app.callback(
    [
        Output(component_id='bit_data', component_property='data'),
        Output(component_id='bit_data', component_property='columns'),
    ],
    Input(component_id='url', component_property='href'),
    Input(component_id='switch-input', component_property='value'),
    prevent_initial_call=True
)
def inicio_tabla(valor, switch_value):
    df = cache.get('bit')
    if df is None or not df:
        raise PreventUpdate

    # Filtrar datos según el valor del switch
    if switch_value == 'open':
        df = [row for row in df if not row['TRADE_CLOSE']]
        tabla_bitacora = [
            dict(id='TRADE_DATE', name='TRADE DATE'),
            dict(id='SYMBOL', name='SYMBOL'),
            dict(id='PRICE', name='PRICE'),
            dict(id='SIDE', name='SIDE'),
            dict(id='ENTRY', name='ENTRY'),
            dict(id='STOP_LOSS', name='STOP LOSS'),
            dict(id='TARGET_PRICE', name='TARGET PRICE'),
            dict(id='PORCENTAJE_ACUMULADO', name='% ' + 'LIVE'),
            dict(id='GL', name='% ' + 'G/L'),
        ]
    else:
        df = [row for row in df if row['TRADE_CLOSE']]
        tabla_bitacora = [
            dict(id='TRADE_DATE', name='TRADE DATE'),
            dict(id='TRADE_CLOSE', name='TRADE CLOSE'),
            dict(id='SYMBOL', name='SYMBOL'),
            dict(id='SIDE', name='SIDE'),
            dict(id='ENTRY', name='ENTRY'),
            dict(id='STOP_LOSS', name='STOP LOSS'),
            dict(id='TARGET_PRICE', name='TARGET PRICE'),
            dict(id='PORCENTAJE_ACUMULADO', name='% ' + 'LIVE'),
        ]

    # Obtener los símbolos únicos de la bitácora
    symbols = set(row['SYMBOL'] for row in df)

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

        for row in df:
            if row['SYMBOL'] == symbol:
                row['PRICE'] = ultimo_precio
                row['ENTRY'] = pd.to_numeric(row['ENTRY'], errors='coerce')
                if row['SIDE'] == "Buy":
                    row['GL'] = round(
                        (row['PRICE'] - row['ENTRY']) / row['ENTRY'] * 100, 2)
                else:
                    row['GL'] = round(
                        (row['ENTRY'] - row['PRICE']) / row['ENTRY'] * 100, 2)

    return df, tabla_bitacora


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
        raise PreventUpdate

    selected_uuid = data[active_cell['row']]['UUID']
    filtered_data = dfh[dfh['UUID'] == selected_uuid]
    ejecuciones_style = {'display': 'block'} if not filtered_data.empty else {
        'display': 'none'}

    return filtered_data.to_dict('records'), ejecuciones_style


def actualizar_gl():
    df_bitacora = cache.get('bit')
    if df_bitacora is None or not df_bitacora:
        raise PreventUpdate

    # Filtrar solo las posiciones cerradas
    df_bitacora_closed = [row for row in df_bitacora if row['TRADE_CLOSE']]

    for row in df_bitacora_closed:
        # Obtener el UUID de la posición cerrada
        uuid_closed = row['UUID']

        # Filtrar las ejecuciones asociadas a la posición cerrada
        df_ejecuciones = cache.get('his')
        if df_ejecuciones is None or not df_ejecuciones:
            continue

        df_ejecuciones = pd.DataFrame(df_ejecuciones)
        df_ejecuciones_filtered = df_ejecuciones[df_ejecuciones['UUID'] == uuid_closed]

        if not df_ejecuciones_filtered.empty and 'PROFIT' in df_ejecuciones_filtered:
            # Obtener el último valor de la columna 'PROFIT' de las ejecuciones
            last_profit = df_ejecuciones_filtered.iloc[-1]['PROFIT']

            # Actualizar el valor de 'GL' en la bitácora con el último valor de 'PROFIT'
            row['GL'] = last_profit

    # Actualizar la cache
    cache.set('bit', df_bitacora)


if __name__ == '__main__':
    app.run_server()
