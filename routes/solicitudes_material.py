from flask import Blueprint, request, jsonify
from models import db, SolicitudMaterial, EstacionMaterial, Material, Usuario, Estacion
from datetime import datetime

solicitudes_bp = Blueprint('solicitudes_material', __name__)

@solicitudes_bp.route('/api/solicitudes/crear', methods=['POST'])
def create_solicitud():
    try:
        data = request.json
        material_id = data.get('material_id')
        usuario_id = data.get('usuario_id')
        cantidad = data.get('cantidad')
        comentario = data.get('comentario')

        if not material_id or not usuario_id or not cantidad:
            return jsonify({'message': 'Faltan datos requeridos (material_id, usuario_id, cantidad)'}), 400

        nueva_solicitud = SolicitudMaterial(
            material_id=material_id,
            usuario_id=usuario_id,
            cantidad=cantidad,
            comentario=comentario
        )
        db.session.add(nueva_solicitud)
        db.session.commit()

        return jsonify({'message': 'Solicitud creada correctamente', 'id': nueva_solicitud.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@solicitudes_bp.route('/api/solicitudes', methods=['GET'])
def get_solicitudes():
    try:
        estacion_id = request.args.get('estacion_id')
        usuario_id = request.args.get('usuario_id')
        estado = request.args.get('estado')
        
        query = SolicitudMaterial.query.join(EstacionMaterial).join(Material).join(Usuario).join(Estacion)

        if estacion_id:
            query = query.filter(EstacionMaterial.estacion_id == estacion_id)
        
        if usuario_id:
            query = query.filter(SolicitudMaterial.usuario_id == usuario_id)
            
        if estado:
            query = query.filter(SolicitudMaterial.estado == estado)
            
        solicitudes = query.order_by(SolicitudMaterial.fecha_solicitada.desc()).all()
        
        resultado = []
        for s in solicitudes:
            resultado.append({
                'id': s.id,
                'estacion_material_id': s.estacion_material_id,
                'material_nombre': s.estacion_material.material.nombre,
                'unidad': s.estacion_material.material.unidad,
                'estacion_nombre': s.estacion_material.estacion.nombre,
                'usuario_id': s.usuario_id,
                'usuario_nombre': s.usuario.nombre,
                'cantidad': float(s.cantidad),
                'fecha_solicitada': s.fecha_solicitada.isoformat(),
                'estado': s.estado,
                'comentario': s.comentario
            })
            
        return jsonify({'solicitudes': resultado}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@solicitudes_bp.route('/api/solicitudes/<int:id>/estado', methods=['PUT'])
def update_solicitud_status(id):
    try:
        data = request.json
        estado = data.get('estado')
        comentarios = data.get('comentarios')

        if not estado:
            return jsonify({'message': 'El estado es requerido'}), 400

        solicitud = SolicitudMaterial.query.get(id)
        if not solicitud:
            return jsonify({'message': 'Solicitud no encontrada'}), 404

        solicitud.estado = estado
        if comentarios:
            if solicitud.comentario:
                solicitud.comentario += f" | {comentarios}"
            else:
                solicitud.comentario = comentarios
        
        db.session.commit()

        return jsonify({'message': 'Estado actualizado correctamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500