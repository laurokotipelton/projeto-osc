from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64))
    email = db.Column(db.String(120), unique=True, index=True)
    senha_hash = db.Column(db.String(128))

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    endereco = db.Column(db.String(200))
    observacoes = db.Column(db.Text)
    
class OrdemServico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    status = db.Column(db.String(20), default='Aguardando')
    data_criacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    data_conclusao = db.Column(db.DateTime, nullable=True)
    valor = db.Column(db.Numeric(10, 2), nullable=True)
    observacoes = db.Column(db.Text)

    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    cliente = db.relationship('Cliente', backref=db.backref('ordens', lazy=True))

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    quantidade = db.Column(db.Integer, default=0)
    unidade = db.Column(db.String(20), default='un')  # Ex: un, kg, m
    categoria = db.Column(db.String(50))
    preco = db.Column(db.Numeric(10, 2), nullable=True)  # opcional

class MovimentacaoEstoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)  # Entrada, Saída, Ajuste
    quantidade = db.Column(db.Integer, nullable=False)
    observacao = db.Column(db.Text)
    data = db.Column(db.DateTime, default=db.func.current_timestamp())

    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    produto = db.relationship('Produto', backref=db.backref('movimentacoes', lazy=True))

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    usuario = db.relationship('Usuario', backref=db.backref('movimentacoes_realizadas', lazy=True))
