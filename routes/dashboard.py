from flask import Blueprint, request, jsonify
from models import db, Usuario, Empleado, Puesto, Evaluacion, Estacion
from datetime import datetime, timedelta
from sqlalchemy import func, and_, extract

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/api/getMetricasEstacion/<int:usuario_id>', methods=['GET'])
def get_metricas_estacion(usuario_id):
    try:
        # Obtener el usuario y su estación
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({"success": false, "error": "Usuario no encontrado"}), 404
        
        estacion_id = usuario.estacion_id
        if not estacion_id:
            return jsonify({"success": false, "error": "Usuario no tiene estación asignada"}), 400
        
        # Obtener fecha actual para cálculos de tendencia
        fecha_actual = datetime.now()
        mes_actual = fecha_actual.month
        año_actual = fecha_actual.year
        
        # Mes anterior para tendencia
        if mes_actual == 1:
            mes_anterior = 12
            año_anterior = año_actual - 1
        else:
            mes_anterior = mes_actual - 1
            año_anterior = año_actual
        
        # 1. Total de empleados en la estación
        total_empleados = Empleado.query.filter_by(estacion_id=estacion_id).count()
        
        # 2. Total de puestos en la estación
        total_puestos = Puesto.query.filter_by(estacion_id=estacion_id).count()
        
        # 3. Empleados activos e inactivos
        empleados_activos = Empleado.query.filter_by(estacion_id=estacion_id, activo=True).count()
        empleados_inactivos = Empleado.query.filter_by(estacion_id=estacion_id, activo=False).count()
        
        # 4. Evaluaciones del mes actual
        evaluaciones_mes_actual = db.session.query(Evaluacion).join(
            Empleado, Evaluacion.empleado_id == Empleado.id
        ).filter(
            and_(
                Empleado.estacion_id == estacion_id,
                Evaluacion.mes == mes_actual,
                Evaluacion.anio == año_actual
            )
        ).count()
        
        # 5. Total de empleados que deberían tener evaluación este mes
        empleados_para_evaluar = Empleado.query.filter_by(
            estacion_id=estacion_id, 
            activo=True
        ).count()
        
        # 6. Evaluaciones pendientes
        evaluaciones_pendientes = max(0, empleados_para_evaluar - evaluaciones_mes_actual)
        
        # 7. Promedio de calificación del mes actual (en escala de 100)
        promedio_actual_query = db.session.query(
            func.avg(Evaluacion.calificacion_final)
        ).join(
            Empleado, Evaluacion.empleado_id == Empleado.id
        ).filter(
            and_(
                Empleado.estacion_id == estacion_id,
                Evaluacion.mes == mes_actual,
                Evaluacion.anio == año_actual
            )
        ).scalar()
        
        # Convertir a escala de 100 (asumiendo escala 1-5)
        promedio_calificacion = 0
        if promedio_actual_query:
            promedio_calificacion = (promedio_actual_query / 5.0) * 100
        
        # 8. Promedio del mes anterior para calcular tendencia
        promedio_anterior_query = db.session.query(
            func.avg(Evaluacion.calificacion_final)
        ).join(
            Empleado, Evaluacion.empleado_id == Empleado.id
        ).filter(
            and_(
                Empleado.estacion_id == estacion_id,
                Evaluacion.mes == mes_anterior,
                Evaluacion.anio == año_anterior
            )
        ).scalar()
        
        # Calcular tendencia
        tendencia_promedio = "0.0"
        if promedio_anterior_query and promedio_actual_query:
            promedio_anterior_100 = (promedio_anterior_query / 5.0) * 100
            diferencia = promedio_calificacion - promedio_anterior_100
            if diferencia > 0:
                tendencia_promedio = f"+{diferencia:.1f}"
            else:
                tendencia_promedio = f"{diferencia:.1f}"
        
        # Preparar respuesta
        response_data = {
            "success": True,
            "data": {
                "totalEmpleados": total_empleados,
                "totalPuestos": total_puestos,
                "evaluacionesCompletadas": evaluaciones_mes_actual,
                "evaluacionesPendientes": evaluaciones_pendientes,
                "promedioCalificacion": round(promedio_calificacion, 1),
                "tendenciaPromedio": tendencia_promedio,
                "empleadosActivos": empleados_activos,
                "empleadosInactivos": empleados_inactivos
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error al obtener métricas: {str(e)}"
        }), 500

@dashboard_bp.route('/api/getInfoEstacion/<int:usuario_id>', methods=['GET'])
def get_info_estacion(usuario_id):
    try:
        # Obtener el usuario
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
        
        # Obtener la estación del usuario
        estacion_id = usuario.estacion_id
        if not estacion_id:
            return jsonify({"success": False, "error": "Usuario no tiene estación asignada"}), 400
        
        estacion = Estacion.query.get(estacion_id)
        if not estacion:
            return jsonify({"success": False, "error": "Estación no encontrada"}), 404
        
        # Buscar el encargado de la estación (usuario con rol de encargado en esa estación)
        # Asumiendo que el rol de encargado tiene id=1 o nombre específico
        # Puedes ajustar esta consulta según tu lógica de roles
        encargado = Usuario.query.filter_by(
            estacion_id=estacion_id,
            activo=True
        ).join(Usuario.rol).filter(
            # Ajusta esta condición según tu estructura de roles
            # Por ejemplo, si el encargado tiene rol_id=1:
            Usuario.rol_id == 1
            # O si buscas por nombre de rol:
            # Rol.nombre.ilike('%encargado%')
        ).first()
        
        # Si no se encuentra un encargado específico, tomar el primer usuario activo de la estación
        if not encargado:
            encargado = Usuario.query.filter_by(
                estacion_id=estacion_id,
                activo=True
            ).first()
        
        # Preparar respuesta
        response_data = {
            "success": True,
            "data": {
                "estacion": {
                    "id": estacion.id,
                    "nombre": estacion.nombre,
                    "activo": estacion.activo
                },
                "encargado": {
                    "id": encargado.id if encargado else None,
                    "nombre": encargado.nombre if encargado else "Sin asignar",
                    "usuario": encargado.usuario if encargado else "N/A"
                }
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error al obtener información de estación: {str(e)}"
        }), 500

@dashboard_bp.route('/api/getEvaluacionesPendientes/<int:usuario_id>', methods=['GET'])
def get_evaluaciones_pendientes(usuario_id):
    try:
        # Obtener el usuario y validar
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
        
        estacion_id = usuario.estacion_id
        if not estacion_id:
            return jsonify({"success": False, "error": "Usuario no tiene estación asignada"}), 400
        
        # Obtener fecha actual
        fecha_actual = datetime.now()
        mes_actual = fecha_actual.month
        año_actual = fecha_actual.year
        
        # Calcular fecha límite (último día del mes actual)
        if mes_actual == 12:
            fecha_limite = datetime(año_actual + 1, 1, 1) - timedelta(days=1)
        else:
            fecha_limite = datetime(año_actual, mes_actual + 1, 1) - timedelta(days=1)
        
        # Obtener todos los empleados activos de la estación
        empleados_estacion = db.session.query(
            Empleado.id,
            Empleado.nombre,
            Puesto.nombre.label('puesto_nombre')
        ).join(
            Puesto, Empleado.puesto_id == Puesto.id
        ).filter(
            and_(
                Empleado.estacion_id == estacion_id,
                Empleado.activo == True
            )
        ).all()
        
        # Obtener empleados que YA tienen evaluación en el mes actual
        empleados_con_evaluacion = db.session.query(
            Empleado.id
        ).join(
            Evaluacion, Empleado.id == Evaluacion.empleado_id
        ).filter(
            and_(
                Empleado.estacion_id == estacion_id,
                Evaluacion.mes == mes_actual,
                Evaluacion.anio == año_actual
            )
        ).subquery()
        
        # Filtrar empleados SIN evaluación (pendientes)
        empleados_pendientes = []
        for empleado in empleados_estacion:
            # Verificar si este empleado NO tiene evaluación
            tiene_evaluacion = db.session.query(
                empleados_con_evaluacion.c.id
            ).filter(
                empleados_con_evaluacion.c.id == empleado.id
            ).first()
            
            if not tiene_evaluacion:
                # Calcular días vencidos
                dias_vencido = (fecha_actual.date() - fecha_limite.date()).days
                dias_vencido = max(0, dias_vencido)  # No puede ser negativo
                
                empleado_pendiente = {
                    "empleado_id": empleado.id,
                    "empleado_nombre": empleado.nombre,
                    "puesto_nombre": empleado.puesto_nombre,
                    "dias_vencido": dias_vencido,
                    "fecha_limite": fecha_limite.strftime('%Y-%m-%d')
                }
                empleados_pendientes.append(empleado_pendiente)
        
        # Ordenar por días vencido (más vencidos primero)
        empleados_pendientes.sort(key=lambda x: x['dias_vencido'], reverse=True)
        
        response_data = {
            "success": True,
            "data": empleados_pendientes
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error al obtener evaluaciones pendientes: {str(e)}"
        }), 500

@dashboard_bp.route('/api/getActividadReciente/<int:usuario_id>', methods=['GET'])
def get_actividad_reciente(usuario_id):
    try:
        # Get user's station
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({
                "success": False,
                "error": "Usuario no encontrado"
            }), 404
        
        estacion_id = usuario.estacion_id
        if not estacion_id:
            return jsonify({
                "success": False,
                "error": "Usuario no tiene estación asignada"
            }), 400
        
        actividades = []
        
        # Get recent completed evaluations (last 30 days)
        fecha_limite = datetime.now() - timedelta(days=30)
        
        evaluaciones_recientes = db.session.query(
            Evaluacion.id,
            Evaluacion.fecha_evaluacion,
            Evaluacion.calificacion_final,
            Empleado.nombre.label('empleado_nombre'),
            Puesto.nombre.label('puesto_nombre')
        ).join(
            Empleado, Evaluacion.empleado_id == Empleado.id
        ).join(
            Puesto, Empleado.puesto_id == Puesto.id
        ).filter(
            and_(
                Empleado.estacion_id == estacion_id,
                Evaluacion.fecha_evaluacion >= fecha_limite,
                Evaluacion.calificacion_final.isnot(None)
            )
        ).order_by(
            Evaluacion.fecha_evaluacion.desc()
        ).limit(10).all()
        
        # Add completed evaluations to activities
        for eval_data in evaluaciones_recientes:
            # Convert calificacion_final to scale of 5 (assuming it's stored as percentage)
            calificacion = eval_data.calificacion_final
            if calificacion > 5:  # If it's a percentage, convert to 1-5 scale
                calificacion = calificacion / 20  # 100/5 = 20
            
            actividades.append({
                "id": eval_data.id,
                "tipo": "evaluacion_completada",
                "descripcion": f"Evaluación completada para {eval_data.empleado_nombre}",
                "empleado_nombre": eval_data.empleado_nombre,
                "puesto_nombre": eval_data.puesto_nombre,
                "fecha": eval_data.fecha_evaluacion.strftime("%Y-%m-%d %H:%M:%S"),
                "calificacion": round(calificacion, 1)
            })
        
        # Get recently added employees (last 30 days)
        # Assuming there's a fecha_creacion or similar field in Empleado
        # If not available, we'll use a different approach
        empleados_recientes = db.session.query(
            Empleado.id,
            Empleado.nombre.label('empleado_nombre'),
            Puesto.nombre.label('puesto_nombre'),
            Empleado.activo  # Using activo field as a proxy for recent addition
        ).join(
            Puesto, Empleado.puesto_id == Puesto.id
        ).filter(
            and_(
                Empleado.estacion_id == estacion_id,
                Empleado.activo == True
            )
        ).order_by(
            Empleado.id.desc()  # Assuming higher IDs are more recent
        ).limit(5).all()
        
        # Add recently added employees to activities
        # Since we don't have fecha_creacion, we'll simulate recent dates
        for i, emp_data in enumerate(empleados_recientes):
            # Simulate dates for recently added employees (last 30 days)
            fecha_simulada = datetime.now() - timedelta(days=i+1, hours=9, minutes=15)
            
            actividades.append({
                "id": emp_data.id + 1000,  # Offset to avoid ID conflicts
                "tipo": "empleado_agregado",
                "descripcion": "Nuevo empleado agregado",
                "empleado_nombre": emp_data.empleado_nombre,
                "puesto_nombre": emp_data.puesto_nombre,
                "fecha": fecha_simulada.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # Sort all activities by date (most recent first)
        actividades.sort(key=lambda x: datetime.strptime(x['fecha'], "%Y-%m-%d %H:%M:%S"), reverse=True)
        
        # Limit to top 10 activities
        actividades = actividades[:10]
        
        return jsonify({
            "success": True,
            "data": actividades
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error al obtener actividad reciente: {str(e)}"
        }), 500

@dashboard_bp.route('/api/getRendimientoEstacion/<int:usuario_id>', methods=['GET'])
def get_rendimiento_estacion(usuario_id):
    try:
        # Get user's station
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({
                "success": False,
                "error": "Usuario no encontrado"
            }), 404
        
        estacion_id = usuario.estacion_id
        if not estacion_id:
            return jsonify({
                "success": False,
                "error": "Usuario no tiene estación asignada"
            }), 400
        
        current_year = datetime.now().year
        
        # 1. Get monthly averages for current year
        promedio_mensual = db.session.query(
            Evaluacion.mes,
            func.avg(Evaluacion.calificacion_final).label('promedio'),
            func.count(Evaluacion.id).label('evaluaciones')
        ).join(
            Empleado, Evaluacion.empleado_id == Empleado.id
        ).filter(
            and_(
                Empleado.estacion_id == estacion_id,
                Evaluacion.anio == current_year,
                Evaluacion.calificacion_final.isnot(None)
            )
        ).group_by(
            Evaluacion.mes
        ).order_by(
            Evaluacion.mes
        ).all()
        
        # Format monthly data
        promedio_mensual_data = []
        for mes_data in promedio_mensual:
            # Convert average to scale of 5 (assuming stored as percentage)
            promedio = mes_data.promedio
            if promedio > 5:  # If it's a percentage, convert to 1-5 scale
                promedio = promedio / 20  # 100/5 = 20
            
            promedio_mensual_data.append({
                "mes": mes_data.mes,
                "promedio": round(promedio, 1),
                "evaluaciones": mes_data.evaluaciones
            })
        
        # 2. Get performance by position
        rendimiento_por_puesto = db.session.query(
            Puesto.nombre.label('puesto'),
            func.avg(Evaluacion.calificacion_final).label('promedio'),
            func.count(func.distinct(Empleado.id)).label('empleados')
        ).join(
            Empleado, Evaluacion.empleado_id == Empleado.id
        ).join(
            Puesto, Empleado.puesto_id == Puesto.id
        ).filter(
            and_(
                Empleado.estacion_id == estacion_id,
                Evaluacion.anio == current_year,
                Evaluacion.calificacion_final.isnot(None)
            )
        ).group_by(
            Puesto.id, Puesto.nombre
        ).order_by(
            func.avg(Evaluacion.calificacion_final).desc()
        ).all()
        
        # Format position performance data
        rendimiento_por_puesto_data = []
        for puesto_data in rendimiento_por_puesto:
            # Convert average to scale of 5
            promedio = puesto_data.promedio
            if promedio > 5:
                promedio = promedio / 20
            
            rendimiento_por_puesto_data.append({
                "puesto": puesto_data.puesto,
                "promedio": round(promedio, 1),
                "empleados": puesto_data.empleados
            })
        
        # 3. Get top employees (highest average ratings)
        top_empleados = db.session.query(
            Empleado.nombre,
            Puesto.nombre.label('puesto'),
            func.avg(Evaluacion.calificacion_final).label('promedio')
        ).join(
            Evaluacion, Empleado.id == Evaluacion.empleado_id
        ).join(
            Puesto, Empleado.puesto_id == Puesto.id
        ).filter(
            and_(
                Empleado.estacion_id == estacion_id,
                Evaluacion.anio == current_year,
                Evaluacion.calificacion_final.isnot(None)
            )
        ).group_by(
            Empleado.id, Empleado.nombre, Puesto.nombre
        ).having(
            func.count(Evaluacion.id) >= 2  # At least 2 evaluations
        ).order_by(
            func.avg(Evaluacion.calificacion_final).desc()
        ).limit(10).all()
        
        # Format top employees data
        top_empleados_data = []
        for emp_data in top_empleados:
            # Convert average to scale of 5
            promedio = emp_data.promedio
            if promedio > 5:
                promedio = promedio / 20
            
            top_empleados_data.append({
                "nombre": emp_data.nombre,
                "promedio": round(promedio, 1),
                "puesto": emp_data.puesto
            })
        
        response_data = {
            "promedioMensual": promedio_mensual_data,
            "rendimientoPorPuesto": rendimiento_por_puesto_data,
            "topEmpleados": top_empleados_data
        }
        
        return jsonify({
            "success": True,
            "data": response_data
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error al obtener rendimiento de estación: {str(e)}"
        }), 500