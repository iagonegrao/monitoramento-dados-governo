import pandas as pd
from sqlalchemy import create_engine
import dash
from dash import dcc, html
import warnings

# Suprimir avisos (opcional)
warnings.filterwarnings("ignore", category=UserWarning)

# Configurações do banco de dados
DATABASE_URL = "postgresql+psycopg2://postgres:191010@localhost/dados_governo"

# Cria uma conexão com o banco de dados usando SQLAlchemy
engine = create_engine(DATABASE_URL)

# Usa um context manager para garantir que a conexão seja fechada corretamente
with engine.connect() as connection:
    # Lê os dados da tabela data_monitoring
    df = pd.read_sql_query("SELECT * FROM br_mapbiomas_alert", connection)

# Inicializa o aplicativo Dash
app = dash.Dash(__name__)

# Layout do dashboard
app.layout = html.Div(children=[
    html.H1(children='Dashboard de Dados Governamentais'),

    dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': df['DTPUBLI'], 'y': df['DTPUBLI'], 'type': 'bar', 'name': 'Atualizações'},
            ],
            'layout': {
                'title': 'Histórico de Atualizações'
            }
        }
    )
])

# Executa o servidor do dashboard
if __name__ == '__main__':
    app.run_server(debug=True)