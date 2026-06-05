from flask import Blueprint, request, jsonify
from models import db, Puesto, Estacion
import jwt, datetime

puestos_bp = Blueprint('puestos', __name__)

@puestos_bp.route('/getPuestos', methods=['GET'])
def getPuestos():
    try:
        puestos = Puesto.query.all()
        return jsonify({'success': True, 'puestos': [{'id': p.id, 'nombre': p.nombre, 'estacion_id': p.estacion_id, 'activo': p.activo} for p in puestos]})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al procesar la solicitud', 'error': str(e)}), 500

@puestos_bp.route('/api/newPuesto', methods=['POST'])
def newPuesto():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        estacion_id = data.get('estacion_id')
        if not nombre or not estacion_id:
            return jsonify({'success': False, 'message': 'Faltan datos: nombre o estacion_id'}), 400
        activo = data.get('activo', True)
        nuevo_puesto = Puesto(nombre=nombre, estacion_id=estacion_id, activo=activo)
        db.session.add(nuevo_puesto)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Puesto creado correctamente', 'puesto': {'id': nuevo_puesto.id, 'nombre': nuevo_puesto.nombre, 'estacion_id': nuevo_puesto.estacion_id, 'activo': nuevo_puesto.activo}})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al procesar la solicitud', 'error': str(e)}), 500

@puestos_bp.route('/api/updatePuesto/<int:puesto_id>', methods=['PUT'])
def updatePuesto(puesto_id):
    try:
        data = request.get_json()
        puesto = Puesto.query.get(puesto_id)
        if not puesto:
            return jsonify({'success': False, 'message': 'Puesto no encontrado'}), 404
        nombre = data.get('nombre')
        estacion_id = data.get('estacion_id')
        if not nombre or not estacion_id:
            return jsonify({'success': False, 'message': 'Faltan datos: nombre o estacion_id'}), 400
        puesto.nombre = nombre
        puesto.estacion_id = estacion_id
        activo = data.get('activo', True)
        puesto.activo = activo
        db.session.commit()
        return jsonify({'success': True, 'message': 'Puesto actualizado correctamente', 'puesto': {'id': puesto.id, 'nombre': puesto.nombre, 'estacion_id': puesto.estacion_id, 'activo': puesto.activo}})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al procesar la solicitud', 'error': str(e)}), 500


@puestos_bp.route('/api/deletePuesto/<int:puesto_id>', methods=['DELETE'])
def deletePuesto(puesto_id):
    try:
        puesto = Puesto.query.get(puesto_id)
        if not puesto:
            return jsonify({'success': False, 'message': 'Puesto no encontrado'}), 404
        puesto.activo = False
        db.session.commit()
        return jsonify({'success': True, 'message': 'Puesto eliminado correctamente', 'puesto': {'id': puesto.id, 'nombre': puesto.nombre, 'estacion_id': puesto.estacion_id, 'activo': puesto.activo}})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al procesar la solicitud', 'error': str(e)}), 500