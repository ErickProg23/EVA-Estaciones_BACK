from flask import Blueprint, request, jsonify
from models import db, Estacion
import jwt, datetime

estacion_bp = Blueprint('estacion', __name__)

@estacion_bp.route('/api/getEstaciones', methods=['GET'])
def getEstaciones():
    try:
        estaciones = Estacion.query.all()
        estaciones_data = []
        for e in estaciones:
            estaciones_data.append({
                'id': e.id,
                'nombre': e.nombre,
                'activo': e.activo
            })
        return jsonify(estaciones_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@estacion_bp.route('/api/createEstacion', methods=['POST'])
def createEstacion():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        activo = data.get('activo', True)
        fecha_creacion = datetime.datetime.now()
        if not nombre:
            return jsonify({'success': False, 'message': 'El nombre de la estacion es obligatorio'}), 400
        estacion = Estacion(nombre=nombre, activo=activo, fecha_creacion=fecha_creacion)
        db.session.add(estacion)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Estacion creada correctamente', 'estacion_id': estacion.id})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al procesar la solicitud', 'error': str(e)}), 500

@estacion_bp.route('/api/deleteEstacion/<int:estacion_id>', methods=['PUT'])
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