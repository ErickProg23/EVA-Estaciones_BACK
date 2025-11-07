from flask import Blueprint, request, jsonify
from models import db, Usuario, Empleado, Puesto, Estacion, Aspecto, PuestoAspecto, Evaluacion, Detalle_Evaluacion
from collections import defaultdict
from datetime import datetime

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

@evaluacion_bp.route('/api/finalizarEvaluacionPuesto', methods=['POST'])
def finalizar_evaluacion_puesto():
    try:
        data = request.get_json()
        
        # Validar datos requeridos (sin fecha_finalizacion: se usa la del servidor)
        usuario_id = data.get('usuario_id')
        puesto_id = data.get('puesto_id')
        evaluaciones = data.get('evaluaciones', {})
        comentarios = data.get('comentarios', {})
        es_borrador = data.get('es_borrador', False)
        faltas = data.get('faltas', 0)
        incapacidad = data.get('incapacidad', 0)
        
        if not all([usuario_id, puesto_id, evaluaciones]):
            return jsonify({
                'success': False,
                'message': 'Faltan datos requeridos: usuario_id, puesto_id, evaluaciones'
            }), 400
        
        if es_borrador:
            return jsonify({
                'success': False,
                'message': 'No se pueden finalizar evaluaciones marcadas como borrador'
            }), 400
        
        # Establecer fecha de evaluación en backend (hora del servidor)
        fecha_evaluacion = datetime.now()
        mes = fecha_evaluacion.month
        anio = fecha_evaluacion.year
        
        # Verificar que el puesto existe
        puesto = Puesto.query.get(puesto_id)
        if not puesto or not puesto.activo:
            return jsonify({
                'success': False,
                'message': 'Puesto no encontrado o inactivo'
            }), 404
        
        # Detectar formato: evaluación para un solo empleado con lista de aspectos (tal cual se envía desde front)
        empleado_id_global = data.get('empleado_id')
        es_lista_de_aspectos_un_empleado = (
            isinstance(evaluaciones, list) and
            len(evaluaciones) > 0 and
            isinstance(evaluaciones[0], dict) and
            ('aspecto_id' in evaluaciones[0]) and
            ('calificacion' in evaluaciones[0])
        )
        
        if es_lista_de_aspectos_un_empleado and empleado_id_global is not None:
            # Usar todo tal cual viene del front: lista de aspectos con calificacion y peso
            empleado_id = int(empleado_id_global)
            
            # Verificar que el empleado existe y pertenece al puesto
            empleado = Empleado.query.filter_by(
                id=empleado_id,
                puesto_id=puesto_id,
                activo=True
            ).first()
            if not empleado:
                return jsonify({
                    'success': False,
                    'message': f'Empleado {empleado_id} no encontrado o no pertenece al puesto especificado'
                }), 404
            
            # Verificar que no existe evaluación para este empleado en el mes/año
            evaluacion_existente = Evaluacion.query.filter_by(
                empleado_id=empleado_id,
                mes=mes,
                anio=anio
            ).first()
            if evaluacion_existente:
                return jsonify({
                    'success': False,
                    'message': f'Ya existe una evaluación para el empleado {empleado.nombre} en {mes}/{anio}'
                }), 409
            
            # Calcular con los datos tal cual vienen del front
            suma_calificaciones_ponderadas = 0.0
            suma_pesos = 0.0
            aspectos_evaluados = []
            
            for item in evaluaciones:
                try:
                    aspecto_id = int(item.get('aspecto_id'))
                    cal = float(item.get('calificacion'))
                    peso = float(item.get('peso'))
                except Exception:
                    return jsonify({
                        'success': False,
                        'message': 'Formato inválido en evaluaciones: asegúrate de enviar aspecto_id, calificacion y peso numéricos'
                    }), 400
                
                # Escala normalizada a 1–5
                if not (0 <= cal <= 5):
                    return jsonify({
                        'success': False,
                        'message': f'Calificación inválida para empleado {empleado.nombre}, aspecto {aspecto_id}. Escala permitida 1–5.'
                    }), 400
                if peso <= 0:
                    return jsonify({
                        'success': False,
                        'message': f'Peso inválido para aspecto {aspecto_id}. Debe ser mayor que 0.'
                    }), 400
                
                suma_calificaciones_ponderadas += cal * peso
                suma_pesos += peso
                aspectos_evaluados.append({
                    'aspecto_id': aspecto_id,
                    'calificacion': cal
                })
            
            if suma_pesos == 0:
                return jsonify({
                    'success': False,
                    'message': 'Suma de pesos es 0. Verifica los pesos enviados.'
                }), 400
            
            calificacion_final = suma_calificaciones_ponderadas / suma_pesos
            porcentaje_final = (calificacion_final / 5) * 100
            
            # Comentario como string directo
            comentario_empleado = comentarios if isinstance(comentarios, str) else ''
            
            # Crear evaluación
            nueva_evaluacion = Evaluacion(
                empleado_id=empleado_id,
                mes=mes,
                anio=anio,
                fecha_evaluacion=fecha_evaluacion,
                calificacion_final=round(calificacion_final, 2),
                porcentaje_final=round(porcentaje_final, 2),
                comentario=comentario_empleado,
                faltas=faltas,
                incapacidad=incapacidad
            )
            db.session.add(nueva_evaluacion)
            db.session.flush()
            
            # Crear detalles de evaluación (calificación por aspecto)
            for aspecto_eval in aspectos_evaluados:
                detalle = Detalle_Evaluacion(
                    evaluacion_id=nueva_evaluacion.id,
                    aspecto_id=aspecto_eval['aspecto_id'],
                    calificacion=aspecto_eval['calificacion']
                )
                db.session.add(detalle)
            
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Se guardó 1 evaluación exitosamente',
                'evaluaciones': [{
                    'empleado_id': empleado_id,
                    'empleado_nombre': empleado.nombre,
                    'calificacion_final': nueva_evaluacion.calificacion_final,
                    'porcentaje_final': nueva_evaluacion.porcentaje_final,
                    'comentario': comentario_empleado,
                    'aspectos_evaluados': len(aspectos_evaluados),
                    'faltas': faltas,
                    'incapacidad': incapacidad
                }],
                'puesto_nombre': puesto.nombre,
                'mes': mes,
                'anio': anio,
                'fecha_evaluacion': fecha_evaluacion.isoformat()
            }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error al procesar las evaluaciones',
            'error': str(e)
        }), 500

@evaluacion_bp.route('/api/getEvaluacionesPuesto/<int:usuario_id>/<int:puesto_id>', methods=['GET'])
def get_evaluaciones_puesto(usuario_id, puesto_id):
    try:
        # Verificar que el usuario existe
        usuario = Usuario.query.get(usuario_id)
        if not usuario or not usuario.activo:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado o inactivo'
            }), 404
        
        # Verificar que el puesto existe
        puesto = Puesto.query.get(puesto_id)
        if not puesto or not puesto.activo:
            return jsonify({
                'success': False,
                'message': 'Puesto no encontrado o inactivo'
            }), 404
        
        # Verificar acceso: el usuario puede acceder si:
        # 1. El puesto pertenece a su estación específica, O
        # 2. El puesto es compartido (estacion_id = 1, "Todas")
        if puesto.estacion_id != usuario.estacion_id and puesto.estacion_id != 1:
            return jsonify({
                'success': False,
                'message': 'No tienes acceso a evaluaciones de este puesto'
            }), 403
        
        # Obtener empleados del puesto que pertenezcan a la estación del usuario
        # Si el puesto es compartido (estacion_id = 1), solo mostrar empleados de la estación del usuario
        empleados_evaluaciones = db.session.query(
            Empleado.id.label('empleado_id'),
            Empleado.nombre.label('empleado_nombre'),
            Evaluacion.id.label('evaluacion_id'),
            Evaluacion.mes,
            Evaluacion.anio,
            Evaluacion.fecha_evaluacion,
            Evaluacion.calificacion_final,
            Evaluacion.porcentaje_final,
            Evaluacion.comentario
        ).outerjoin(
            Evaluacion, Empleado.id == Evaluacion.empleado_id
        ).filter(
            Empleado.puesto_id == puesto_id,
            Empleado.activo == True,
            # Si el puesto es compartido (estacion_id = 1), filtrar por estación del usuario
            # Si el puesto es específico, ya sabemos que coincide con la estación del usuario
            Empleado.estacion_id == usuario.estacion_id if puesto.estacion_id == 1 else True
        ).order_by(
            Empleado.nombre,
            Evaluacion.anio.desc(),
            Evaluacion.mes.desc()
        ).all()
        
        # ... resto del código permanece igual ...
        
        # Organizar datos por empleado
        empleados_data = {}
        
        for row in empleados_evaluaciones:
            empleado_id = row.empleado_id
            
            if empleado_id not in empleados_data:
                empleados_data[empleado_id] = {
                    'empleado_id': empleado_id,
                    'empleado_nombre': row.empleado_nombre,
                    'evaluaciones': []
                }
            
            # Solo agregar evaluación si existe
            if row.evaluacion_id:
                evaluacion_data = {
                    'evaluacion_id': row.evaluacion_id,
                    'mes': row.mes,
                    'anio': row.anio,
                    'fecha_evaluacion': row.fecha_evaluacion.isoformat() if row.fecha_evaluacion else None,
                    'calificacion_final': float(row.calificacion_final) if row.calificacion_final else None,
                    'porcentaje_final': float(row.porcentaje_final) if row.porcentaje_final else None,
                    'comentario': row.comentario or ''
                }
                
                # Obtener detalles de la evaluación (aspectos evaluados)
                detalles = db.session.query(
                    Detalle_Evaluacion.aspecto_id,
                    Detalle_Evaluacion.calificacion,
                    Aspecto.nombre.label('aspecto_nombre')
                ).join(
                    Aspecto, Detalle_Evaluacion.aspecto_id == Aspecto.id
                ).filter(
                    Detalle_Evaluacion.evaluacion_id == row.evaluacion_id
                ).all()
                
                evaluacion_data['aspectos'] = [
                    {
                        'aspecto_id': detalle.aspecto_id,
                        'aspecto_nombre': detalle.aspecto_nombre,
                        'calificacion': detalle.calificacion
                    }
                    for detalle in detalles
                ]
                
                empleados_data[empleado_id]['evaluaciones'].append(evaluacion_data)
        
        # Convertir a lista y calcular estadísticas
        empleados_list = list(empleados_data.values())
        
        # Estadísticas generales
        total_empleados = len(empleados_list)
        empleados_con_evaluaciones = sum(1 for emp in empleados_list if emp['evaluaciones'])
        empleados_sin_evaluaciones = total_empleados - empleados_con_evaluaciones
        
        # Calcular promedio general del puesto (última evaluación de cada empleado)
        calificaciones_recientes = []
        for empleado in empleados_list:
            if empleado['evaluaciones']:
                # La primera evaluación es la más reciente (ordenado desc)
                calificaciones_recientes.append(empleado['evaluaciones'][0]['calificacion_final'])
        
        promedio_puesto = sum(calificaciones_recientes) / len(calificaciones_recientes) if calificaciones_recientes else 0
        
        return jsonify({
            'success': True,
            'data': {
                'puesto': {
                    'id': puesto.id,
                    'nombre': puesto.nombre,
                    'estacion_id': puesto.estacion_id,
                    'es_compartido': puesto.estacion_id == 1  # Indicador para el frontend
                },
                'empleados': empleados_list,
                'estadisticas': {
                    'total_empleados': total_empleados,
                    'empleados_con_evaluaciones': empleados_con_evaluaciones,
                    'empleados_sin_evaluaciones': empleados_sin_evaluaciones,
                    'promedio_puesto': round(promedio_puesto, 2) if promedio_puesto > 0 else None
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error al obtener evaluaciones del puesto',
            'error': str(e)
        }), 500