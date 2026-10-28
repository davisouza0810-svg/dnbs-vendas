from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'chave_secreta_ecommerce'

# Configuração do Administrador
ADMIN_USER = "admin"
ADMIN_PASS = "macacobrancoazul"

def conectar_banco():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123@macacobranco",
        database="meu_banco"
    )

@app.route('/', methods=['GET', 'POST'])
def home():
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)
    
    if request.method == 'POST':
        acao = request.form.get('acao')
        
        if acao == 'cadastrar':
            nome = request.form['nome']
            email = request.form['email']
            senha = request.form['senha']
            idade = request.form['idade'] or None
            telefone = request.form['telefone']
            cpf = request.form['cpf']
            genero = request.form['genero']
            data_nascimento = request.form['data_nascimento'] or None
            
            comando = """
                INSERT INTO usuarios (nome, email, senha, idade, telefone, cpf, genero, data_nascimento) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(comando, (nome, email, senha, idade, telefone, cpf, genero, data_nascimento))
            conexao.commit()
            
            cursor.execute("SELECT id, nome FROM usuarios WHERE email = %s", (email,))
            novo_user = cursor.fetchone()
            session['usuario_id'] = novo_user['id']
            session['usuario_nome'] = novo_user['nome']
            
        elif acao == 'login':
            email = request.form['login_email']
            senha = request.form['login_senha']
            
            cursor.execute("SELECT id, nome FROM usuarios WHERE email = %s AND senha = %s", (email, senha))
            user = cursor.fetchone()
            
            if user:
                session['usuario_id'] = user['id']
                session['usuario_nome'] = user['nome']
                
        cursor.close()
        conexao.close()
        return redirect(url_for('home'))
    
    produtos = []
    if session.get('usuario_id'):
        try:
            cursor.execute("SELECT id, produto, preco_venda, estoque_atual, link FROM produtos;")
            produtos = cursor.fetchall()
        except:
            produtos = []
    
    cursor.close()
    conexao.close()
    
    return render_template('index.html', produtos=produtos)

@app.route('/produto/<int:id_produto>', methods=['GET', 'POST'])
def detalhe_produto(id_produto):
    if not session.get('usuario_id'):
        return redirect(url_for('home'))
        
    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)
    
    if request.method == 'POST':
        comentario = request.form.get('comentario')
        nota = request.form.get('nota')
        usuario_id = session.get('usuario_id')
        
        try:
            comando = "INSERT INTO avaliacoes (produto_id, usuario_id, nota, comentario) VALUES (%s, %s, %s, %s)"
            cursor.execute(comando, (id_produto, usuario_id, nota, comentario))
            conexao.commit()
        except Exception as e:
            print("Erro ao guardar avaliação (crie a tabela avaliacoes se necessário):", e)
            
        cursor.close()
        conexao.close()
        return redirect(url_for('detalhe_produto', id_produto=id_produto))

    cursor.execute("SELECT * FROM produtos WHERE id = %s;", (id_produto,))
    produto = cursor.fetchone()
    
    avaliacoes = []
    try:
        cursor.execute("""
            SELECT a.nota, a.comentario, u.nome 
            FROM avaliacoes a 
            JOIN usuarios u ON a.usuario_id = u.id 
            WHERE a.produto_id = %s;
        """, (id_produto,))
        avaliacoes = cursor.fetchall()
    except:
        pass
        
    cursor.close()
    conexao.close()
    
    return render_template('produto.html', produto=produto, avaliacoes=avaliacoes)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    erro = None
    usuarios = []
    
    if request.method == 'POST':
        adm_user = request.form.get('adm_user')
        adm_senha = request.form.get('adm_senha')
        
        if adm_user == ADMIN_USER and adm_senha == ADMIN_PASS:
            session['admin_logado'] = True
        else:
            erro = "Credenciais de Administrador inválidas!"
            
    if session.get('admin_logado'):
        conexao = conectar_banco()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT id, nome, email, telefone, cpf, genero, data_nascimento FROM usuarios;")
        usuarios = cursor.fetchall()
        cursor.close()
        conexao.close()
        
    return render_template('admin.html', usuarios=usuarios, erro=erro)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logado', None)
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    