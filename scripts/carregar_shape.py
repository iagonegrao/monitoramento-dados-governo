import geopandas as gpd
from sqlalchemy import create_engine, inspect
import sys
import os
from config import DATABASE_CONFIG

def carregar_shapefile_para_postgres(caminho_shapefile, nome_tabela):
    # Ler o arquivo SHP usando geopandas
    gdf = gpd.read_file(caminho_shapefile)

    # Criar a string de conexão com o banco de dados
    conexao_str = f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['dbname']}"

    # Criar a engine de conexão com o banco de dados
    engine = create_engine(conexao_str)

    # Verificar se a tabela já existe
    inspector = inspect(engine)
    if nome_tabela in inspector.get_table_names():
        print(f"A tabela {nome_tabela} já existe. Realizando TRUNCATE...")
        with engine.connect() as conn:
            conn.execute(f"TRUNCATE TABLE {nome_tabela};")
            conn.commit()

    # Carregar os dados no banco de dados
    gdf.to_postgis(nome_tabela, engine, if_exists='append', index=False)

    print(f"Dados carregados com sucesso na tabela {nome_tabela}!")

# Caminho para o arquivo SHP
caminho_shapefile = r'C:\Users\iagoc\Downloads\dashboard_alerts-shapefile\dashboard_alerts-shapefile.shp'

# Nome da tabela que será criada no PostgreSQL
nome_tabela = 'br_mapbiomas_alert'

# Chamar a função para carregar os dados
carregar_shapefile_para_postgres(caminho_shapefile, nome_tabela)