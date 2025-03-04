import psycopg2
from backend.config import DATABASE_CONFIG

try:
    # Conecta ao banco de dados
    conn = psycopg2.connect(**DATABASE_CONFIG)
    print("Conexão com o banco de dados estabelecida com sucesso!")
except Exception as e:
    print(f"Erro ao conectar ao banco de dados: {e}")
finally:
    if conn:
        conn.close()