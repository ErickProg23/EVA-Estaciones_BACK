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
        
        # Solo evaluaciones recientes; se omiten empleados recientes
        # Ordenar y limitar por consistencia, aunque la consulta ya limita y ordena
        actividades.sort(key=lambda x: datetime.strptime(x['fecha'], "%Y-%m-%d %H:%M:%S"), reverse=True)
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

@dashboard_bp.route('/api/getEmpleadosEnEstacion/<int:usuario_id>', methods=['GET'])
def get_empleados_estacion(usuario_id):
    try:
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
        estacion_id = usuario.estacion_id
        if not estacion_id:
            return jsonify({"success": False, "error": "Usuario no tiene estación asignada"}), 400

        resultados = db.session.query(
            Puesto.id.label('puesto_id'),
            Puesto.nombre.label('puesto_nombre'),
            func.count(Empleado.id).label('total_empleados')
        ).join(
            Empleado, Puesto.id == Empleado.puesto_id
        ).filter(
            Empleado.estacion_id == estacion_id,
            Empleado.activo == True
        ).group_by(
            Puesto.id, Puesto.nombre
        ).order_by(
            Puesto.nombre
        ).all()

        data = [
            {
                'puesto_id': r.puesto_id,
                'puesto_nombre': r.puesto_nombre,
                'total_empleados': r.total_empleados
            }
            for r in resultados
        ]

        return jsonify({"success": True, "data": data, "estacion_id": estacion_id}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al obtener empleados por puesto: {str(e)}"}), 500

@dashboard_bp.route('/api/getRendimientoMensual/<int:usuario_id>', methods=['GET'])
def get_rendimiento_mensual(usuario_id):
    try:
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
        estacion_id = usuario.estacion_id
        if not estacion_id:
            return jsonify({"success": False, "error": "Usuario no tiene estación asignada"}), 400

        anio_str = request.args.get('anio')
        if anio_str:
            try:
                anio_val = int(anio_str)
            except Exception:
                return jsonify({"success": False, "error": "Año inválido"}), 400
        else:
            anio_val = datetime.now().year

        rows = db.session.query(
            Evaluacion.mes,
            func.avg(Evaluacion.calificacion_final).label('promedio'),
            func.count(Evaluacion.id).label('evaluaciones')
        ).join(
            Empleado, Evaluacion.empleado_id == Empleado.id
        ).filter(
            and_(
                Empleado.estacion_id == estacion_id,
                Evaluacion.anio == anio_val,
                Evaluacion.calificacion_final.isnot(None)
            )
        ).group_by(
            Evaluacion.mes
        ).order_by(
            Evaluacion.mes
        ).all()

        mapa = {r.mes: r for r in rows}
        meses = []
        for m in range(1, 13):
            r = mapa.get(m)
            meses.append({
                'mes': m,
                'promedio': float(r.promedio) if r and r.promedio is not None else None,
                'evaluaciones': int(r.evaluaciones) if r else 0
            })

        return jsonify({"success": True, "data": {"anio": anio_val, "meses": meses}, "estacion_id": estacion_id}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al obtener rendimiento mensual: {str(e)}"}), 500

@dashboard_bp.route('/api/getAlertas/<int:usuario_id>', methods=['GET'])
def get_alertas(usuario_id):
    try:
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
        estacion_id = usuario.estacion_id
        if not estacion_id:
            return jsonify({"success": False, "error": "Usuario no tiene estación asignada"}), 400

        now = datetime.now()
        inicio_mes = datetime(now.year, now.month, 1)
        deadline = inicio_mes + timedelta(days=14)
        mes_actual = now.month
        anio_actual = now.year

        if now <= deadline:
            return jsonify({"success": True, "message": "Aún dentro del periodo de evaluación", "data": {"deadline": deadline.strftime('%Y-%m-%d'), "mes": mes_actual, "anio": anio_actual, "atrasos": {"puestos": [], "empleados": []}}}), 200

        empleados = db.session.query(
            Empleado.id,
            Empleado.nombre,
            Puesto.id.label('puesto_id'),
            Puesto.nombre.label('puesto_nombre')
        ).join(
            Puesto, Empleado.puesto_id == Puesto.id
        ).filter(
            Empleado.estacion_id == estacion_id,
            Empleado.activo == True
        ).all()

        evaluados_ids_rows = db.session.query(Empleado.id).join(
            Evaluacion, Evaluacion.empleado_id == Empleado.id
        ).filter(
            Empleado.estacion_id == estacion_id,
            Evaluacion.mes == mes_actual,
            Evaluacion.anio == anio_actual
        ).distinct().all()

        evaluados_ids = {row.id for row in evaluados_ids_rows}

        atrasados_empleados = []
        cont_por_puesto = {}
        for emp in empleados:
            if emp.id not in evaluados_ids:
                atrasados_empleados.append({
                    "empleado_id": emp.id,
                    "empleado_nombre": emp.nombre,
                    "puesto_id": emp.puesto_id,
                    "puesto_nombre": emp.puesto_nombre
                })
                key = (emp.puesto_id, emp.puesto_nombre)
                cont_por_puesto[key] = cont_por_puesto.get(key, 0) + 1

        atrasados_puestos = [
            {
                "puesto_id": k[0],
                "puesto_nombre": k[1],
                "pendientes": v
            }
            for k, v in cont_por_puesto.items()
        ]

        return jsonify({
            "success": True,
            "data": {
                "deadline": deadline.strftime('%Y-%m-%d'),
                "mes": mes_actual,
                "anio": anio_actual,
                "atrasos": {
                    "puestos": atrasados_puestos
                }
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al obtener alertas: {str(e)}"}), 500

