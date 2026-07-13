from flask import Blueprint, request, jsonify, render_template, current_app
from models import db, SolicitudMaterial, EstacionMaterial, Material, Usuario, Estacion, Rol
from datetime import datetime
import os, smtplib, threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

solicitudes_bp = Blueprint('solicitudes_material', __name__)

# Cargar variables de entorno
load_dotenv()
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT") or 0)
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_FROM = os.getenv("SMTP_FROM") or SMTP_USER
SMTP_SSL = (os.getenv("SMTP_SSL") == "true") or (SMTP_PORT == 465)
SMTP_TO_DEFAULT = os.getenv("SMTP_TO_DEFAULT")

def enviar_correo_async(destinatario, asunto, html_content):
    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_FROM or "no-reply@localhost"
    msg["To"] = destinatario
    msg["Subject"] = asunto
    msg.attach(MIMEText(html_content, "html"))

    try:
        if SMTP_SSL:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                server.ehlo()
                if SMTP_USER and SMTP_PASS:
                    server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(msg["From"], destinatario, msg.as_string())
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                server.ehlo()
                try:
                    server.starttls()
                    server.ehlo()
                except Exception:
                    pass
                if SMTP_USER and SMTP_PASS:
                    server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(msg["From"], destinatario, msg.as_string())
        print(f"Correo enviado a {destinatario}")
    except Exception as e:
        print(f"Error enviando correo: {e}")

@solicitudes_bp.route('/solicitudes/crear', methods=['POST'])
def create_solicitud():
    try:
        data = request.json
        catalogo_material_id = data.get('material_id')
        usuario_id = data.get('usuario_id')
        cantidad = data.get('cantidad')
        comentario = data.get('comentarios')

        if not catalogo_material_id or not usuario_id or not cantidad:
            return jsonify({'message': 'Faltan datos requeridos (material_id, usuario_id, cantidad)'}), 400

        # 1. Obtener la estación del usuario
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({'message': 'Usuario no encontrado'}), 404

        # 2. Buscar el EstacionMaterial correspondiente (Inventario de esa estación)
        estacion_material = EstacionMaterial.query.filter_by(
            estacion_id=usuario.estacion_id,
            material_id=catalogo_material_id
        ).first()

        nueva_solicitud = SolicitudMaterial(
            material_id=estacion_material.id,
            usuario_id=usuario_id,
            cantidad=cantidad,
            comentario=comentario
        )
        db.session.add(nueva_solicitud)
        db.session.commit()

        # Preparar datos para el correo
        try:
            solicitud_full = db.session.query(SolicitudMaterial).join(EstacionMaterial).join(Material).join(Usuario).join(Estacion).filter(SolicitudMaterial.id == nueva_solicitud.id).first()
            
            if solicitud_full:
                # Obtener el objeto material a través de la relación estacion_material
                material_obj = solicitud_full.estacion_material.material
                
                html_content = render_template(
                    'correo_solicitud.html',
                    id=solicitud_full.id,
                    solicitante=solicitud_full.usuario.nombre,
                    estacion=solicitud_full.usuario.estacion.nombre,
                    material=material_obj.nombre,
                    unidad=material_obj.unidad,
                    cantidad=float(solicitud_full.cantidad),
                    fecha=solicitud_full.fecha_solicitada.strftime('%Y-%m-%d %H:%M'),
                    comentario=solicitud_full.comentario or "Sin comentarios"
                )
                
                admins =  (Usuarios.query
                        .join(Usuario.rol)
                        .filter(
                            Usuario.activo == True,
                            Rol.activo == True,
                            Rol.nombre.ilike('%administrador')
                        ).all())

                destinatarios = []
                for u in admins:
                    correo = (u.correo or '').strip()
                    if correo and correo not in destinatarios:
                        destinatarios.append(correo)
                if not destinatarios:
                    fallback= (SMTP_TO_DEFAULT or "soportesistemas@estacioneslapopular.com")
                    if fallback: 
                        destinatarios = [fallback]

                for dest in destinatarios:
                    threading.Thread(
                        target=enviar_correo_async, args=(dest, "Nueva solicitud de material", html_content)
                    ).start()

            else:
                print("No se pudo obtener la solicitud completa para el correo.")
        except Exception as e:
            print(f"Error preparando correo: {e}")
            import traceback
            traceback.print_exc()

        return jsonify({'message': 'Solicitud creada correctamente', 'id': nueva_solicitud.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@solicitudes_bp.route('/solicitudes', methods=['GET'])
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
                'material_id': s.material_id,
                'material_nombre': s.estacion_material.material.nombre,
                'unidad': s.estacion_material.material.unidad,
                'estacion_nombre': s.usuario.estacion.nombre if s.usuario.estacion else "Sin Estación",
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

@solicitudes_bp.route('/solicitudes/<int:id>/estado', methods=['PUT'])
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

        comentario_original = solicitud.comentario

        solicitud.estado = estado
        if comentarios:
            if solicitud.comentario:
                solicitud.comentario += f" | {comentarios}"
            else:
                solicitud.comentario = comentarios
        
        db.session.commit()

        try:
            if estado in ['aceptado', 'rechazado'] and solicitud.usuario and solicitud.usuario.correo:
                material_obj = solicitud.estacion_material.material if solicitud.estacion_material else None
                estacion_obj = solicitud.usuario.estacion if solicitud.usuario else None

                header_color = '#28a745' if estado == 'aceptado' else '#dc3545'
                page_title = f"Solicitud de Material #{solicitud.id} - {estado.upper()}"
                intro_text = f"Tu solicitud de material ha sido {estado}."

                html_content = render_template(
                    'correo_solicitud.html',
                    page_title=page_title,
                    header_color=header_color,
                    intro_text=intro_text,
                    id=solicitud.id,
                    solicitante=solicitud.usuario.nombre,
                    estacion=estacion_obj.nombre if estacion_obj else "Sin Estación",
                    estado=estado,
                    material=material_obj.nombre if material_obj else "N/A",
                    unidad=material_obj.unidad if material_obj else "",
                    cantidad=float(solicitud.cantidad),
                    fecha=solicitud.fecha_solicitada.strftime('%Y-%m-%d %H:%M') if solicitud.fecha_solicitada else "",
                    comentario=comentario_original or "Sin comentarios",
                    comentario_revision=comentarios or None
                )

                asunto = f"Solicitud de Material #{solicitud.id} - {estado.upper()}"
                threading.Thread(
                    target=enviar_correo_async,
                    args=(solicitud.usuario.correo, asunto, html_content)
                ).start()
        except Exception as e:
            print(f"Error enviando correo de actualización de estado: {e}")

        return jsonify({'message': 'Estado actualizado correctamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@solicitudes_bp.route('/solicitudes/<int:id>/confirmar', methods=['POST'])
def confirmar_recepcion(id):
    try:
        solicitud = SolicitudMaterial.query.get(id)
        if not solicitud:
            return jsonify({'message': 'Solicitud no encontrada'}), 404

        # Validar flujo: Admin (Aceptado) -> Encargado (Finalizado)
        # El usuario indicó que el Admin aprueba (Aceptado) y luego el Encargado confirma.
        # Se mantiene 'entregado' por compatibilidad, pero el estado principal esperado es 'aceptado'.
        if solicitud.estado not in ['aceptado', 'entregado']:
            return jsonify({'message': 'La solicitud debe estar Aceptada por el administrador para confirmar la recepción'}), 400

        # 1. Actualizar estado de la solicitud
        solicitud.estado = 'finalizado'
        
        # 2. Actualizar stock del material en la estación
        estacion_material = solicitud.estacion_material
        if estacion_material:
            cantidad_sumar = float(solicitud.cantidad)
            estacion_material.stock += cantidad_sumar
            db.session.add(estacion_material) # Asegurar que se marca para actualización
            
            msg = f" | Recepción confirmada: +{cantidad_sumar} stock el {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            if solicitud.comentario:
                solicitud.comentario += msg
            else:
                solicitud.comentario = msg.strip(" | ")
        else:
            return jsonify({'message': 'Error: No se encontró la asignación de material asociada'}), 500

        db.session.commit()

        return jsonify({'message': 'Recepción confirmada y stock actualizado correctamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500