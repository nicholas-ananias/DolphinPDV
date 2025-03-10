from dolphinpdvapi import app, database
from dolphinpdvapi.models import Usuario, Categoria, Produto, Lote, Estoque, MetodoPgto, Venda, VendaProduto

with app.app_context():
    database.create_all()

with app.app_context():
    usuario = Usuario(nome='Admin', username='admin', email='admin@admin.com.br', senha='admin', administrador=True)
    database.session.add(usuario)
    database.session.commit()

with app.app_context():
    meus_usuarios = Usuario.query.all()
    for usuario in meus_usuarios:
        print(usuario)