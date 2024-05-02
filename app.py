from flask import Flask, render_template, redirect, request, flash, session
import sqlite3
import os
import re

app = Flask(__name__)

def generate_secret_key():
    return os.urandom(24).hex()

app.secret_key = generate_secret_key()
print("Chave secreta:", app.secret_key)

@app.route('/')
def inicio():
    return redirect('/home')

@app.route('/home')
def index():
    conn = sqlite3.connect('estoque.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM registro")
    nome = cursor.fetchall()
    conn.close()

    return render_template('index.html', nome=nome)

@app.route('/login')
def login():
        return render_template('login.html')

@app.route('/log', methods=['GET', 'POST'] )
def log():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        try:
            conn = sqlite3.connect('estoque.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM registro WHERE emai = ? AND senha = ?", (email, senha))
            resultado = cursor.fetchone()[0]
        except sqlite3.Error as e:
            flash(f"Erro de banco de dados: {e}", "error")
            return redirect('/login')
        finally:
            conn.close()

        if resultado > 0:
            return redirect('/home')
        else:
            flash("Email ou senha incorretos.", "error")
            return redirect('/login')
    return render_template('login.html')

@app.route('/loginempresa')
def login_empresa():
    return render_template('loginempresa.html')


@app.route('/loge', methods=['GET', 'POST'])
def loge():
    if request.method == 'POST':
        nome_empresa = request.form['nome']
        senha = request.form['senha']

        try:
            with sqlite3.connect('registro.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM empresas WHERE nome_empresa = ? AND senha = ?", (nome_empresa, senha))
                resultado = cursor.fetchone()[0]
        except sqlite3.Error as e:
            flash(f"Erro de banco de dados: {e}", "error")
            return redirect('/loginempresa')

        if resultado > 0:
            session['nome'] = nome_empresa
            return redirect(f'/consultar/{nome_empresa}')
        else:
            flash("Nome ou senha incorretos.", "error")
            return redirect('/loginempresa')

    return render_template('loginempresa.html')


@app.route('/consultar/<nome>')
def consultar_empresa(nome):
    # Verifica se o nome da empresa contém apenas caracteres alfanuméricos e "_"
    if re.match("^[a-zA-Z0-9_]+$", nome):
        tabela = f"produtos_{nome}"  # Supondo que você tenha tabelas separadas para cada empresa
        conn = sqlite3.connect('registro.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {tabela}")
        produtos = cursor.fetchall()
        conn.close()

        # Renderiza o template mesmo que não haja produtos na tabela
        return render_template('consultar.html', empresa_nome=nome, produtos=produtos)
    else:
        flash("Nome de empresa inválido.", "error")
        return redirect('/consultar')  # Redireciona de volta para a página de consulta

@app.route('/registrar')
def registro():
    return render_template('registar.html')

@app.route('/registrarempresa')
def registro_empresa():
    return render_template('registrarempresa.html')

@app.route('/authempresa', methods=['POST'])
def authempresa():
    if request.method == 'POST':
        nome_empresa = request.form['empresa']
        senha = request.form['senha']

        # Conectar ao banco de dados
        conn = sqlite3.connect('registro.db')
        cursor = conn.cursor()

        # Criar tabela se não existir
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS empresas (
                            id INTEGER PRIMARY KEY,
                            nome_empresa TEXT,
                            senha TEXT
                        )''')
        
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS produtos_{nome_empresa} (
                            codigo INTEGER PRIMARY KEY,
                            nome TEXT,
                            quantidade INTEGER,
                            entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )''')
        
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS entradas_{nome_empresa} (
                            codigo INTEGER PRIMARY KEY,
                            nome TEXT,
                            quantidade INTEGER,
                            entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )''')


        # Inserir dados na tabela
        cursor.execute("INSERT INTO empresas (nome_empresa, senha) VALUES (?, ?)", (nome_empresa, senha))

        # Commit e fechar a conexão
        conn.commit()
        conn.close()

        # Redirecionar para a página inicial após o registro
        return redirect('/loginempresa')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
       if request.method == 'POST':
        nomeu = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        empresa = request.form['empresa']

        conn = sqlite3.connect('estoque.db')
        cursor = conn.cursor()

        cursor.execute("INSERT INTO registro (nome, emai, senha, empresa) VALUES (?, ?, ?, ?)", (nomeu, email, senha, empresa ))
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {empresa}(codigo INTEGER PRIMARY KEY, nome TEXT, quatidae INTEGER)")
        conn.commit()
        conn.close()

        return redirect('/home')
    

@app.route('/consultar')
def consultar_estoque():
    nome_empresa = session.get('nome')
    if nome_empresa:
        return redirect(f'/consultar/{nome_empresa}')
    else:
        return redirect('/loginempresa')

@app.route('/entradas')
def exibir_entradas():
    nome_empresa = session.get('nome')
    if nome_empresa:
        conn = sqlite3.connect('registro.db')
        cursor = conn.cursor()

        tabela2 = f"entradas_{nome_empresa}"

        cursor.execute(f"SELECT nome, codigo, quantidade, entrada FROM {tabela2}" )
        entradas = cursor.fetchall()

        conn.close()

        return render_template('entradas.html', entradas=entradas)
    else:
        # Se o usuário não estiver logado, redirecione para a página de login
        return redirect('/loginempresa')



@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
    nome_empresa = session.get('nome')
    if nome_empresa:
        if request.method == 'POST':
            nome = request.form['nome']
            codigo = request.form['codigo']
            quantidade = request.form['quantidade']

            conn = sqlite3.connect('registro.db')
            cursor = conn.cursor()

            tabela = f"produtos_{nome_empresa}"
            tabela2 = f"entradas_{nome_empresa}"

            cursor.execute("SELECT codigo FROM " + tabela + " WHERE codigo = ?", (codigo,))
            cursor.execute("SELECT codigo FROM " + tabela2 + " WHERE codigo = ?", (codigo,))
            resultado = cursor.fetchone()

            if resultado:
                conn.close()
                return render_template('adicionar.html', mensagem="O código já está em uso. Por favor, escolha outro.")

            cursor.execute("INSERT INTO " + tabela + " (nome, codigo, quantidade) VALUES (?, ?, ?)", (nome, codigo, quantidade))
            cursor.execute("INSERT INTO " + tabela2 + " (nome, codigo, quantidade) VALUES (?, ?, ?)", (nome, codigo, quantidade))
            conn.commit()
            conn.close()

            return redirect(f'/consultar/{nome_empresa}')

    else:
        return redirect('/loginempresa')

    return render_template('adicionar.html')

@app.route('/quantidade', methods=['GET', 'POST'])
def remover():
    nome_empresa = session.get('nome')
    if nome_empresa:
        if request.method == 'POST':
            codigo = request.form['codigo']
            quantidade = int(request.form['quantidade'])  # Converta a quantidade para um número inteiro

            conn = sqlite3.connect('registro.db')
            cursor = conn.cursor()

            tabela = f"produtos_{nome_empresa}"

            cursor.execute(f"SELECT quantidade FROM {tabela} WHERE codigo = ?", (codigo,))
            estoque_atual = cursor.fetchone()

            if estoque_atual:
                estoque_atual = estoque_atual[0]
                # Verifique se há estoque suficiente para a operação
                if estoque_atual >= quantidade:
                    novo_estoque = estoque_atual - quantidade
                    cursor.execute(f"UPDATE {tabela} SET quantidade = ? WHERE codigo = ?", (novo_estoque, codigo))
                    conn.commit()
                    conn.close()
                    return redirect(f'/consultar/{nome_empresa}')
                else:
                    cursor.execute(f"DELETE FROM {tabela} WHERE codigo = ?", (codigo,))
                    conn.commit()
                    conn.close()
                    return redirect(f'/consultar/{nome_empresa}')
            else:
                flash("Produto não encontrado.", "error")
                return redirect(f'/consultar/{nome_empresa}')

    else:
        return redirect('/loginempresa')

    return render_template('editar.html')
 

if __name__ == '__main__':
    app.run(debug=True)