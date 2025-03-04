import os
import time
import psycopg2
from datetime import datetime

# Configurações
PASTA_MONITORADA = 'E:\\OneDrive\\Documentos\\Arquivos_monitorados'
DATABASE_CONFIG = {
    'dbname': 'monitoramento_dados',
    'user': 'postgres',
    'password': '191010',
    'host': 'localhost'
}

def conectar_banco():
    return psycopg2.connect(**DATABASE_CONFIG)

def carregar_csv(arquivo):
    # Implementar a lógica de carga de CSV
    pass

def carregar_shp(arquivo):
    # Implementar a lógica de carga de SHP
    pass

def monitorar_pasta():
    arquivos_conhecidos = set(os.listdir(PASTA_MONITORADA))
    while True:
        time.sleep(10)
        arquivos_atual = set(os.listdir(PASTA_MONITORADA))
        novos_arquivos = arquivos_atual - arquivos_conhecidos
        for arquivo in novos_arquivos:
            if arquivo.endswith('.csv'):
                carregar_csv(arquivo)
            elif arquivo.endswith('.shp'):
                carregar_shp(arquivo)
            arquivos_conhecidos.add(arquivo)

if __name__ == "__main__":
    monitorar_pasta()