from flask import Blueprint, request, jsonify
from models import db, Usuario, Empleado, Puesto, Estacion
from collections import defaultdict

evaluacion_bp = Blueprint('evaluacion', __name__)

@evaluacion_bp.route('/api/getEmpleadosByUsuarioEstacion/<int:usuario_id>', methods=['GET'])
def get_empleados_by_usuario_estacion(usuario_id):
    try:
        # 1. Verificar que el usuario existe
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({
                'success': False, 
                'message': 'Usuario no encontrado'
            }), 404
        
        # 2. Verificar que el usuario esté activo
        if not usuario.activo:
            return jsonify({
                'success': False, 
                'message': 'Usuario inactivo'
            }), 400
        
        # 3. Verificar que el usuario tenga una estación asignada
        if not usuario.estacion_id:
            return jsonify({
                'success': False, 
                'message': 'Usuario no tiene estación asignada'
            }), 400
        
        # 4. Obtener información de la estación del usuario
        estacion = Estacion.query.get(usuario.estacion_id)
        if not estacion:
            return jsonify({
                'success': False, 
                'message': 'Estación no encontrada'
            }), 404
        
        # 5. Buscar todos los empleados activos de esa estación
        empleados = Empleado.query.filter_by(
            estacion_id=usuario.estacion_id,
            activo=True
        ).all()
        
        # 6. Agrupar empleados por puesto
        empleados_por_puesto = defaultdict(list)
        
        for empleado in empleados:
            # Obtener información del puesto
            puesto_info = {
                'puesto_id': empleado.puesto_id,
                'puesto_nombre': empleado.puesto.nombre if empleado.puesto else 'Sin puesto asignado'
            }
            
            # Información del empleado
            empleado_info = {
                'id': empleado.id,
                'nombre': empleado.nombre,
                'num_empleado': empleado.num_empleado,  
                'activo': empleado.activo
            }
            
            # Agrupar por puesto_id (usar 0 si no tiene puesto)
            puesto_key = empleado.puesto_id if empleado.puesto_id else 0
            
            # Si es el primer empleado de este puesto, agregar info del puesto
            if not empleados_por_puesto[puesto_key]:
                empleados_por_puesto[puesto_key] = {
                    'puesto_id': puesto_info['puesto_id'],
                    'puesto_nombre': puesto_info['puesto_nombre'],
                    'empleados': []
                }
            
            empleados_por_puesto[puesto_key]['empleados'].append(empleado_info)
        
        # 7. Convertir defaultdict a lista para el response
        puestos_con_empleados = list(empleados_por_puesto.values())
        
        # 8. Ordenar por nombre de puesto
        puestos_con_empleados.sort(key=lambda x: x['puesto_nombre'])
        
        # 9. Preparar response completo
        response_data = {
            'success': True,
            'usuario': {
                'id': usuario.id,
                'nombre': usuario.nombre,
                'usuario': usuario.usuario
            },
            'estacion': {
                'id': estacion.id,
                'nombre': estacion.nombre
            },
            'total_empleados': len(empleados),
            'total_puestos': len(puestos_con_empleados),
            'puestos_con_empleados': puestos_con_empleados
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': 'Error al procesar la solicitud', 
            'error': str(e)
        }), 500

@evaluacion_bp.route('/api/getEmpleadosByUsuarioEstacionResumen/<int:usuario_id>', methods=['GET'])
def get_empleados_by_usuario_estacion_resumen(usuario_id):
    """Versión resumida que solo devuelve estadísticas"""
    try:
        # Verificar usuario
        usuario = Usuario.query.get(usuario_id)
        if not usuario or not usuario.activo:
            return jsonify({
                'success': False, 
                'message': 'Usuario no encontrado o inactivo'
            }), 404
        
        if not usuario.estacion_id:
            return jsonify({
                'success': False, 
                'message': 'Usuario no tiene estación asignada'
            }), 400
        
        # Contar empleados por puesto usando JOIN
        empleados_por_puesto = db.session.query(
            Puesto.id.label('puesto_id'),
            Puesto.nombre.label('puesto_nombre'),
            db.func.count(Empleado.id).label('total_empleados')
        ).join(
            Empleado, Puesto.id == Empleado.puesto_id
        ).filter(
            Empleado.estacion_id == usuario.estacion_id,
            Empleado.activo == True
        ).group_by(
            Puesto.id, Puesto.nombre
        ).all()
        
        # Contar empleados sin puesto asignado
        empleados_sin_puesto = Empleado.query.filter_by(
            estacion_id=usuario.estacion_id,
            puesto_id=None,
            activo=True
        ).count()
        
        resumen_puestos = []
        total_empleados = 0
        
        for puesto in empleados_por_puesto:
            resumen_puestos.append({
                'puesto_id': puesto.puesto_id,
                'puesto_nombre': puesto.puesto_nombre,
                'total_empleados': puesto.total_empleados
            })
            total_empleados += puesto.total_empleados
        
        # Agregar empleados sin puesto si existen
        if empleados_sin_puesto > 0:
            resumen_puestos.append({
                'puesto_id': None,
                'puesto_nombre': 'Sin puesto asignado',
                'total_empleados': empleados_sin_puesto
            })
            total_empleados += empleados_sin_puesto
        
        return jsonify({
            'success': True,
            'usuario_id': usuario_id,
            'estacion_id': usuario.estacion_id,
            'estacion_nombre': usuario.estacion.nombre,
            'total_empleados': total_empleados,
            'total_puestos': len(resumen_puestos),
            'resumen_por_puestos': resumen_puestos
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': 'Error al procesar la solicitud', 
            'error': str(e)
        }), 500