from flask import Flask, render_template
import psycopg2

app = Flask(__name__)

DATABASE_CONFIG = {
    'dbname': 'monitoramento_dados',
    'user': 'postgres',
    'password': '191010',
    'host': 'localhost'
}

@app.route('/')
def index():
    conn = psycopg2.connect(**DATABASE_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT * FROM data_monitoring")
    dados = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', dados=dados)

if __name__ == "__main__":
    app.run(debug=True)