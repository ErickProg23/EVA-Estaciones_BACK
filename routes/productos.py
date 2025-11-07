from flask import Blueprint, request, jsonify
from models import db, Producto, Estacion, Usuario
from sqlalchemy import or_

productos_bp = Blueprint('productos', __name__)

@productos_bp.route('/api/getProductos', methods=['GET'])
def get_productos():
    try:
        productos = Producto.query.all()
        data = [
            {
                'id': p.id,
                'nombre': p.nombre,
                'precio': p.precio,
                'estacion_id': p.estacion_id,
                'activo': p.activo
            }
            for p in productos
        ]
        return jsonify({'success': True, 'productos': data}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al obtener productos', 'error': str(e)}), 500

@productos_bp.route('/api/updateProducto/<int:producto_id>', methods=['PUT'])
def update_producto(producto_id):
    try:
        producto = Producto.query.get(producto_id)
        if not producto:
            return jsonify({'success': False, 'message': 'Producto no encontrado'}), 404

        data = request.get_json()
        nombre = data.get('nombre')
        precio = data.get('precio')
        estacion_id = data.get('estacion_id')
        activo = data.get('activo', True)

        if nombre is None or precio is None or estacion_id is None:
            return jsonify({'success': False, 'message': 'Faltan datos: nombre, precio o estacion_id'}), 400

        # Validar precio numérico
        try:
            precio = float(precio)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'Precio inválido'}), 400

        # Validar estación existente (opcional pero recomendado)
        estacion = Estacion.query.get(estacion_id)
        if not estacion:
            return jsonify({'success': False, 'message': 'Estación no encontrada'}), 404

        producto.nombre = nombre
        producto.precio = precio
        producto.estacion_id = estacion_id
        producto.activo = bool(activo)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Producto actualizado correctamente',
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'precio': producto.precio,
                'estacion_id': producto.estacion_id,
                'activo': producto.activo
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al actualizar el producto', 'error': str(e)}), 500

@productos_bp.route('/api/getProductosByUsuarioEstacion/<int:usuario_id>', methods=['GET'])
def get_productos_by_usuario_estacion(usuario_id):
    try:
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
        if not usuario.activo:
            return jsonify({'success': False, 'message': 'Usuario inactivo'}), 400
        if not usuario.estacion_id:
            return jsonify({'success': False, 'message': 'Usuario no tiene estación asignada'}), 400

        # Incluye productos de la estación del usuario y compartidos (estacion_id = 1)
        productos = Producto.query.filter(
            or_(Producto.estacion_id == usuario.estacion_id, Producto.estacion_id == 1),
            Producto.activo == True
        ).all()

        data = [{
            'id': p.id,
            'nombre': p.nombre,
            'precio': p.precio,
            'estacion_id': p.estacion_id,
            'activo': p.activo
        } for p in productos]

        return jsonify({'success': True, 'productos': data}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al obtener productos de la estación', 'error': str(e)}), 500

@productos_bp.route('/api/updatePrecioProducto/<int:producto_id>', methods=['PUT'])
def update_precio_producto(producto_id):
    try:
        data = request.get_json() or {}
        precio = data.get('precio')
        usuario_id = data.get('usuario_id')

        if usuario_id is None:
            return jsonify({'success': False, 'message': 'Falta usuario_id'}), 400

        usuario = Usuario.query.get(usuario_id)
        if not usuario or not usuario.activo:
            return jsonify({'success': False, 'message': 'Usuario no encontrado o inactivo'}), 404

        producto = Producto.query.get(producto_id)
        if not producto:
            return jsonify({'success': False, 'message': 'Producto no encontrado'}), 404

        # Validar acceso: misma estación o producto compartido (estacion_id = 1)
        if producto.estacion_id != usuario.estacion_id and producto.estacion_id != 1:
            return jsonify({'success': False, 'message': 'No tienes acceso para editar este producto'}), 403

        if precio is None:
            return jsonify({'success': False, 'message': 'Falta precio'}), 400

        try:
            precio = float(precio)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'Precio inválido'}), 400

        producto.precio = precio
        db.session.commit()

        return jsonify({'success': True, 'message': 'Precio actualizado correctamente', 'producto_id': producto.id, 'precio': producto.precio}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al actualizar precio del producto', 'error': str(e)}), 500