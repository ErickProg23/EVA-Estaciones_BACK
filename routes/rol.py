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
                'descripcion': r.descripcion,
                'activo': r.activo
            })
        return jsonify(roles_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rol_bp.route('/api/createRol', methods=['POST'])
def createRol():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        descripcion = data.get('descripcion')
        activo = data.get('activo', True)
        if not nombre:
            return jsonify({'success': False, 'message': 'Nombre es requerido'}), 400
        existente = Rol.query.filter_by(nombre=nombre).first()
        if existente:
            return jsonify({'success': False, 'message': 'El rol ya existe'}), 400
        rol = Rol(nombre=nombre, descripcion=descripcion, activo=activo)
        db.session.add(rol)
        db.session.commit()
        return jsonify({'success': True, 'rol': {'id': rol.id, 'nombre': rol.nombre, 'descripcion': rol.descripcion, 'activo': rol.activo}}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@rol_bp.route('/api/updateRol/<int:id>', methods=['PUT'])
def updateRol(id):
    try:
        rol = Rol.query.get(id)
        if not rol:
            return jsonify({'success': False, 'message': 'Rol no encontrado'}), 404
        data = request.get_json()
        if data.get('nombre') is not None:
            rol.nombre = data.get('nombre')
        if 'descripcion' in data:
            rol.descripcion = data.get('descripcion')
        if 'activo' in data:
            rol.activo = data.get('activo')
        db.session.commit()
        return jsonify({'success': True, 'rol': {'id': rol.id, 'nombre': rol.nombre, 'descripcion': rol.descripcion, 'activo': rol.activo}}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

