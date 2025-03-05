import os
import pandas as pd
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

def carregar_csv_para_postgres(caminho_csv, nome_tabela, nome_orgao):
    """
    Carrega um arquivo CSV no PostgreSQL dentro de um schema específico.
    Converte a coluna 'geom' de texto para o tipo 'geometry' (se existir).
    """
    # Verifica se o arquivo CSV existe
    if not os.path.exists(caminho_csv):
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {caminho_csv}")

    # Ler o arquivo CSV com Pandas
    df = pd.read_csv(caminho_csv)

    # Nome do schema (usando o nome do órgão responsável)
    nome_schema = nome_orgao.lower().replace(" ", "_")  # Formata o nome para ser compatível com SQL

    # Conectar ao banco de dados e criar o schema (se necessário)
    with engine.connect() as conn:
        criar_schema(conn, nome_schema)

        # Carregar os dados no PostgreSQL dentro do schema
        df.to_sql(
            nome_tabela,
            engine,
            schema=nome_schema,  # Especifica o schema
            if_exists='append',
            index=False
        )

        # Verifica se a coluna 'geom' existe no DataFrame
        if 'geom' in df.columns:
            # Converte a coluna 'geom' de texto para o tipo 'geometry'
            conn.execute(text(f"""
                ALTER TABLE {nome_schema}.{nome_tabela}
                ALTER COLUMN geom TYPE geometry USING ST_SetSRID(ST_GeomFromText(geom), 4326);
            """))
            conn.commit()
            print(f"Coluna 'geom' convertida para o tipo 'geometry' na tabela '{nome_schema}.{nome_tabela}'.")

    print(f"Dados do CSV '{caminho_csv}' carregados na tabela '{nome_schema}.{nome_tabela}' com sucesso!")

# Exemplo de uso
if __name__ == "__main__":
    # Caminho para o arquivo CSV (usando raw string para evitar problemas com barras invertidas)
    caminho_csv = r"C:\Arquivos_monitorados\focos_incendio\download_eventos_painel_do_fogo.csv"

    # Nome da tabela no PostgreSQL
    nome_tabela = "br_sipam_mapa_fogo"  # Nome da tabela

    # Nome do órgão responsável (será usado como nome do schema)
    nome_orgao = "sipam"  # Exemplo de nome de órgão

    # Carregar o CSV no PostgreSQL
    carregar_csv_para_postgres(caminho_csv, nome_tabela, nome_orgao)