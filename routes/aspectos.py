from flask import Blueprint, request, jsonify
from models import Aspecto, db, Puesto, Estacion, Empleado, Rol, Usuario, PuestoAspecto
from sqlalchemy import and_
import jwt, datetime

aspecto_bp = Blueprint('aspecto', __name__)

@aspecto_bp.route('/api/getAspectos', methods=['GET'])
def get_aspectos():
    try:
        aspectos = Aspecto.query.all()
        aspectos_list = []
        for aspecto in aspectos:
            aspectos_list.append({
                'id': aspecto.id,
                'nombre': aspecto.nombre,
                # Removido 'tipo'
                'activo': aspecto.activo
            })
        return jsonify(aspectos_list), 200
    except Exception as e:
        return jsonify({'message': 'Error al obtener los aspectos', 'error': str(e)}), 500

@aspecto_bp.route('/api/getAspectosByPuesto/<int:puesto_id>', methods=['GET'])
def get_aspectos_by_puesto(puesto_id):
    try:
        aspectos_puesto = db.session.query(Aspecto, PuestoAspecto).outerjoin(
            PuestoAspecto, 
            and_(Aspecto.id == PuestoAspecto.aspecto_id, PuestoAspecto.puesto_id == puesto_id)
        ).filter(Aspecto.activo == True).all()
        
        aspectos_list = []
        for aspecto, puesto_aspecto in aspectos_puesto:
            aspectos_list.append({
                'id': aspecto.id,
                'nombre': aspecto.nombre,
                # Removido 'tipo'
                'peso': puesto_aspecto.peso if puesto_aspecto else 0,
                'activo': aspecto.activo,
                'tiene_peso_asignado': puesto_aspecto is not None
            })
        return jsonify(aspectos_list), 200
    except Exception as e:
        return jsonify({'message': 'Error al obtener los aspectos del puesto', 'error': str(e)}), 500

@aspecto_bp.route('/api/newAspecto', methods=['POST'])
def newAspecto():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        # Removido tipo
        activo = data.get('activo', True)
        
        if not nombre:
            return jsonify({'message': 'Falta el nombre del aspecto'}), 400
            
        # Verificar que no exista un aspecto con el mismo nombre
        aspecto_existente = Aspecto.query.filter_by(nombre=nombre).first()
        if aspecto_existente:
            return jsonify({'message': 'Ya existe un aspecto con ese nombre'}), 400
            
        # Crear aspecto sin tipo
        aspecto = Aspecto(nombre=nombre, activo=activo)
        db.session.add(aspecto)
        db.session.commit()
        return jsonify({'message': 'Aspecto creado exitosamente'}), 201
    except Exception as e:
        return jsonify({'message': 'Error al crear el aspecto', 'error': str(e)}), 500

@aspecto_bp.route('/api/asignarAspectoAPuesto', methods=['POST'])
def asignar_aspecto_a_puesto():
    try:
        data = request.get_json()
        puesto_id = data.get('puesto_id')
        aspecto_id = data.get('aspecto_id')
        peso = data.get('peso')
        
        if not all([puesto_id, aspecto_id, peso]):
            return jsonify({'message': 'Faltan datos'}), 400
            
        # Verificar que no exista ya la relación
        existe = PuestoAspecto.query.filter_by(
            puesto_id=puesto_id, 
            aspecto_id=aspecto_id
        ).first()
        
        if existe:
            return jsonify({'message': 'El aspecto ya está asignado a este puesto'}), 400
            
        puesto_aspecto = PuestoAspecto(puesto_id=puesto_id, aspecto_id=aspecto_id, peso=peso)
        db.session.add(puesto_aspecto)
        db.session.commit()
        return jsonify({'message': 'Aspecto asignado al puesto exitosamente'}), 201
    except Exception as e:
        return jsonify({'message': 'Error al asignar aspecto al puesto', 'error': str(e)}), 500

@aspecto_bp.route('/api/updateAspecto', methods=['PUT'])
def updateAspecto():
    try:
        data = request.get_json()
        id = data.get('id')
        nombre = data.get('nombre')
        # Removido tipo
        activo = data.get('activo')
        
        if not all([id, nombre, activo is not None]):
            return jsonify({'message': 'Faltan datos'}), 400
            
        aspecto = Aspecto.query.get(id)
        if not aspecto:
            return jsonify({'message': 'Aspecto no encontrado'}), 404
            
        # Verificar que no exista otro aspecto con el mismo nombre (excluyendo el actual)
        aspecto_existente = Aspecto.query.filter(Aspecto.nombre == nombre, Aspecto.id != id).first()
        if aspecto_existente:
            return jsonify({'message': 'Ya existe otro aspecto con ese nombre'}), 400
            
        aspecto.nombre = nombre
        # Removido aspecto.tipo
        aspecto.activo = activo
        db.session.commit()
        return jsonify({'message': 'Aspecto actualizado exitosamente'}), 200
    except Exception as e:
        return jsonify({'message': 'Error al actualizar el aspecto', 'error': str(e)}), 500

@aspecto_bp.route('/api/updatePesoAspectoPuesto', methods=['PUT'])
def update_peso_aspecto_puesto():
    try:
        data = request.get_json()
        puesto_id = data.get('puesto_id')
        aspecto_id = data.get('aspecto_id')
        nuevo_peso = data.get('peso')
        
        if not all([puesto_id, aspecto_id, nuevo_peso is not None]):
            return jsonify({'success': False, 'message': 'Faltan datos'}), 400
            
        puesto_aspecto = PuestoAspecto.query.filter_by(
            puesto_id=puesto_id,
            aspecto_id=aspecto_id
        ).first()
        
        if not puesto_aspecto:
            # Crear la relación si no existe
            puesto_aspecto = PuestoAspecto(
                puesto_id=puesto_id,
                aspecto_id=aspecto_id,
                peso=nuevo_peso
            )
            db.session.add(puesto_aspecto)
            message = 'Peso creado exitosamente'
        else:
            # Actualizar si ya existe
            puesto_aspecto.peso = nuevo_peso
            message = 'Peso actualizado exitosamente'
            
        db.session.commit()
        return jsonify({'success': True, 'message': message}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error al procesar el peso', 'error': str(e)}), 500
