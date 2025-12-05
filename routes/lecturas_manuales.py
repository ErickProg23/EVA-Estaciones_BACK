from flask import Blueprint, request, jsonify
from models import db, Puesto, Estacion, Rol, Usuario, Bomba, LecturaManual
import jwt, datetime


lecturas_manuales = Blueprint('lecturas_manuales', __name__)

@lecturas_manuales.route('/api/getUltimaLecturaManualByUsuarioEstacion/<int:usuario_id>', methods=['GET'])
def get_ultima_lectura_manual(usuario_id):
    try:
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
        if not usuario.activo:
            return jsonify({'success': False, 'message': 'Usuario inactivo'}), 400
        if not usuario.estacion_id:
            return jsonify({'success': False, 'message': 'Usuario no tiene estación asignada'}), 400

        lectura = LecturaManual.query.filter_by(estacion_id=usuario.estacion_id)\
            .order_by(LecturaManual.fecha.desc(), LecturaManual.turno.desc(), LecturaManual.id.desc()).first()

        if not lectura:
            return jsonify({'success': True, 'message': 'No hay lecturas para la estación', 'lectura': None}), 200

        return jsonify({'success': True, 'lectura': {
            'id': lectura.id,
            'numero_bomba': lectura.numero_bomba,
            'fecha': lectura.fecha.isoformat(),
            'turno': lectura.turno,
            'estacion_id': lectura.estacion_id,
            'cantidad': lectura.cantidad
        }}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al obtener última lectura', 'error': str(e)}), 500

@lecturas_manuales.route('/api/guardarLecturaManual', methods=['POST'])
def guardar_lectura_manual():
    try:
        data = request.get_json() or {}
        lectura_val = data.get('lectura')
        fecha_str = data.get('fecha')
        turno = data.get('turno')
        estacion_id = data.get('estacion_id')
        bomba_id = data.get('bomba_id')
        numero_bomba_input = data.get('numero_bomba')
        producto_id = data.get('producto_id')

        if lectura_val is None or fecha_str is None or turno is None or estacion_id is None or (bomba_id is None and numero_bomba_input is None):
            return jsonify({'success': False, 'message': 'Faltan datos: lectura, fecha, turno, estacion_id y bomba_id o numero_bomba'}), 400

        try:
            cantidad = float(lectura_val)
        except Exception:
            return jsonify({'success': False, 'message': 'Lectura inválida'}), 400

        try:
            try:
                fecha_dt = datetime.datetime.fromisoformat(str(fecha_str))
            except Exception:
                fecha_dt = datetime.datetime.strptime(str(fecha_str), '%Y-%m-%d')
        except Exception:
            return jsonify({'success': False, 'message': 'Fecha inválida'}), 400

        estacion = Estacion.query.get(estacion_id)
        if not estacion:
            return jsonify({'success': False, 'message': 'Estación no encontrada'}), 404

        bomba = None
        if bomba_id is not None:
            try:
                bomba = Bomba.query.get(int(bomba_id))
            except Exception:
                bomba = None
        if not bomba and numero_bomba_input is not None:
            candidatos = Bomba.query.filter_by(estacion_id=estacion_id, numero_bomba=str(numero_bomba_input)).all()
            if producto_id is not None:
                try:
                    pid = int(producto_id)
                    candidatos = [b for b in candidatos if b.producto_id == pid]
                except Exception:
                    return jsonify({'success': False, 'message': 'producto_id inválido'}), 400
            if len(candidatos) == 1:
                bomba = candidatos[0]
            elif len(candidatos) > 1:
                return jsonify({'success': False, 'message': 'Número de bomba ambiguo en la estación; especifique producto_id o bomba_id'}), 400
        if not bomba:
            return jsonify({'success': False, 'message': 'Bomba no encontrada'}), 404

        lectura_manual = LecturaManual(
            numero_bomba=bomba.id,
            fecha=fecha_dt,
            turno=int(turno),
            estacion_id=estacion_id,
            cantidad=cantidad,
            producto_id=bomba.producto_id if bomba else producto_id
        )
        db.session.add(lectura_manual)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Lectura guardada correctamente', 'lectura': {
            'id': lectura_manual.id,
            'bomba_id': bomba.id,
            'numero_bomba': bomba.numero_bomba,
            'producto_id': bomba.producto_id,
            'fecha': lectura_manual.fecha.isoformat(),
            'turno': lectura_manual.turno,
            'estacion_id': lectura_manual.estacion_id,
            'cantidad': lectura_manual.cantidad
        }}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error al guardar la lectura', 'error': str(e)}), 500

@lecturas_manuales.route('/api/getLecturasManualUltimas/<int:estacion_id>', methods=['GET'])
def get_lecturas_manual_ultimas(estacion_id):
    try:
        fecha_str = request.args.get('fecha')
        turno_str = request.args.get('turno')

        if fecha_str:
            try:
                try:
                    base_dt = datetime.datetime.fromisoformat(str(fecha_str))
                except Exception:
                    base_dt = datetime.datetime.strptime(str(fecha_str), '%Y-%m-%d')
            except Exception:
                return jsonify({'success': False, 'message': 'Fecha inválida'}), 400
            start = datetime.datetime.combine(base_dt.date(), datetime.time.min)
            end = datetime.datetime.combine(base_dt.date(), datetime.time.max)
        else:
            latest = db.session.query(LecturaManual.fecha, LecturaManual.turno)\
                .filter(LecturaManual.estacion_id == estacion_id)\
                .order_by(LecturaManual.fecha.desc(), LecturaManual.turno.desc(), LecturaManual.id.desc()).first()
            if not latest:
                return jsonify({'success': True, 'lecturas': [], 'message': 'Sin lecturas'}), 200
            start = datetime.datetime.combine(latest.fecha.date(), datetime.time.min)
            end = datetime.datetime.combine(latest.fecha.date(), datetime.time.max)
            turno_str = str(latest.turno)

        if turno_str:
            try:
                turno_val = int(turno_str)
            except Exception:
                return jsonify({'success': False, 'message': 'Turno inválido'}), 400
        else:
            turno_val = db.session.query(db.func.max(LecturaManual.turno))\
                .filter(LecturaManual.estacion_id == estacion_id, LecturaManual.fecha >= start, LecturaManual.fecha <= end).scalar()
            if turno_val is None:
                return jsonify({'success': True, 'lecturas': [], 'message': 'Sin lecturas en la fecha'}), 200

        rows = LecturaManual.query\
            .filter(LecturaManual.estacion_id == estacion_id, LecturaManual.fecha >= start, LecturaManual.fecha <= end, LecturaManual.turno == turno_val)\
            .order_by(LecturaManual.fecha.desc(), LecturaManual.id.desc()).all()

        numeros = [str(r.numero_bomba) for r in rows]
        bombas = Bomba.query.filter(Bomba.estacion_id == estacion_id, Bomba.numero_bomba.in_(numeros)).all() if numeros else []
        bombas_map = {b.numero_bomba: b for b in bombas}

        lecturas = []
        por_producto = {}
        for r in rows:
            key = str(r.numero_bomba)
            b = bombas_map.get(key)
            item = {
                'id': r.id,
                'numero_bomba': key,
                'fecha': r.fecha.isoformat(),
                'turno': r.turno,
                'estacion_id': r.estacion_id,
                'cantidad': r.cantidad,
                'producto_id': (b.producto_id if b else r.producto_id)
            }
            lecturas.append(item)
            pid = item['producto_id']
            if pid not in por_producto:
                por_producto[pid] = []
            por_producto[pid].append(item)

        return jsonify({'success': True, 'message': 'Lecturas últimas obtenidas', 'fecha': start.date().isoformat(), 'turno': turno_val, 'lecturas': lecturas, 'lecturas_por_producto': por_producto}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al obtener lecturas últimas', 'error': str(e)}), 500
