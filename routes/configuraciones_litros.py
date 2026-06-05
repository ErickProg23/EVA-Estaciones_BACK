from flask import Blueprint, request, jsonify
from models import db, ConfiguracionLitros, Usuario, Estacion, Producto
from datetime import datetime, timedelta

configuraciones_litros_bp = Blueprint('configuraciones_litros', __name__)

@configuraciones_litros_bp.route('/estacion/<int:estacion_id>', methods=['GET'])
def obtener_configuraciones_litros_estacion(estacion_id):
    estacion = Estacion.query.get(estacion_id)
    if not estacion:
        return jsonify({'error': 'Estación no encontrada'}), 404

    configuraciones = ConfiguracionLitros.query.filter_by(id_estacion=estacion_id).all()

    return jsonify({
        'estacion': {
            'id': estacion.id,
            'nombre': estacion.nombre
        },
        'configuraciones': [{
            'estacion_id': configur.id_estacion,
            'producto': configur.producto,
            'producto_nombre': configur.nombre,
            'limite_max_litros': float(configur.limite_max_litros) if configur.limite_max_litros is not None else None
        } for configur in configuraciones]
    }), 200

@configuraciones_litros_bp.route('/usuario/<int:usuario_id>', methods=['GET'])
def obtener_configuraciones_litros_usuario(usuario_id):
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    if not usuario.estacion_id:
        return jsonify({'error': 'Usuario no tiene estación asignada'}), 400

    estacion = Estacion.query.get(usuario.estacion_id)
    if not estacion:
        return jsonify({'error': 'Estación no encontrada'}), 404

    configuraciones = ConfiguracionLitros.query.filter_by(id_estacion=usuario.estacion_id).all()

    productos = Producto.query.filter_by(estacion_id=usuario.estacion_id).all()
    

    return jsonify({
        'usuario_id': usuario.id,
        'estacion': {
            'id': estacion.id,
            'nombre': estacion.nombre
        },
        'productos':
        [{
            'id': p.id,
            'nombre': p.nombre,
        } for p in productos],
        'configuraciones': [{
            'estacion_id': configur.id_estacion,
            'producto': configur.producto,
            'limite_max_litros': float(configur.limite_max_litros) if configur.limite_max_litros is not None else None
        } for configur in configuraciones]
    }), 200
