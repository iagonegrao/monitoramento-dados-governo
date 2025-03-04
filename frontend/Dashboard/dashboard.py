import dash
from dash import dcc, html
import psycopg2
import pandas as pd

DATABASE_CONFIG = {
    'dbname': 'monitoramento_dados',
    'user': 'postgres',
    'password': '191010',
    'host': 'localhost'
}

app = dash.Dash(__name__)

conn = psycopg2.connect(**DATABASE_CONFIG)
df = pd.read_sql_query("SELECT * FROM data_monitoring", conn)
conn.close()

app.layout = html.Div(children=[
    html.H1(children='Dashboard de Dados Governamentais'),

    dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': df['created_date'], 'y': df['update_date'], 'type': 'bar', 'name': 'Atualizações'},
            ],
            'layout': {
                'title': 'Histórico de Atualizações'
            }
        }
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)