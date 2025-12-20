from flask import Blueprint, request, jsonify, render_template, current_app
from models import db, SolicitudMaterial, EstacionMaterial, Material, Usuario, Estacion
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

@solicitudes_bp.route('/api/solicitudes/crear', methods=['POST'])
def create_solicitud():
    try:
        data = request.json
        material_id = data.get('material_id')
        usuario_id = data.get('usuario_id')
        cantidad = data.get('cantidad')
        comentario = data.get('comentarios')

        if not material_id or not usuario_id or not cantidad:
            return jsonify({'message': 'Faltan datos requeridos (material_id, usuario_id, cantidad)'}), 400

        nueva_solicitud = SolicitudMaterial(
            material_id=material_id,
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
                
                destinatario = SMTP_TO_DEFAULT or "soportesistemas@estacioneslapopular.com" 
                print(f"Iniciando envío de correo a: {destinatario}")
                
                # Enviar en hilo aparte
                threading.Thread(target=enviar_correo_async, args=(destinatario, "Nueva Solicitud de Material", html_content)).start()
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

@solicitudes_bp.route('/api/solicitudes', methods=['GET'])
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

@solicitudes_bp.route('/api/solicitudes/<int:id>/estado', methods=['PUT'])
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

        solicitud.estado = estado
        if comentarios:
            if solicitud.comentario:
                solicitud.comentario += f" | {comentarios}"
            else:
                solicitud.comentario = comentarios
        
        db.session.commit()

        return jsonify({'message': 'Estado actualizado correctamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500