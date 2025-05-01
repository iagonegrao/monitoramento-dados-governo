from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from psycopg2 import sql
from werkzeug.utils import secure_filename
import os
from sqlalchemy import create_engine

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/logos'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DATABASE_CONFIG = {
    'dbname': 'dados_governo',
    'user': 'postgres',
    'password': '191010',
    'host': 'localhost'
}

DATABASE_URL = "postgresql+psycopg2://postgres:191010@localhost/dados_governo"
engine = create_engine(DATABASE_URL)

def conectar_banco():
    return psycopg2.connect(**DATABASE_CONFIG)

def consultar_intersecao(cur, cod_imovel, schema, tabela, coluna_geom):
    query = f"""
        SELECT 
            ST_Area(ST_Intersection(ST_Transform(ST_SetSRID(s.geom, 4326), 4326), 
                                    ST_Transform(d.{coluna_geom}, 4326))::geography) / 10000 AS area_ha,
            (ST_Area(ST_Intersection(ST_Transform(ST_SetSRID(s.geom, 4326), 4326), 
                                     ST_Transform(d.{coluna_geom}, 4326))::geography) / 
             ST_Area(ST_Transform(ST_SetSRID(s.geom, 4326), 4326)::geography)) * 100.0 AS percentual
        FROM sicar s, {schema}.{tabela} d
        WHERE s.cod_imovel = %s 
          AND ST_Intersects(ST_Transform(ST_SetSRID(s.geom, 4326), 4326), 
                            ST_Transform(d.{coluna_geom}, 4326))
    """
    cur.execute(query, (cod_imovel,))
    return cur.fetchone()

@app.route('/')
def index():
    try:
        with conectar_banco() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nome_orgao, site_oficial, logo FROM agency;")
                orgaos = cur.fetchall()
                cur.execute("SELECT id, nome_dado, site_oficial FROM data_monitoring;")
                dados = cur.fetchall()
    except Exception as e:
        orgaos, dados = [], []
        print(f"Erro ao carregar dados: {e}")

    return render_template('index.html', orgaos=orgaos, dados=dados)
@app.route('/mapa')
def modulo_mapa():
    return render_template('mapa.html')
@app.route('/cadastrar_orgao', methods=['GET', 'POST'])
def cadastrar_orgao():
    mensagem = None
    if request.method == 'POST':
        nome_orgao = request.form.get('nome_orgao')
        site_oficial = request.form.get('site_oficial')
        logo = request.files.get('logo')
        if not nome_orgao or not site_oficial:
            mensagem = "Erro: Todos os campos são obrigatórios!"
        else:
            logo_filename = None
            if logo and logo.filename:
                logo_filename = secure_filename(logo.filename)
                logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
                logo.save(logo_path)
                logo_filename = f"/{logo_path}"
            try:
                with conectar_banco() as conn:
                    with conn.cursor() as cur:
                        if logo_filename is None:
                            logo_filename = ''
                        cur.execute("INSERT INTO agency (nome_orgao, site_oficial, logo) VALUES (%s, %s, %s);",
                                    (nome_orgao, site_oficial, logo_filename))
                        mensagem = "Órgão cadastrado com sucesso!"
            except Exception as e:
                mensagem = f"Erro ao cadastrar órgão: {e}"
    return render_template('cadastrar_orgao.html', mensagem=mensagem)

@app.route('/editar_orgao/<int:orgao_id>', methods=['GET', 'POST'])
def editar_orgao(orgao_id):
    mensagem = None
    orgao = None
    try:
        with conectar_banco() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nome_orgao, site_oficial, logo FROM agency WHERE id = %s;", (orgao_id,))
                orgao = cur.fetchone()
        if request.method == 'POST':
            nome_orgao = request.form.get('nome_orgao')
            site_oficial = request.form.get('site_oficial')
            logo = request.files.get('logo')
            if not nome_orgao or not site_oficial:
                mensagem = "Erro: Todos os campos são obrigatórios!"
            else:
                logo_filename = orgao[3]
                if logo and logo.filename:
                    logo_filename = secure_filename(logo.filename)
                    logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
                    logo.save(logo_path)
                    logo_filename = f"/{logo_path}"
                with conectar_banco() as conn:
                    with conn.cursor() as cur:
                        cur.execute("UPDATE agency SET nome_orgao = %s, site_oficial = %s, logo = %s WHERE id = %s;",
                                    (nome_orgao, site_oficial, logo_filename, orgao_id))
                        mensagem = "Órgão atualizado com sucesso!"
                return redirect(url_for('index'))
    except Exception as e:
        mensagem = f"Erro ao carregar órgão: {e}"
    return render_template('editar_orgao.html', orgao=orgao, mensagem=mensagem)

@app.route('/cadastrar_dado', methods=['GET', 'POST'])
def cadastrar_dado():
    mensagem = None
    try:
        with conectar_banco() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nome_orgao FROM agency;")
                orgaos = cur.fetchall()
    except Exception as e:
        mensagem = f"Erro ao carregar órgãos: {e}"
        orgaos = []

    if request.method == 'POST':
        fk_id_agency = request.form.get('fk_id_agency')
        nome_dado = request.form.get('nome_dado')
        site_oficial = request.form.get('site_oficial')
        if not fk_id_agency or not nome_dado or not site_oficial:
            mensagem = "Erro: Todos os campos são obrigatórios!"
        else:
            try:
                with conectar_banco() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO data_monitoring (fk_id_agency, nome_dado, site_oficial, script, update_date) VALUES (%s, %s, %s, %s, NOW());",
                            (fk_id_agency, nome_dado, site_oficial, '0')
                        )
                        mensagem = "Dado cadastrado com sucesso!"
            except Exception as e:
                mensagem = f"Erro ao cadastrar dado: {e}"
    return render_template('cadastrar_dado.html', mensagem=mensagem, orgaos=orgaos)

@app.route('/cruzar_car', methods=['GET', 'POST'])
def cruzar_car():
    resultado = None
    if request.method == 'POST':
        cod_imovel = request.form['cod_imovel']
        fonte_dado = request.form['fonte_dado']

        try:
            conn = conectar_banco()
            cur = conn.cursor()

            if fonte_dado == 'todos':
                fontes = [
                    {'nome': 'Prodes', 'schema': 'terrabrasilis_inpe', 'tabela': 'br_inpe_prodes_2024', 'coluna': 'geometry'},
                    {'nome': 'Sipam', 'schema': 'sipam', 'tabela': 'br_sipam_mapa_fogo', 'coluna': 'geom'},
                    {'nome': 'Mapbiomas', 'schema': 'mapbiomas', 'tabela': 'br_mapbiomas_alert', 'coluna': 'geometry'}
                ]
                analises = []
                car_encontrado = False

                cur.execute("SELECT 1 FROM sicar WHERE cod_imovel = %s", (cod_imovel,))
                car_encontrado = bool(cur.fetchone())

                for fonte in fontes:
                    intersecao = consultar_intersecao(cur, cod_imovel, fonte['schema'], fonte['tabela'], fonte['coluna'])
                    if intersecao:
                        analises.append({
                            'fonte': fonte['nome'],
                            'intersecao': True,
                            'area_intersecao': float(intersecao[0]),
                            'percentual': float(intersecao[1])
                        })
                    else:
                        analises.append({
                            'fonte': fonte['nome'],
                            'intersecao': False
                        })

                resultado = {
                    'car_encontrado': car_encontrado,
                    'analises': analises
                }

            else:
                fontes_map = {
                    'prodes': ('terrabrasilis_inpe', 'br_inpe_prodes_2024', 'geometry'),
                    'sipam': ('sipam', 'br_sipam_mapa_fogo', 'geom'),
                    'mapbiomas': ('mapbiomas', 'br_mapbiomas_alert', 'geometry')
                }

                schema, tabela, coluna_geom = fontes_map.get(fonte_dado)
                intersecao = consultar_intersecao(cur, cod_imovel, schema, tabela, coluna_geom)

                if intersecao:
                    resultado = {
                        'car_encontrado': True,
                        'intersecao': True,
                        'area_intersecao': float(intersecao[0]),
                        'percentual': float(intersecao[1])
                    }
                else:
                    cur.execute("SELECT 1 FROM sicar WHERE cod_imovel = %s", (cod_imovel,))
                    existe = cur.fetchone()
                    resultado = {
                        'car_encontrado': bool(existe),
                        'intersecao': False
                    }

        except Exception as e:
            resultado = {'erro': str(e)}
        finally:
            cur.close()
            conn.close()

    return render_template('cruzar_car.html', resultado=resultado)

if __name__ == '__main__':
    app.run(debug=True)