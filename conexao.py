from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
import bcrypt
from functools import wraps
from datetime import date

import pandas as pd
import numpy as np
from ofxparse import OfxParser
import io
import unicodedata

from simulador import calcular_investimento, format_currency, calcular_financiamento, locale


app = Flask(__name__)
app.secret_key = 'senha'
app.jinja_env.filters['currency'] = format_currency

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'ifinancas'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def strip_accents(text):
    return ''.join(
        ch for ch in unicodedata.normalize('NFKD', str(text))
        if not unicodedata.combining(ch)
    )

def read_ofx_statement(file_stream):
    ofx = OfxParser.parse(file_stream)
    account = ofx.account
    statement = account.statement
    
    transacoes = []
    for transaction in statement.transactions:
        transacoes.append({
            'Data': transaction.date,
            'Descricao': transaction.memo,
            'Valor': transaction.amount
        })
    
    if not transacoes:
        return pd.DataFrame()
        
    df = pd.DataFrame(transacoes)
    
    df['Data'] = pd.to_datetime(df['Data']).dt.date
    df['Valor'] = pd.to_numeric(df['Valor'])
    return df

def categorize(description):
    
    d = strip_accents(str(description)).lower()
    if any(k in d for k in ['salario', 'ordenado', 'vencimento']): return 'Receita'
    if 'pix recebido' in d: return 'Receita'
    if any(k in d for k in ['restaurante', 'ifood', 'rappi', 'lanche']): return 'Alimentação'
    if 'supermercado' in d or 'mercado' in d: return 'Mercado'
    if 'transporte' in d or 'uber' in d or '99' in d: return 'Transporte'
    if any(k in d for k in ['conta de luz', 'energia', 'claro', 'net', 'vivo', 'tim']): return 'Contas Fixas'
    if 'farmacia' in d or 'drogaria' in d: return 'Saúde'
    if 'aluguel' in d: return 'Moradia'
    return 'Outros'


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça o login para acessar esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def cadastrar_usuario(nome, email, senha):
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
        query = "INSERT INTO usuario (nome, email, senha, data_cadastro) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (nome, email, senha_hash, date.today()))
        conexao.commit()
        return True
    except mysql.connector.Error as erro:
        print(f"Erro ao cadastrar: {erro}")
        return False
    finally:
        if 'conexao' in locals() and conexao.is_connected():
            cursor.close()
            conexao.close()

def verificar_login(email, senha):
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)
        query = "SELECT * FROM usuario WHERE email = %s"
        cursor.execute(query, (email,))
        usuario = cursor.fetchone()
        if usuario:
            senha_hash_bd = usuario['senha'].encode('utf-8')
            if bcrypt.checkpw(senha.encode('utf-8'), senha_hash_bd):
                return usuario
        return None
    except mysql.connector.Error as erro:
        print(f"Erro ao verificar login: {erro}")
        return None
    finally:
        if 'conexao' in locals() and conexao.is_connected():
            cursor.close()
            conexao.close()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = verificar_login(email, senha)
        if usuario:
            session['logged_in'] = True
            session['user_id'] = usuario['id_usuario']
            session['user_name'] = usuario['nome']
            session['user_email'] = usuario['email']
            session['user_senha'] = usuario['senha']
            return redirect(url_for('dashboard'))
        else:
            flash('E-mail ou senha inválidos. Tente novamente.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        if cadastrar_usuario(nome, email, senha):
            flash('Cadastro realizado com sucesso! Faça o login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Erro ao realizar o cadastro. Tente novamente.', 'error')
            return redirect(url_for('cadastro'))
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    conexao = get_db_connection()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute("SELECT SUM(valor) as total FROM receita WHERE id_usuario = %s", (user_id,))
    total_receitas = cursor.fetchone()['total'] or 0

    cursor.execute("SELECT SUM(valor) as total FROM despesa WHERE id_usuario = %s", (user_id,))
    total_despesas = cursor.fetchone()['total'] or 0
    
    saldo_atual = total_receitas - total_despesas

    cursor.execute("SELECT nome, valor_objetivo, valor_atual FROM meta_financeira WHERE id_usuario = %s", (user_id,))
    metas = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template(
        'dashboard.html',
        user_name=session.get('user_name'),
        saldo_atual=f"{saldo_atual:.2f}",
        metas=metas,
        total_receitas=total_receitas,
        total_despesas=total_despesas
    )

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    user_id = session['user_id']
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        try:
            conexao = get_db_connection()
            cursor = conexao.cursor()

            if senha:
                senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
                query = "UPDATE usuario SET nome = %s, email = %s, senha = %s WHERE id_usuario = %s"
                cursor.execute(query, (nome, email, senha_hash, user_id))
            else:
                query = "UPDATE usuario SET nome = %s, email = %s WHERE id_usuario = %s"
                cursor.execute(query, (nome, email, user_id))

            conexao.commit()
            session['user_name'] = nome
            session['user_email'] = email
            flash('Seus dados foram alterados com sucesso!', 'success')

        except mysql.connector.Error as erro:
            print(f"Erro ao atualizar perfil: {erro}")
            flash('Ocorreu um erro ao atualizar seus dados. Tente novamente.', 'error')
        
        finally:
            if 'conexao' in locals() and conexao.is_connected():
                cursor.close()
                conexao.close()
        
        return redirect(url_for('perfil'))

    return render_template('perfil.html',
                           user_name=session.get('user_name'),
                           user_email=session.get('user_email'))

@app.route('/upload')
@login_required
def upload():
    return render_template('upload.html', user_name=session.get('user_name'))

@app.route('/analisar', methods=['POST'])
@login_required
def analisar():
    file = request.files.get('extratoFile')
    
    if not file or file.filename == '':
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(url_for('upload'))
    
    if not file.filename.lower().endswith('.ofx'):
         flash('Formato de arquivo inválido. Por favor, envie um arquivo .OFX.', 'error')
         return redirect(url_for('upload'))

    try:
        user_id = session['user_id']
        file_stream = io.BytesIO(file.read())
        df = read_ofx_statement(file_stream)
        
        if df.empty:
            flash('O arquivo OFX está vazio ou não contém transações.', 'warning')
            return redirect(url_for('upload'))

        df['Categoria'] = df['Descricao'].apply(categorize)
        
        conexao = get_db_connection()
        cursor = conexao.cursor()
        
        receitas_add = 0
        despesas_add = 0

        for _, row in df.iterrows():
            if row['Valor'] > 0:
                query = "INSERT INTO receita (id_usuario, descricao, valor, data, categoria) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(query, (user_id, row['Descricao'], row['Valor'], row['Data'], row['Categoria']))
                receitas_add += 1
            elif row['Valor'] < 0:
                query = "INSERT INTO despesa (id_usuario, descricao, valor, data, categoria) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(query, (user_id, row['Descricao'], abs(row['Valor']), row['Data'], row['Categoria']))
                despesas_add += 1
        
        conexao.commit()
        flash(f'Extrato processado! {receitas_add} receitas e {despesas_add} despesas adicionadas.', 'successo')

    except Exception as e:
        if 'conexao' in locals():
            conexao.rollback()
        print(f"Erro ao processar OFX: {e}")
        flash(f'Ocorreu um erro ao processar o arquivo: {str(e)}', 'erro')
    
    finally:
        if 'conexao' in locals() and conexao.is_connected():
            cursor.close()
            conexao.close()
    
    return redirect(url_for('dashboard'))


@app.route('/despesa', methods=['GET', 'POST'])
@login_required
def despesa():
    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = request.form['valor']
        data = request.form['data']
        categoria = request.form['categoria']
        user_id = session['user_id']

        conexao = get_db_connection()
        cursor = conexao.cursor()
        query = "INSERT INTO despesa (id_usuario, descricao, valor, data, categoria) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (user_id, descricao, valor, data, categoria))
        conexao.commit()
        cursor.close()
        conexao.close()
        
        flash('Despesa registrada com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('despesa.html', user_name=session.get('user_name'))

@app.route('/receita', methods=['GET', 'POST'])
@login_required
def receita():
    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = request.form['valor']
        data = request.form['data']
        categoria = request.form['categoria']
        user_id = session['user_id']

        conexao = get_db_connection()
        cursor = conexao.cursor()
        query = "INSERT INTO receita (id_usuario, descricao, valor, data, categoria) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (user_id, descricao, valor, data, categoria))
        conexao.commit()
        cursor.close()
        conexao.close()

        flash('Receita registrada com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('receita.html', user_name=session.get('user_name'))

@app.route('/meta', methods=['GET', 'POST'])
@login_required
def meta():
    user_id = session['user_id']

    if request.method == 'POST':
        nome = request.form['nome']
        valor_objetivo = request.form['valor_objetivo']
        data_limite = request.form['data_limite']
        
        conexao_post = None
        cursor_post = None
        try:
            conexao_post = get_db_connection()
            cursor_post = conexao_post.cursor() 
            query = "INSERT INTO meta_financeira (id_usuario, nome, valor_objetivo, data_limite, valor_atual) VALUES (%s, %s, %s, %s, 0)"
            cursor_post.execute(query, (user_id, nome, valor_objetivo, data_limite))
            conexao_post.commit()
            flash('Meta criada com sucesso!', 'success')
            
        except mysql.connector.Error as erro:
            print(f"Erro ao criar meta: {erro}")
            flash('Erro ao criar meta.', 'error')
            if conexao_post:
                conexao_post.rollback()
        finally:
            if cursor_post:
                cursor_post.close()
            if conexao_post and conexao_post.is_connected():
                conexao_post.close()
        
        return redirect(url_for('dashboard'))

    metas_existentes = []
    conexao_get = None
    cursor_get = None
    try:
        conexao_get = get_db_connection()
        cursor_get = conexao_get.cursor(dictionary=True) 
        query_get_metas = "SELECT id_meta, nome FROM meta_financeira WHERE id_usuario = %s ORDER BY nome"
        cursor_get.execute(query_get_metas, (user_id,))
        metas_existentes = cursor_get.fetchall()
        
    except mysql.connector.Error as erro:
        print(f"Erro ao buscar metas: {erro}")
        flash('Erro ao carregar suas metas existentes.', 'error')
    finally:
        if cursor_get:
            cursor_get.close()
        if conexao_get and conexao_get.is_connected():
            conexao_get.close()

    return render_template('meta.html', 
                           user_name=session.get('user_name'),
                           metas=metas_existentes)

@app.route('/adicionar_meta', methods=['POST'])
@login_required
def adicionar_meta():
    user_id = session['user_id']
    meta_id = request.form.get('meta_id') 
    
    if not meta_id:
        flash('Nenhuma meta foi selecionada.', 'error')
        return redirect(url_for('meta'))

    try:
        valor_adicionar = float(request.form['valor_adicionar'])
    except ValueError:
        flash('Valor a adicionar inválido.', 'error')
        return redirect(url_for('meta'))

    if valor_adicionar <= 0:
        flash('O valor a adicionar deve ser positivo.', 'error')
        return redirect(url_for('meta'))

    conexao = None
    cursor = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True) 

        cursor.execute("SELECT SUM(valor) as total FROM receita WHERE id_usuario = %s", (user_id,))
        total_receitas = cursor.fetchone()['total'] or 0
        cursor.execute("SELECT SUM(valor) as total FROM despesa WHERE id_usuario = %s", (user_id,))
        total_despesas = cursor.fetchone()['total'] or 0
        saldo_atual = total_receitas - total_despesas

        if valor_adicionar > saldo_atual:
            flash(f'Saldo insuficiente. Você tentou adicionar R$ {valor_adicionar:.2f}, mas seu saldo é R$ {saldo_atual:.2f}.', 'error')
            return redirect(url_for('meta'))

        cursor.execute("SELECT nome FROM meta_financeira WHERE id_meta = %s AND id_usuario = %s", (meta_id, user_id))
        meta_info = cursor.fetchone()
        
        if not meta_info:
            flash('Meta não encontrada. O ID selecionado pode ser inválido.', 'error')
            return redirect(url_for('meta'))
        
        nome_meta = meta_info['nome']
        cursor.close()

        cursor_update = conexao.cursor()
        query_update_meta = "UPDATE meta_financeira SET valor_atual = valor_atual + %s WHERE id_meta = %s"
        cursor_update.execute(query_update_meta, (valor_adicionar, meta_id))

        
        query_insert_despesa = "INSERT INTO despesa (id_usuario, descricao, valor, data, categoria) VALUES (%s, %s, %s, %s, %s)"
        descricao_despesa = f"Aplicação na meta: {nome_meta}"
        cursor_update.execute(query_insert_despesa, (user_id, descricao_despesa, valor_adicionar, date.today(), 'Metas'))
        
        conexao.commit() 
        cursor_update.close()

        flash('Valor adicionado à meta com sucesso! Uma despesa foi registrada para abater do seu saldo.', 'success')

    except mysql.connector.Error as erro:
        if conexao:
            conexao.rollback()
        print(f"Erro ao adicionar valor à meta: {erro}")
        flash('Ocorreu um erro no banco de dados. A operação foi cancelada.', 'error')
    except Exception as e:
        if conexao:
            conexao.rollback()
        print(f"Erro inesperado: {e}")
        flash('Ocorreu um erro inesperado. A operação foi cancelada.', 'error')
    finally:
        if cursor:
            cursor.close()
        if conexao and conexao.is_connected():
            conexao.close()

    return redirect(url_for('dashboard'))


@app.route('/simulador')
@login_required
def simulador():
    return render_template('simulador.html', user_name=session.get('user_name'))

@app.route('/simulador/financiamento', methods=['GET', 'POST'])
@login_required
def simular_financiamento():
    resultados = None
    if request.method == 'POST':
        try:
            valor_total = float(request.form['valor_total'])
            valor_entrada = float(request.form['valor_entrada'])
            taxa_juros = float(request.form['taxa_juros'])
            prazo_meses = int(request.form['prazo_meses'])

            if valor_entrada >= valor_total:
                flash('O valor de entrada não pode ser maior ou igual ao valor total do bem.', 'error')
                return redirect(url_for('simular_financiamento'))
            if prazo_meses <= 0:
                flash('O prazo deve ser de pelo menos 1 mês.', 'error')
                return redirect(url_for('simular_financiamento'))

            resultados = calcular_financiamento(
                valor_total=valor_total,
                valor_entrada=valor_entrada,
                taxa_juros_anual=taxa_juros,
                prazo_meses=prazo_meses
            )
        except (ValueError, KeyError) as e:
            flash(f'Erro nos dados de entrada: {e}. Por favor, preencha todos os campos corretamente.', 'error')
            return redirect(url_for('simular_financiamento'))
        except Exception as e:
            flash(f'Ocorreu um erro inesperado: {e}', 'error')
            return redirect(url_for('simular_financiamento'))

    return render_template('simular-financiamento.html',
                           user_name=session.get('user_name'),
                           resultados=resultados)

@app.route('/simulador/investimento', methods=['GET', 'POST'])
@login_required
def simular_investimento():
    
    resultados = None
    if request.method == 'POST':
        try:
            investimento_inicial = float(request.form['investimento_inicial'])
            aporte_mensal = float(request.form['aporte_mensal'])
            rentabilidade = float(request.form['rentabilidade'])
            prazo = int(request.form['prazo'])

            resultados = calcular_investimento(
                investimento_inicial=investimento_inicial,
                aporte_mensal=aporte_mensal,
                taxa_anual=rentabilidade,
                prazo_meses=prazo
            )
        except (ValueError, KeyError) as e:
            flash(f'Erro nos dados de entrada: {e}. Por favor, preencha todos os campos corretamente.', 'error')
            return redirect(url_for('simular_investimento'))

    return render_template('simular-investimento.html',
                           user_name=session.get('user_name'),
                           resultados=resultados)

@app.route('/excluir_conta')
@login_required
def excluir_conta():
    user_id = session['user_id']
    conexao = None
    cursor = None
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        query_alertas = "DELETE FROM alerta WHERE id_meta IN (SELECT id_meta FROM meta_financeira WHERE id_usuario = %s)"
        cursor.execute(query_alertas, (user_id,))
        
        query_metas = "DELETE FROM meta_financeira WHERE id_usuario = %s"
        cursor.execute(query_metas, (user_id,))
        
        query_despesas = "DELETE FROM despesa WHERE id_usuario = %s"
        cursor.execute(query_despesas, (user_id,))
        
        query_receitas = "DELETE FROM receita WHERE id_usuario = %s"
        cursor.execute(query_receitas, (user_id,))
        
        query_usuario = "DELETE FROM usuario WHERE id_usuario = %s"
        cursor.execute(query_usuario, (user_id,))
        
        conexao.commit()
        
        session.clear()
        flash('Sua conta e todos os seus dados foram excluídos com sucesso.', 'info')
        return redirect(url_for('login'))

    except mysql.connector.Error as erro:
        if conexao:
            conexao.rollback() 
        print(f"Erro ao excluir conta: {erro}")
        flash('Ocorreu um erro ao tentar excluir sua conta. Tente novamente.', 'error')
        return redirect(url_for('perfil'))
    finally:
        if cursor:
            cursor.close()
        if conexao and conexao.is_connected():
            conexao.close()


if __name__ == "__main__": 
    app.run(debug=True)