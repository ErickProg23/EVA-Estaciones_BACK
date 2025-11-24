from flask import Blueprint, request, jsonify
from models import db, Bomba, Estacion, Usuario, Producto
from sqlalchemy import or_

bombas_bp = Blueprint('bombas', __name__)

@bombas_bp.route('/api/getBombas', methods=['GET'])
def get_bombas():
    try:
        bombas = Bomba.query.all()
        estacion_ids = {b.estacion_id for b in bombas if b.estacion_id}
        producto_ids = {b.producto_id for b in bombas if b.producto_id}
        estaciones = {e.id: {'id': e.id, 'nombre': e.nombre} for e in Estacion.query.filter(Estacion.id.in_(estacion_ids)).all()} if estacion_ids else {}
        productos = {p.id: {'id': p.id, 'nombre': p.nombre, 'precio': p.precio} for p in Producto.query.filter(Producto.id.in_(producto_ids)).all()} if producto_ids else {}
        data = [{'id': b.id, 'numero_bomba': b.numero_bomba, 'estacion_id': b.estacion_id, 'producto_id': b.producto_id, 'activo': b.activo, 'estacion': estaciones.get(b.estacion_id), 'producto': productos.get(b.producto_id)} for b in bombas]
        return jsonify({'success': True, 'bombas': data}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al obtener bombas', 'error': str(e)}), 500

@bombas_bp.route('/api/newBomba', methods=['POST'])
def new_bomba():
    try:
        data = request.get_json() or {}
        numero_bomba = data.get('numero_bomba')
        estacion_id = data.get('estacion_id')
        producto_id = data.get('producto_id')
        activo = data.get('activo', True)
        if not numero_bomba or not estacion_id or not producto_id:
            return jsonify({'success': False, 'message': 'Faltan datos: numero_bomba, estacion_id o producto_id'}), 400
        estacion = Estacion.query.get(estacion_id)
        if not estacion:
            return jsonify({'success': False, 'message': 'Estación no encontrada'}), 404
        producto = Producto.query.get(producto_id)
        if not producto:
            return jsonify({'success': False, 'message': 'Producto no encontrado'}), 404
        bomba = Bomba(numero_bomba=numero_bomba, estacion_id=estacion_id, producto_id=producto_id, activo=bool(activo))
        db.session.add(bomba)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Bomba creada correctamente', 'bomba': {'id': bomba.id, 'numero_bomba': bomba.numero_bomba, 'estacion_id': bomba.estacion_id, 'producto_id': bomba.producto_id, 'activo': bomba.activo, 'estacion': {'id': estacion.id, 'nombre': estacion.nombre}, 'producto': {'id': producto.id, 'nombre': producto.nombre, 'precio': producto.precio}}}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al crear bomba', 'error': str(e)}), 500

@bombas_bp.route('/api/updateBomba/<int:bomba_id>', methods=['PUT'])
def update_bomba(bomba_id):
    try:
        bomba = Bomba.query.get(bomba_id)
        if not bomba:
            return jsonify({'success': False, 'message': 'Bomba no encontrada'}), 404
        data = request.get_json() or {}
        numero_bomba = data.get('numero_bomba')
        estacion_id = data.get('estacion_id')
        producto_id = data.get('producto_id')
        activo = data.get('activo', True)
        if not numero_bomba or not estacion_id or not producto_id:
            return jsonify({'success': False, 'message': 'Faltan datos: numero_bomba, estacion_id o producto_id'}), 400
        estacion = Estacion.query.get(estacion_id)
        if not estacion:
            return jsonify({'success': False, 'message': 'Estación no encontrada'}), 404
        producto = Producto.query.get(producto_id)
        if not producto:
            return jsonify({'success': False, 'message': 'Producto no encontrado'}), 404
        bomba.numero_bomba = numero_bomba
        bomba.estacion_id = estacion_id
        bomba.producto_id = producto_id
        bomba.activo = bool(activo)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Bomba actualizada correctamente', 'bomba': {'id': bomba.id, 'numero_bomba': bomba.numero_bomba, 'estacion_id': bomba.estacion_id, 'producto_id': bomba.producto_id, 'activo': bomba.activo, 'estacion': {'id': estacion.id, 'nombre': estacion.nombre}, 'producto': {'id': producto.id, 'nombre': producto.nombre, 'precio': producto.precio}}}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al actualizar bomba', 'error': str(e)}), 500

@bombas_bp.route('/api/deleteBomba/<int:bomba_id>', methods=['DELETE'])
def delete_bomba(bomba_id):
    try:
        bomba = Bomba.query.get(bomba_id)
        if not bomba:
            return jsonify({'success': False, 'message': 'Bomba no encontrada'}), 404
        bomba.activo = False
        db.session.commit()
        est = Estacion.query.get(bomba.estacion_id)
        prod = Producto.query.get(bomba.producto_id)
        return jsonify({'success': True, 'message': 'Bomba eliminada correctamente', 'bomba': {'id': bomba.id, 'numero_bomba': bomba.numero_bomba, 'estacion_id': bomba.estacion_id, 'producto_id': bomba.producto_id, 'activo': bomba.activo, 'estacion': {'id': est.id, 'nombre': est.nombre} if est else None, 'producto': {'id': prod.id, 'nombre': prod.nombre, 'precio': prod.precio} if prod else None}}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al eliminar bomba', 'error': str(e)}), 500

@bombas_bp.route('/api/getBombasByUsuarioEstacion/<int:usuario_id>', methods=['GET'])
def get_bombas_by_usuario_estacion(usuario_id):
    try:
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
        if not usuario.activo:
            return jsonify({'success': False, 'message': 'Usuario inactivo'}), 400
        if not usuario.estacion_id:
            return jsonify({'success': False, 'message': 'Usuario no tiene estación asignada'}), 400
        bombas = Bomba.query.filter(or_(Bomba.estacion_id == usuario.estacion_id, Bomba.estacion_id == 1), Bomba.activo == True).all()
        estacion_ids = {b.estacion_id for b in bombas if b.estacion_id}
        producto_ids = {b.producto_id for b in bombas if b.producto_id}
        estaciones = {e.id: {'id': e.id, 'nombre': e.nombre} for e in Estacion.query.filter(Estacion.id.in_(estacion_ids)).all()} if estacion_ids else {}
        productos = {p.id: {'id': p.id, 'nombre': p.nombre, 'precio': p.precio} for p in Producto.query.filter(Producto.id.in_(producto_ids)).all()} if producto_ids else {}
        data = [{'id': b.id, 'numero_bomba': b.numero_bomba, 'estacion_id': b.estacion_id, 'producto_id': b.producto_id, 'activo': b.activo, 'estacion': estaciones.get(b.estacion_id), 'producto': productos.get(b.producto_id)} for b in bombas]
        return jsonify({'success': True, 'bombas': data}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al obtener bombas de la estación', 'error': str(e)}), 500