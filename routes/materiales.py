from flask import Blueprint, request, jsonify
from models import db, Material, EstacionMaterial, Estacion

materiales_bp = Blueprint('materiales', __name__)

@materiales_bp.route('/api/materiales/obtener', methods=['GET'])
def get_materiales():
    try:
        materiales = Material.query.filter_by(activo=True).all()
        return jsonify([{
            'id': m.id,
            'nombre': m.nombre,
            'unidad': m.unidad
        } for m in materiales]), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@materiales_bp.route('/api/materiales/crear', methods=['POST'])
def create_material():
    try:
        data = request.json
        nombre = data.get('nombre')
        unidad = data.get('unidad')

        if not nombre or not unidad:
            return jsonify({'message': 'Nombre y unidad son requeridos'}), 400

        nuevo_material = Material(nombre=nombre, unidad=unidad)
        db.session.add(nuevo_material)
        db.session.commit()

        return jsonify({'message': 'Material creado exitosamente', 'id': nuevo_material.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@materiales_bp.route('/api/materiales/estacion/<int:estacion_id>', methods=['GET'])
def get_materiales_estacion(estacion_id):
    try:
        # Obtener materiales asignados a la estación
        asignaciones = EstacionMaterial.query.filter_by(estacion_id=estacion_id, activo=True).all()
        
        resultado = []
        for asignacion in asignaciones:
            material = asignacion.material
            resultado.append({
                'asignacion_id': asignacion.id,
                'material_id': material.id,
                'nombre': material.nombre,
                'unidad': material.unidad
            })
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@materiales_bp.route('/api/materiales/asignar', methods=['POST'])
def asignar_material():
    try:
        data = request.json
        estacion_id = data.get('estacion_id')
        material_id = data.get('material_id')

        if not estacion_id or not material_id:
            return jsonify({'message': 'Estacion ID y Material ID son requeridos'}), 400
        
        # Verificar si ya existe
        existente = EstacionMaterial.query.filter_by(estacion_id=estacion_id, material_id=material_id).first()
        
        if existente:
            if not existente.activo:
                existente.activo = True
                db.session.commit()
                return jsonify({'message': 'Material reactivado en la estación'}), 200
            return jsonify({'message': 'El material ya está asignado a esta estación'}), 400

        nueva_asignacion = EstacionMaterial(estacion_id=estacion_id, material_id=material_id)
        db.session.add(nueva_asignacion)
        db.session.commit()

        return jsonify({'message': 'Material asignado correctamente'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@materiales_bp.route('/api/materiales/desasignar', methods=['POST'])
def desasignar_material():
    try:
        data = request.json
        estacion_id = data.get('estacion_id')
        material_id = data.get('material_id')
        
        if not estacion_id or not material_id:
            return jsonify({'message': 'Estacion ID y Material ID son requeridos'}), 400

        asignacion = EstacionMaterial.query.filter_by(estacion_id=estacion_id, material_id=material_id).first()
        
        if asignacion:
            asignacion.activo = False
            db.session.commit()
            return jsonify({'message': 'Material desasignado correctamente'}), 200
        
        return jsonify({'message': 'Asignación no encontrada'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500