from app import database
from datetime import datetime

class Usuario(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    nome = database.Column(database.String(100), nullable=False)
    username = database.Column(database.String(100), unique=True, nullable=False)
    email = database.Column(database.String(100), unique=True, nullable=False)
    senha = database.Column(database.String(100), nullable=False)
    foto_perfil = database.Column(database.String(200))
    administrador = database.Column(database.Boolean, default=False)
    ativo = database.Column(database.Boolean, default=True)

class Categoria(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    nome_categoria = database.Column(database.String(100), nullable=False)

class Produto(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    nome_produto = database.Column(database.String(100), nullable=False)
    id_categoria = database.Column(database.Integer, database.ForeignKey('categoria.id'), nullable=False)
    preco = database.Column(database.Float, nullable=False)
    codigo_barra = database.Column(database.String(100), unique=True, nullable=True)

class Lote(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    id_produto = database.Column(database.Integer, database.ForeignKey('produto.id'), nullable=False)
    quantidade = database.Column(database.Integer, nullable=False)
    data_inclusao = database.Column(database.Date, default=datetime.now, nullable=False)
    data_validade = database.Column(database.Date, nullable=True)

class Estoque(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    id_produto = database.Column(database.Integer, database.ForeignKey('produto.id'), nullable=False)
    id_lote = database.Column(database.Integer, database.ForeignKey('lote.id'), nullable=False)
    quantidade = database.Column(database.Integer, nullable=False)

class MetodoPgto(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    nome_metodo_pgto = database.Column(database.String(100), nullable=False)

class Venda(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    data_hora_venda = database.Column(database.DateTime, default=datetime.now, nullable=False)
    desconto = database.Column(database.Float, default=0.0)
    acrescimo = database.Column(database.Float, default=0.0)
    valor_total = database.Column(database.Float, nullable=False)
    id_metodo_pgto = database.Column(database.Integer, database.ForeignKey('metodo_pgto.id'), nullable=False)
    usuario_id = database.Column(database.Integer, database.ForeignKey('usuario.id'), nullable=False)

class VendaProduto(database.Model):
    item = database.Column(database.Integer, primary_key=True)
    id_venda = database.Column(database.Integer, database.ForeignKey('venda.id'), nullable=False)
    codigo_produto = database.Column(database.Integer, database.ForeignKey('produto.id'), nullable=False)
    unidades = database.Column(database.Integer, nullable=False)
    preco_unitario = database.Column(database.Float, nullable=False)
    preco_total = database.Column(database.Float, nullable=False)

