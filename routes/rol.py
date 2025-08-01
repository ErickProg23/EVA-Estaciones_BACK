from flask import Blueprint, request, jsonify
from models import db, Rol
import jwt, datetime

rol_bp = Blueprint('rol', __name__)

@rol_bp.route('/api/getRoles', methods=['GET'])
def getRoles():
    try:
        roles = Rol.query.all()
        roles_data = []
        for r in roles:
            roles_data.append({
                'id': r.id,
                'nombre': r.nombre,
            })
        return jsonify(roles_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

