from flask import Flask, render_template, request
import psycopg2

app = Flask(__name__)

# Configurações do banco de dados
DATABASE_CONFIG = {
    'dbname': 'dados_governo',
    'user': 'postgres',
    'password': '191010',
    'host': 'localhost'
}

def conectar_banco():
    """Conecta ao banco de dados PostgreSQL."""
    return psycopg2.connect(**DATABASE_CONFIG)

@app.route('/')
def index():
    """Página inicial."""
    return render_template('cadastrar_orgao.html')

@app.route('/cadastrar_orgao', methods=['POST'])
def cadastrar_orgao():
    """Cadastra um novo órgão na tabela agency."""
    # Recupera os dados do formulário
    nome_orgao = request.form['nome_orgao']
    site_oficial = request.form['site_oficial']

    # Insere os dados no banco de dados
    try:
        conn = conectar_banco()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO agency (nome_orgao, site_oficial) VALUES (%s, %s);",
            (nome_orgao, site_oficial)
        )
        conn.commit()
        cur.close()
        conn.close()
        mensagem = "Órgão cadastrado com sucesso!"
    except Exception as e:
        mensagem = f"Erro ao cadastrar órgão: {e}"

    # Exibe uma mensagem de sucesso ou erro
    return render_template('cadastrar_orgao.html', mensagem=mensagem)

if __name__ == '__main__':
    app.run(debug=True)