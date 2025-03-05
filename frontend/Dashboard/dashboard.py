import pandas as pd
from sqlalchemy import create_engine
import dash
from dash import dcc, html, callback, Input, Output
import plotly.express as px
import warnings
from flask import Flask, render_template

# Suprimir avisos (opcional)
warnings.filterwarnings("ignore", category=UserWarning)

# Configuração do banco de dados
DATABASE_URL = "postgresql+psycopg2://postgres:191010@localhost/dados_governo"
engine = create_engine(DATABASE_URL)

# Criando servidor Flask
server = Flask(__name__)

# Inicializar Dash sem `routes_pathname_prefix`
app = dash.Dash(__name__, server=server)

# Listagem de tabelas disponíveis e suas respectivas queries
TABELAS_QUERIES = {
    'Amazonia legal Prodes 2024 - Cenas prioritárias': """
        SELECT DISTINCT state as uf, COUNT(*) as contagem 
        FROM terrabrasilis_inpe.br_inpe_prodes_2024 
        GROUP BY state
    """,
    'Alerta Mapbiomas': """
        SELECT DISTINCT "ESTADO" as uf, COUNT(*) as contagem
        FROM mapbiomas.br_mapbiomas_alert 
        GROUP BY "ESTADO"
    """
}

def carregar_dados(tabela):
    """Carrega dados baseado na tabela selecionada"""
    with engine.connect() as connection:
        query = TABELAS_QUERIES.get(tabela, "")
        if query:
            df = pd.read_sql_query(query, connection)
            return df
        return pd.DataFrame()

# Layout do dashboard
app.layout = html.Div(children=[
    html.H1(children='Dashboard de Dados Governamentais', style={'textAlign': 'center'}),

    # Dropdown para seleção de tabela
    dcc.Dropdown(
        id='tabela-dropdown',
        options=[{'label': nome, 'value': nome} for nome in TABELAS_QUERIES.keys()],
        value=list(TABELAS_QUERIES.keys())[0],
        placeholder='Selecione um conjunto de dados'
    ),

    # Dropdown para seleção de estados
    dcc.Dropdown(
        id='estado-dropdown',
        multi=True,
        placeholder='Selecione um ou mais estados'
    ),

    # Indicador numérico
    html.Div(id='indicador-total', style={'fontSize': '24px', 'textAlign': 'center', 'margin': '20px'}),

    # Gráfico de barras
    dcc.Graph(id='bar-chart'),

    # Gráfico de pizza
    dcc.Graph(id='pie-chart')
])

# Callback para atualizar dropdown de estados e gráficos
@callback(
    [Output('estado-dropdown', 'options'), Output('bar-chart', 'figure'), Output('pie-chart', 'figure'), Output('indicador-total', 'children')],
    [Input('tabela-dropdown', 'value'), Input('estado-dropdown', 'value')]
)
def update_dashboard(tabela_selecionada, estados_selecionados):
    df = carregar_dados(tabela_selecionada)

    if df.empty or 'uf' not in df.columns:
        return [], px.bar(title='Nenhum dado disponível'), px.pie(title='Nenhum dado disponível'), 'Nenhum dado disponível'

    estado_options = [{'label': str(estado), 'value': str(estado)} for estado in df['uf'].dropna().unique()]
    df_filtrado = df if not estados_selecionados else df[df['uf'].isin(estados_selecionados)]

    # Gráfico de barras
    bar_fig = px.bar(
        df_filtrado, x='uf', y='contagem',
        title='Quantidade por estado',
        labels={'uf': 'Estado', 'contagem': 'Quantidade'},
        color='contagem', color_continuous_scale='viridis'
    )

    # Gráfico de pizza
    pie_fig = px.pie(
        df_filtrado, values='contagem', names='uf',
        title='Proporção por estado'
    )

    # Indicador total
    total_registros = df_filtrado['contagem'].sum()
    indicador_texto = f'Total: {total_registros:,}'.replace(',', '.')

    return estado_options, bar_fig, pie_fig, indicador_texto

# Criar uma rota do Flask para redirecionar para o Dash
@server.route('/')
def index():
    return render_template('index.html')

# Executar o servidor Flask com Dash na porta 8050 e aceitar conexões externas
if __name__ == '__main__':
    server.run(debug=True, host='0.0.0.0', port=8050)
