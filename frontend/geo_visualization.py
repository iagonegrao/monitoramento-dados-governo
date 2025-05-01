import geopandas as gpd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import folium
import psycopg2
from psycopg2 import sql
import json
import logging
from shapely.geometry import shape

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Cria conexão com o banco de dados"""
    try:
        return psycopg2.connect(
            dbname='dados_governo',
            user='postgres',
            password='191010',
            host='localhost',
            connect_timeout=3
        )
    except Exception as e:
        logger.error(f"Erro na conexão com o banco: {e}")
        return None

def generate_intersection_plot(cod_imovel, schema, tabela, coluna_geom):
    """Gera plot estático com CAR e intersecções"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return None

        # Consulta otimizada para todas as geometrias
        query = sql.SQL("""
        WITH car_geom AS (
            SELECT ST_Transform(ST_SetSRID(geom, 4326), 4326) as geom 
            FROM sicar 
            WHERE cod_imovel = %s
        ),
        intersected_data AS (
            SELECT ST_Transform({}, 4326) as geom
            FROM {}.{} 
            WHERE ST_Intersects(
                ST_Transform({}, 4326),
                (SELECT geom FROM car_geom)
            )
        )
        SELECT 
            (SELECT geom FROM car_geom) as car_geom,
            (SELECT array_agg(geom) FROM intersected_data) as data_geoms,
            (SELECT ST_Union(geom) FROM intersected_data) as union_geom,
            (SELECT ST_Intersection(
                (SELECT geom FROM car_geom),
                (SELECT ST_Union(geom) FROM intersected_data)
            )) as intersection_geom
        """).format(
            sql.Identifier(coluna_geom),
            sql.Identifier(schema),
            sql.Identifier(tabela),
            sql.Identifier(coluna_geom)
        )

        with conn.cursor() as cur:
            cur.execute(query, (cod_imovel,))
            result = cur.fetchone()

            if not result or not result[0]:
                logger.warning("CAR não encontrado ou sem geometria")
                return None

            # Preparar figura
            fig, ax = plt.subplots(figsize=(12, 10))
            
            # Plotar CAR
            gdf_car = gpd.GeoDataFrame([{'geometry': result[0]}], crs="EPSG:4326")
            gdf_car.plot(ax=ax, color='blue', alpha=0.3, edgecolor='navy', linewidth=2, label='CAR')

            # Plotar geometrias dos dados (individualmente)
            if result[1]:
                for geom in result[1]:
                    if geom:  # Verifica se a geometria não é None
                        gpd.GeoDataFrame([{'geometry': geom}], crs="EPSG:4326").plot(
                            ax=ax, color='green', alpha=0.2, edgecolor='darkgreen')

            # Plotar união das geometrias
            if result[2]:
                gpd.GeoDataFrame([{'geometry': result[2]}], crs="EPSG:4326").plot(
                    ax=ax, color='green', alpha=0.4, edgecolor='darkgreen', linewidth=1, label=f'{tabela} (Área Total)')

            # Plotar intersecção
            if result[3]:
                gpd.GeoDataFrame([{'geometry': result[3]}], crs="EPSG:4326").plot(
                    ax=ax, color='red', alpha=0.7, edgecolor='darkred', linewidth=2, label='Área de Intersecção')

            # Configurações do gráfico
            ax.set_title(f'CAR {cod_imovel} × {tabela}', pad=20, fontsize=14)
            ax.legend(loc='upper right')
            ax.set_axis_off()
            plt.tight_layout()

            # Converter para base64
            img = BytesIO()
            plt.savefig(img, format='png', bbox_inches='tight', dpi=120)
            plt.close()
            return base64.b64encode(img.getvalue()).decode('utf-8')

    except Exception as e:
        logger.error(f"Erro ao gerar plot: {e}", exc_info=True)
        return None
    finally:
        if conn:
            conn.close()

def generate_interactive_map(cod_imovel, schema, tabela, coluna_geom):
    """Gera mapa interativo com todas as geometrias"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return None

        # Consulta completa para o mapa
        query = sql.SQL("""
        WITH car_geom AS (
            SELECT 
                ST_Transform(ST_SetSRID(geom, 4326), 4326) as geom,
                ST_Centroid(ST_Transform(ST_SetSRID(geom, 4326), 4326)) as centroid
            FROM sicar 
            WHERE cod_imovel = %s
        ),
        intersected_data AS (
            SELECT 
                ST_Transform({}, 4326) as geom,
                id  -- assumindo que existe uma coluna id
            FROM {}.{} 
            WHERE ST_Intersects(
                ST_Transform({}, 4326),
                (SELECT geom FROM car_geom)
            )
        )
        SELECT 
            ST_AsGeoJSON((SELECT geom FROM car_geom)) as car_geojson,
            (SELECT json_agg(ST_AsGeoJSON(id.*)) FROM intersected_data id) as data_geojsons,
            ST_AsGeoJSON(ST_Union((SELECT array_agg(geom) FROM intersected_data))) as union_geojson,
            ST_AsGeoJSON(ST_Intersection(
                (SELECT geom FROM car_geom),
                ST_Union((SELECT array_agg(geom) FROM intersected_data))
            )) as intersect_geojson,
            ST_Y((SELECT centroid FROM car_geom)) as lat,
            ST_X((SELECT centroid FROM car_geom)) as lng
        """).format(
            sql.Identifier(coluna_geom),
            sql.Identifier(schema),
            sql.Identifier(tabela),
            sql.Identifier(coluna_geom)
        )

        with conn.cursor() as cur:
            cur.execute(query, (cod_imovel,))
            result = cur.fetchone()

            if not result or not result[0]:
                logger.warning("Nenhum dado encontrado para visualização")
                return None

            # Criar mapa base
            m = folium.Map(
                location=[result[4], result[5]], 
                zoom_start=12,
                tiles='CartoDB positron',
                control_scale=True
            )

            # Adicionar CAR
            folium.GeoJson(
                json.loads(result[0]),
                name='CAR',
                style_function=lambda x: {
                    'fillColor': '#3186cc',
                    'color': '#3186cc',
                    'weight': 2,
                    'fillOpacity': 0.3
                },
                tooltip=folium.GeoJsonTooltip(fields=[], aliases=['CAR'])
            ).add_to(m)

            # Adicionar geometrias individuais dos dados
            if result[1]:
                for feature in json.loads(result[1]):
                    folium.GeoJson(
                        feature,
                        name=f'{tabela} (individual)',
                        style_function=lambda x: {
                            'fillColor': '#2ca02c',
                            'color': '#2ca02c',
                            'weight': 1,
                            'fillOpacity': 0.2
                        },
                        tooltip=folium.GeoJsonTooltip(
                            fields=['id'],
                            aliases=['ID:']
                        )
                    ).add_to(m)

            # Adicionar união das geometrias
            if result[2]:
                folium.GeoJson(
                    json.loads(result[2]),
                    name=f'{tabela} (Área Total)',
                    style_function=lambda x: {
                        'fillColor': '#2ca02c',
                        'color': '#2ca02c',
                        'weight': 1.5,
                        'fillOpacity': 0.4
                    }
                ).add_to(m)

            # Adicionar intersecção
            if result[3]:
                folium.GeoJson(
                    json.loads(result[3]),
                    name='Área de Intersecção',
                    style_function=lambda x: {
                        'fillColor': '#d62728',
                        'color': '#d62728',
                        'weight': 2,
                        'fillOpacity': 0.7
                    },
                    tooltip=folium.GeoJsonTooltip(fields=[], aliases=['Intersecção'])
                ).add_to(m)

            # Controles do mapa
            folium.LayerControl(
                position='topright',
                collapsed=False
            ).add_to(m)

            return m._repr_html_()

    except Exception as e:
        logger.error(f"Erro ao gerar mapa: {e}", exc_info=True)
        return None
    finally:
        if conn:
            conn.close()