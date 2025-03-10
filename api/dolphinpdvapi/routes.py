from dolphinpdvapi import app, database, jsonify, request
from dolphinpdvapi.models import Usuario


@app.route('/criar_usuario', methods=['POST'])
def create_user():
    data = request.json
    new_user = Usuario(nome=data['nome'], username=data['username'], email=data['email'], senha=data['senha'])
    database.session.add(new_user)
    database.session.commit()
    
    return jsonify({'mensagem': 'Usuário criado com sucesso!'}), 201

@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    usuarios = Usuario.query.all()
    return jsonify([{
        'id': u.id, 'nome': u.nome, 'username': u.username, 'email': u.email,
        'administrador': u.administrador, 'ativo': u.ativo
    } for u in usuarios])