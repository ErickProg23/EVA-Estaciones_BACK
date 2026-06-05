from flask import Blueprint, request, jsonify
from models import db, Puesto, Estacion, Rol, Usuario, Bomba, LecturaManual, ComparativaTotal
import jwt, datetime
from decimal import Decimal, InvalidOperation
from sqlalchemy import func



lecturas_manuales = Blueprint('lecturas_manuales', __name__)

@lecturas_manuales.route('/getUltimaLecturaManualByUsuarioEstacion/<int:usuario_id>', methods=['GET'])
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

@lecturas_manuales.route('/guardarLecturaManual', methods=['POST'])
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
            cantidad = int(str(lectura_val))
        except Exception:
            return jsonify({'success': False, 'message': 'Lectura inválida'}), 400

        print("guardarLecturaManual -> lectura_val:", lectura_val, "cantidad_parsed:", cantidad)
        
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

        numero_bomba_val = None
        for cand in [numero_bomba_input, getattr(bomba, 'numero_bomba', None), bomba_id, getattr(bomba, 'id', None)]:
            if cand is None:
                continue
            try:
                numero_bomba_val = int(str(cand))
                break
            except Exception:
                continue

        if numero_bomba_val is None:
            return jsonify({'success': False, 'message': 'Número de bomba inválido'}), 400

        try:
            producto_final = int(bomba.producto_id) if bomba and bomba.producto_id is not None else (int(producto_id) if producto_id is not None else None)
        except Exception:
            return jsonify({'success': False, 'message': 'producto_id inválido'}), 400

        if producto_final is None:
            return jsonify({'success': False, 'message': 'No se pudo determinar el producto de la bomba'}), 400

        existe = LecturaManual.query.filter(
            LecturaManual.estacion_id == estacion_id,
            func.date(LecturaManual.fecha) == fecha_dt.date(),
            LecturaManual.turno == int(turno),
            LecturaManual.numero_bomba == numero_bomba_val,
            LecturaManual.producto_id == producto_final
        ).first()

        if existe:
            return jsonify({
                'success': False,
                'message': 'Ya existe una lectura para esa estación, fecha, turno y bomba',
                'lectura_existente_id': existe.id
            }), 409

        lectura_manual = LecturaManual(
            numero_bomba=numero_bomba_val,
            fecha=fecha_dt,
            turno=int(turno),
            estacion_id=estacion_id,
            cantidad=cantidad,
            producto_id=producto_final
        )
        db.session.add(lectura_manual)
        db.session.commit()

        saved = LecturaManual.query.get(lectura_manual.id)
        try:
            print('guardarLecturaManual -> stored cantidad:', int(saved.cantidad))
        except Exception:
            pass

        return jsonify({'success': True, 'message': 'Lectura guardada correctamente', 'lectura': {
            'id': lectura_manual.id,
            'bomba_id': bomba.id,
            'numero_bomba': bomba.numero_bomba if bomba else numero_bomba_input,
            'producto_id': producto_final,
            'fecha': lectura_manual.fecha.isoformat(),
            'turno': lectura_manual.turno,
            'estacion_id': lectura_manual.estacion_id,
            'cantidad': cantidad
        }}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error al guardar la lectura', 'error': str(e)}), 500

@lecturas_manuales.route('/getLecturasManualUltimas/<int:estacion_id>', methods=['GET'])
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

def prev_turno_fecha(fecha_str, turno):
    d = datetime.date.fromisoformat(fecha_str)
    if int(turno) > 1:
        return d, int(turno) - 1
    return d - datetime.timedelta(days=1), 3

@lecturas_manuales.route('/getLecturasManualDiferencias/<int:estacion_id>', methods=['GET'])
def get_lecturas_manual_diferencias(estacion_id):
    fecha_str = request.args.get('fecha')
    turno = request.args.get('turno', type=int)
    if not fecha_str or turno is None:
        return jsonify({'success': False, 'message': 'faltan fecha y turno'}), 400

    try:
        fecha_dt = datetime.date.fromisoformat(fecha_str)
    except Exception:
        return jsonify({'success': False, 'message': 'fecha inválida'}), 400

    prev_fecha_dt, prev_turno = prev_turno_fecha(fecha_str, turno)

    cur_list = (db.session.query(LecturaManual)
        .filter(LecturaManual.estacion_id == estacion_id)
        .filter(func.date(LecturaManual.fecha) == fecha_dt)
        .filter(LecturaManual.turno == turno)
        .all())

    prev_list = (db.session.query(LecturaManual)
        .filter(LecturaManual.estacion_id == estacion_id)
        .filter(func.date(LecturaManual.fecha) == prev_fecha_dt)
        .filter(LecturaManual.turno == prev_turno)
        .all())

    def k(it): return f"{it.estacion_id}:{it.producto_id}:{str(it.numero_bomba)}"
    cur_map = {k(it): it for it in cur_list}
    prev_map = {k(it): it for it in prev_list}
    keys = set(cur_map.keys()) | set(prev_map.keys())

    data = []
    for key in keys:
        c = cur_map.get(key)
        p = prev_map.get(key)
        final_actual = float(c.cantidad) if c else 0.0
        final_prev = float(p.cantidad) if p else 0.0
        dif = final_actual - final_prev
        data.append({
            'estacion_id': int(c.estacion_id if c else p.estacion_id),
            'producto_id': int(c.producto_id if c else p.producto_id),
            'numero_bomba': int(c.numero_bomba if c else p.numero_bomba),
            'fecha': fecha_dt.isoformat(),
            'turno': int(turno),
            'final_actual': final_actual,
            'fecha_prev': prev_fecha_dt.isoformat(),
            'turno_prev': int(prev_turno),
            'final_prev': final_prev,
            'dif_lecturas': dif,
            'success': True
        })

    return jsonify({'success': True, 'lecturas': data}), 200

@lecturas_manuales.route('/saveComparativaTotales', methods=['POST'])
def save_comparativa_totales():
    try:
        data = request.get_json()
        estacion_id = data.get('estacion_id')
        fecha_str = data.get('fecha')
        turno = data.get('turno')
        detalles = data.get('detalles')


        if not all([estacion_id, fecha_str, turno, detalles]):
            return jsonify({'success': False, 'message': 'Faltan datos'}), 400

        try:
            try:
                fecha_dt = datetime.datetime.fromisoformat(str(fecha_str)).date()
            except ValueError:
                fecha_dt = datetime.datetime.strptime(str(fecha_str), '%Y-%m-%d').date()
        except Exception:
            return jsonify({'success': False, 'message': 'Fecha inválida'}), 400

        # Upsert logic
        for prod_id_str, info in detalles.items():
            try:
                prod_id = int(prod_id_str)
                nexus = float(info.get('nexus', 0))
                dif_lect = float(info.get('dif_lect', 0))
                precio = float(info.get('precio', 0))
                dif_pesos = float(info.get('dif_pesos', 0))
            except ValueError:
                continue
            
            existing = ComparativaTotal.query.filter_by(
                estacion_id=estacion_id,
                fecha=fecha_dt,
                turno=turno,
                producto_id=prod_id
            ).first()

            if existing:
                existing.nexus_total = nexus
                existing.diferencia_lecturas = dif_lect
                existing.precio_unitario = precio
                existing.diferencia_pesos = dif_pesos
            else:
                new_entry = ComparativaTotal(estacion_id, fecha_dt, turno, prod_id, nexus, dif_lect, precio, dif_pesos)
                db.session.add(new_entry)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Totales guardados correctamente'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error al guardar totales', 'error': str(e)}), 500

@lecturas_manuales.route('/getComparativaTotales/<int:estacion_id>', methods=['GET'])
def get_comparativa_totales(estacion_id):
    try:
        fecha_str = request.args.get('fecha')
        turno = request.args.get('turno')

        if not fecha_str or not turno:
            return jsonify({'success': False, 'message': 'Faltan fecha o turno'}), 400

        try:
            try:
                fecha_dt = datetime.datetime.fromisoformat(str(fecha_str)).date()
            except ValueError:
                fecha_dt = datetime.datetime.strptime(str(fecha_str), '%Y-%m-%d').date()
        except Exception:
            return jsonify({'success': False, 'message': 'Fecha inválida'}), 400
        
        results = ComparativaTotal.query.filter_by(
            estacion_id=estacion_id,
            fecha=fecha_dt,
            turno=turno
        ).all()

        data = {}
        for r in results:
            data[str(r.producto_id)] = {
                'nexus': r.nexus_total,
                'dif_lect': r.diferencia_lecturas,
                'precio': r.precio_unitario,
                'dif_pesos': r.diferencia_pesos
            }
        
        return jsonify({'success': True, 'detalles': data}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al obtener totales', 'error': str(e)}), 500