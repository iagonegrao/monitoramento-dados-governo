import os
import geopandas as gpd
from sqlalchemy import create_engine, text

# Configurações do banco de dados
DATABASE_URL = "postgresql+psycopg2://postgres:191010@localhost/dados_governo"

# Cria uma conexão com o banco de dados usando SQLAlchemy
engine = create_engine(DATABASE_URL)

def criar_schema(conn, nome_schema):
    """
    Cria um schema no PostgreSQL se ele não existir.
    """
    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {nome_schema};"))
    conn.commit()
    print(f"Schema '{nome_schema}' criado ou verificado com sucesso.")

def carregar_shapefile_para_postgres(caminho_shapefile, nome_tabela, nome_orgao):
    """
    Carrega um shapefile no PostgreSQL dentro de um schema específico.
    """
    # Verifica se o arquivo shapefile existe
    if not os.path.exists(caminho_shapefile):
        raise FileNotFoundError(f"Arquivo shapefile não encontrado: {caminho_shapefile}")

    # Ler o shapefile com GeoPandas
    gdf = gpd.read_file(caminho_shapefile)

    # Nome do schema (usando o nome do órgão responsável)
    nome_schema = nome_orgao.lower().replace(" ", "_")  # Formata o nome para ser compatível com SQL

    # Conectar ao banco de dados e criar o schema (se necessário)
    with engine.connect() as conn:
        criar_schema(conn, nome_schema)

        # Carregar os dados no PostgreSQL dentro do schema
        gdf.to_postgis(
            nome_tabela,
            engine,
            schema=nome_schema,  # Especifica o schema
            if_exists='append',
            index=False
        )

        # Definir um nome de índice manualmente (limitado a 63 caracteres)
        nome_indice = f"idx_{nome_tabela}_geom"  # Nome curto para o índice

        # Criar um índice espacial manualmente
        conn.execute(text(f"CREATE INDEX {nome_indice} ON {nome_schema}.{nome_tabela} USING GIST (geometry);"))
        conn.commit()  # Confirma a transação

    print(f"Dados do shapefile '{caminho_shapefile}' carregados na tabela '{nome_schema}.{nome_tabela}' com sucesso!")
    print(f"Índice espacial '{nome_indice}' criado manualmente.")

# Exemplo de uso
if __name__ == "__main__":
    # Caminho para o shapefile (usando raw string para evitar problemas com barras invertidas)
    caminho_shapefile = r"C:\Arquivos_monitorados\focos_incendio\download_eventos_painel_do_fogo.csv"

    # Nome da tabela no PostgreSQL
    nome_tabela = "br_sipam_mapa_fogo"  # Nome curto para evitar problemas

    # Nome do órgão responsável (será usado como nome do schema)
    nome_orgao = "sipam"  # Exemplo de nome de órgão

    # Carregar o shapefile no PostgreSQL
    carregar_shapefile_para_postgres(caminho_shapefile, nome_tabela, nome_orgao)