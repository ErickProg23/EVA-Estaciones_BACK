from flask import Blueprint, request, jsonify
from models import db, Puesto, Estacion, Empleado, Rol, Usuario
import jwt, datetime

personal_bp = Blueprint('personal', __name__)

@personal_bp.route('/api/getPersonal', methods=['GET'])
def getPersonal():
    try:
        personal = Empleado.query.all()
        personal_list = []
        for p in personal:
            personal_list.append({
                'id': p.id,
                'nombre': p.nombre,
                'puesto_id': p.puesto_id,
                'puesto': p.puesto.nombre  if p.puesto else None,
                'estacion_id': p.estacion_id,
                'estacion': p.estacion.nombre if p.estacion else None,
                'num_empleado': p.num_empleado,
                'tipo_evaluacion': p.tipo_evaluacion,
                'activo': p.activo,
            })
        return jsonify({'success': True, 'personal': personal_list})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al procesar la solicitud', 'error': str(e)}), 500

@personal_bp.route('/api/newPersonal', methods=['POST'])
def newPersonal():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        puesto_id = data.get('puesto_id')
        estacion_id = data.get('estacion_id')
        num_empleado = data.get('num_empleado')
        tipo_evaluacion = data.get('tipo_evaluacion')
        activo = data.get('activo', True)
        if not all([nombre, puesto_id, estacion_id, num_empleado, tipo_evaluacion]):
            return jsonify({'success': False, 'message': 'Faltan datos'}), 400
        personal = Empleado(nombre=nombre, puesto_id=puesto_id, estacion_id=estacion_id, num_empleado=num_empleado, tipo_evaluacion=tipo_evaluacion, activo=activo)
        db.session.add(personal)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Empleado added successfully'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al procesar la solicitud', 'error': str(e)}), 500
    
@personal_bp.route('/api/updateEmpleado/<int:id>', methods=['PUT'])
def updateEmpleado(id):
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        puesto_id = data.get('puesto_id')
        estacion_id = data.get('estacion_id')
        num_empleado = data.get('num_empleado')
        tipo_evaluacion = data.get('tipo_evaluacion')
        activo = data.get('activo', True)
        if not all([nombre, puesto_id, estacion_id, num_empleado, tipo_evaluacion]):
            return jsonify({'success': False, 'message': 'Faltan datos'}), 400
        personal = Empleado.query.get(id)
        if not personal:
            return jsonify({'success': False, 'message': 'Empleado no encontrado'}), 404
        personal.nombre = nombre
        personal.puesto_id = puesto_id
        personal.estacion_id = estacion_id
        personal.num_empleado = num_empleado
        personal.tipo_evaluacion = tipo_evaluacion
        personal.activo = activo
        db.session.commit()
        return jsonify({'success': True, 'message': 'Empleado updated successfully', 'personal': personal})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al procesar la solicitud', 'error': str(e)}), 500

@personal_bp.route('/api/deleteEmpleado/<int:id>', methods=['PUT'])
def deleteEmpleado(id):
    try:
        personal = Empleado.query.get(id)
        if not personal:
            return jsonify({'success': False, 'message': 'Empleado no encontrado'}), 404
        personal.activo = False
        db.session.commit()
        return jsonify({'success': True, 'message': 'Empleado deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al procesar la solicitud', 'error': str(e)}), 500