from flask import Blueprint, request, jsonify
from models import db, Ticket, Usuario, Evaluacion, Empleado, Puesto, Estacion
from datetime import datetime
from sqlalchemy import func, and_, or_

reportes_bp = Blueprint('reportes', __name__)  

@reportes_bp.route('/api/getReportesEstaciones', methods=['GET'])
def get_reportes_estaciones():
    try:
        # Query corregida para compatibilidad con ONLY_FULL_GROUP_BY
        query = db.session.query(
            Estacion.id.label('estacion_id'),
            Estacion.nombre.label('estacion_nombre'),
            Puesto.id.label('puesto_id'),
            Puesto.nombre.label('puesto_nombre'),
            Empleado.id.label('empleado_id'),
            Empleado.nombre.label('empleado_nombre'),
            func.avg(Evaluacion.calificacion_final).label('promedio'),
            func.count(Evaluacion.id).label('total_evaluaciones'),
            Evaluacion.mes,
            Evaluacion.anio.label('año'),
            func.max(Evaluacion.fecha_evaluacion).label('fecha_evaluacion')
        ).join(
            Empleado, Evaluacion.empleado_id == Empleado.id
        ).join(
            Puesto, Empleado.puesto_id == Puesto.id
        ).join(
            Estacion, Empleado.estacion_id == Estacion.id
        ).group_by(
            Estacion.id,
            Estacion.nombre,
            Puesto.id,
            Puesto.nombre,
            Empleado.id,
            Empleado.nombre,
            Evaluacion.mes,
            Evaluacion.anio
        ).order_by(
            Estacion.nombre,
            Empleado.nombre,
            Evaluacion.anio.desc(),
            Evaluacion.mes.desc()
        )
        
        resultados = query.all()
        
        # Formatear los resultados con promedio en escala de 100
        reportes = []
        for idx, resultado in enumerate(resultados, 1):
            # Convertir promedio a escala de 100
            # Asumiendo que calificacion_final está en escala 1-5, convertimos a 100
            promedio_100 = 0
            if resultado.promedio:
                # Si tu escala es 1-5, usa esta fórmula:
                promedio_100 = (resultado.promedio / 5.0) * 100
                # Si tu escala es 1-10, usa esta fórmula:
                # promedio_100 = (resultado.promedio / 10.0) * 100
                # Si ya está en escala 1-100, usa:
                # promedio_100 = resultado.promedio
            
            reporte = {
                "id": idx,
                "estacion_id": resultado.estacion_id,
                "estacion_nombre": resultado.estacion_nombre,
                "puesto_id": resultado.puesto_id,
                "puesto_nombre": resultado.puesto_nombre,
                "empleado_id": resultado.empleado_id,
                "empleado_nombre": resultado.empleado_nombre,
                "promedio": f"{promedio_100:.1f}",  # Promedio en escala de 100
                "total_evaluaciones": resultado.total_evaluaciones,
                "mes": resultado.mes,
                "año": resultado.año,
                "fecha_evaluacion": resultado.fecha_evaluacion.strftime('%Y-%m-%d') if resultado.fecha_evaluacion else None
            }
            reportes.append(reporte)
        
        return jsonify(reportes), 200
        
    except Exception as e:
        return jsonify({"error": f"Error al obtener reportes: {str(e)}"}), 500
