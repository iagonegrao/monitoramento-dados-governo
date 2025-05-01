from flask import Flask, render_template, request, redirect, url_for, request
import psycopg2
from psycopg2 import sql
from werkzeug.utils import secure_filename
import os
from sqlalchemy import create_engine

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/logos'  # Pasta para armazenar as imagens
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Cria a pasta se não existir

# Configuração do banco de dados
DATABASE_CONFIG = {
    'dbname': 'dados_governo',
    'user': 'postgres',
    'password': '191010',
    'host': 'localhost'
}

DATABASE_URL = "postgresql+psycopg2://postgres:191010@localhost/dados_governo"
engine = create_engine(DATABASE_URL)

def conectar_banco():
    """Conecta ao banco de dados PostgreSQL."""
    return psycopg2.connect(**DATABASE_CONFIG)

@app.route('/')
def index():
    """Página inicial com listagem de órgãos e dados cadastrados."""
    try:
        with conectar_banco() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nome_orgao, site_oficial, logo FROM agency;")
                orgaos = cur.fetchall()

                cur.execute("SELECT id, nome_dado, site_oficial FROM data_monitoring;")
                dados = cur.fetchall()
    except Exception as e:
        orgaos, dados = [], []
        print(f"Erro ao carregar dados: {e}")  # Depuração

    return render_template('index.html', orgaos=orgaos, dados=dados)

@app.route('/cadastrar_orgao', methods=['GET', 'POST'])
def cadastrar_orgao():
    """Cadastra um novo órgão na tabela agency."""
    mensagem = None

    if request.method == 'POST':
        nome_orgao = request.form.get('nome_orgao')
        site_oficial = request.form.get('site_oficial')
        logo = request.files.get('logo')

        if not nome_orgao or not site_oficial:
            mensagem = "Erro: Todos os campos são obrigatórios!"
        else:
            logo_filename = None  # Inicializa a variável antes de usá-la
            if logo and logo.filename:
                logo_filename = secure_filename(logo.filename)  # Asegure-se de que o nome do arquivo é seguro
                logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
                logo.save(logo_path)
                logo_filename = f"/{logo_path}"  # Caminho relativo para exibição

            try:
                with conectar_banco() as conn:
                    with conn.cursor() as cur:
                        # Verifique se logo_filename foi definido antes de tentar inseri-lo no banco de dados
                        if logo_filename is None:
                            logo_filename = ''  # Ou um valor padrão, se não houver logo

                        cur.execute("INSERT INTO agency (nome_orgao, site_oficial, logo) VALUES (%s, %s, %s);",
                                    (nome_orgao, site_oficial, logo_filename))
                        mensagem = "Órgão cadastrado com sucesso!"
            except Exception as e:
                mensagem = f"Erro ao cadastrar órgão: {e}"

    return render_template('cadastrar_orgao.html', mensagem=mensagem)

@app.route('/editar_orgao/<int:orgao_id>', methods=['GET', 'POST'])
def editar_orgao(orgao_id):
    """Edita um órgão já cadastrado."""
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
                logo_filename = orgao[3]  # Mantém o logo atual caso não seja atualizado
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
    """Exibe o formulário para cadastrar um novo dado a ser monitorado e processa a inserção."""
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
        
        try:
            conn = conectar_banco()
            cur = conn.cursor()
            
            # 1. Verificar se CAR existe
            cur.execute("SELECT geom FROM sicar WHERE cod_imovel = %s", (cod_imovel,))
            car_data = cur.fetchone()
            
            if not car_data:
                resultado = {'car_encontrado': False}
            else:
                # 2. Calcular interseção com PRODES
                query = """
                        SELECT 
                            ST_Area(ST_Intersection(ST_Transform(s.geom, 4674), ST_Transform(p.geometry, 4674))::geography) / 10000 AS area_ha,
                            (ST_Area(ST_Intersection(ST_Transform(s.geom, 4674), ST_Transform(p.geometry, 4674))::geography) / 
                            ST_Area(ST_Transform(s.geom, 4674)::geography)) * 100.0 AS percentual
                        FROM sicar s, terrabrasilis_inpe.br_inpe_prodes_2024 p
                        WHERE s.cod_imovel = %s 
                        AND ST_Intersects(ST_Transform(s.geom, 4674), ST_Transform(p.geometry, 4674));
                    """
                cur.execute(query, (cod_imovel,))
                row = cur.fetchone()
                
                if row:
                    resultado = {
                        'car_encontrado': True,
                        'intersecao': True,
                        'area_intersecao': float(row[0]),
                        'percentual': float(row[1])
                    }
                else:
                    resultado = {
                        'car_encontrado': True,
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