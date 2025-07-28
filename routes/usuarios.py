# routes/usuarios.py
from flask import Blueprint, request, jsonify
from models import db, Usuario
import jwt, datetime

SECRET_KEY = 'mi_clave_secreta_segura'  # Usa una más segura y guárdala como variable de entorno


usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    usuario = Usuario.query.filter_by(usuario=username).first()

    if usuario and usuario.password == password:
        # Generar token
        token = jwt.encode({
            'user_id': usuario.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, SECRET_KEY, algorithm='HS256')

        return jsonify({'success': True, 'message': 'Login exitoso', 'token': token})
    else:
        return jsonify({'success': False, 'message': 'Credenciales incorrectas'}), 401

