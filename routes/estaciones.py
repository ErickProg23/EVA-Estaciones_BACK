from flask import Blueprint, request, jsonify
from models import db, Estacion
import jwt, datetime

estacion_bp = Blueprint('estacion', __name__)

@estacion_bp.route('/getEstaciones', methods=['GET'])
def getEstaciones():
    try:
        estaciones = Estacion.query.all()
        estaciones_data = []
        for e in estaciones:
            estaciones_data.append({
                'id': e.id,
                'nombre': e.nombre,
                'activo': e.activo,
                'turnos_disponibles': e.turnos_disponibles
            })
        return jsonify(estaciones_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@estacion_bp.route('/createEstacion', methods=['POST'])
def createEstacion():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        activo = data.get('activo', True)
        fecha_creacion = datetime.datetime.now()
        if not nombre:
            return jsonify({'success': False, 'message': 'El nombre de la estacion es obligatorio'}), 400
        try:
            turnos_disponibles = int(data.get('turnos_disponibles'))
        except Exception:
            return jsonify({'success': False, 'message': 'turnos_disponibles inválido'}), 400
        estacion = Estacion(nombre=nombre, activo=activo, fecha_creacion=fecha_creacion, turnos_disponibles=turnos_disponibles)
        db.session.add(estacion)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Estacion creada correctamente', 'estacion_id': estacion.id})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al procesar la solicitud', 'error': str(e)}), 500

@estacion_bp.route('/deleteEstacion/<int:estacion_id>', methods=['PUT'])
def deleteEstacion(estacion_id):
    try:
        estacion = Estacion.query.get(estacion_id)
        if not estacion:
            return jsonify({'success': False, 'message': 'Estacion no encontrada'}), 404
        estacion.activo = False
        db.session.commit()
        return jsonify({'success': True, 'message': 'Estacion eliminada correctamente'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al procesar la solicitud', 'error': str(e)}), 500

@estacion_bp.route('/updateEstacion/<int:estacion_id>', methods=['PUT'])
def updateEstacion(estacion_id):
    try:
        estacion = Estacion.query.get(estacion_id)
        if not estacion:
            return jsonify({'success': False, 'message': 'Estacion no encontrada'}), 404

        data = request.get_json() or {}

        if 'nombre' in data:
            estacion.nombre = data.get('nombre')
        if 'activo' in data:
            estacion.activo = data.get('activo')
        if 'turnos_disponibles' in data:
            try:
                estacion.turnos_disponibles = int(data.get('turnos_disponibles'))
            except Exception:
                return jsonify({'success': False, 'message': 'turnos_disponibles inválido'}), 400

        db.session.commit()
        return jsonify({'success': True, 'message': 'Estacion actualizada correctamente'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al procesar la solicitud', 'error': str(e)}), 500