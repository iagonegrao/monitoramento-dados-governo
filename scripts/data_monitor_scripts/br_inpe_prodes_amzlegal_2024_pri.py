import os
import geopandas as gpd
from sqlalchemy import create_engine, text

# Configurações do banco de dados
DATABASE_URL = "postgresql+psycopg2://postgres:191010@localhost/dados_governo"

# Cria uma conexão com o banco de dados usando SQLAlchemy
engine = create_engine(DATABASE_URL)

def carregar_shapefile_para_postgres(caminho_shapefile, nome_tabela):
    """
    Carrega um shapefile no PostgreSQL usando GeoPandas e SQLAlchemy.
    Define manualmente o nome do índice para evitar problemas com limites de caracteres.
    """
    # Verifica se o arquivo shapefile existe
    if not os.path.exists(caminho_shapefile):
        raise FileNotFoundError(f"Arquivo shapefile não encontrado: {caminho_shapefile}")

    # Ler o shapefile com GeoPandas
    gdf = gpd.read_file(caminho_shapefile)

    # Definir um nome de índice manualmente (limitado a 63 caracteres)
    nome_indice = f"idx_{nome_tabela}_geom"  # Nome curto para o índice

    # Carregar os dados no PostgreSQL
    gdf.to_postgis(nome_tabela, engine, if_exists='append', index=False)

    # Criar um índice espacial manualmente
    with engine.connect() as conn:
        conn.execute(text(f"CREATE INDEX {nome_indice} ON {nome_tabela} USING GIST (geometry);"))
        conn.commit()  # Confirma a transação

    print(f"Dados do shapefile '{caminho_shapefile}' carregados na tabela '{nome_tabela}' com sucesso!")
    print(f"Índice espacial '{nome_indice}' criado manualmente.")

# Exemplo de uso
if __name__ == "__main__":
    # Caminho para o shapefile (usando raw string para evitar problemas com barras invertidas)
    caminho_shapefile = r"C:\Arquivos_monitorados\prodes_amazonia_legal_2024_cenas_prioritarias\yearly_deforestation_2024_pri.shp"

    # Nome da tabela no PostgreSQL
    nome_tabela = "br_inpe_prodes_2024"  # Nome curto para evitar problemas

    # Carregar o shapefile no PostgreSQL
    carregar_shapefile_para_postgres(caminho_shapefile, nome_tabela)