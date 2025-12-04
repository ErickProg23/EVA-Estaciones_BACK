from flask import Blueprint, request, jsonify, render_template
from models import db, Ticket, TicketComentario, Usuario
from datetime import datetime
from sqlalchemy import func, and_, or_
from dotenv import load_dotenv
import os, smtplib, threading
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

tickets_bp = Blueprint('tickets', __name__)

MAILTRAP_HOST = "mail.evaluacioneseva.com"
MAILTRAP_PORT = 465
MAILTRAP_USER = "estaciones@evaluacioneseva.com"       # <-- cámbialo por el username que te dio Mailtrap
MAILTRAP_PASS = "q-f!R]&vM_lcaVgj"   # <-- cámbialo por la contraseña de Mailtrap

def enviar_correo_ticket(html_content, destinatario):
    msg = MIMEMultipart("alternative")

    msg["From"] = MAILTRAP_USER
    msg["To"] = destinatario or "soportesistemas@estacioneslapopular.com"
    msg["Subject"] = "Ticket nuevo creado"
    msg.attach(MIMEText(html_content, "html"))

    smtp_host = MAILTRAP_HOST
    smtp_port = MAILTRAP_PORT
    smtp_user = MAILTRAP_USER
    smtp_pass = MAILTRAP_PASS
    smtp_ssl  = True


    if not smtp_host or not smtp_port:
        print("SMTP: falta HOST o PORT")
        print("HOST:", smtp_host)
        print("PORT:", smtp_port)
        print("USER:", smtp_user)
        print("PASS:", smtp_pass)
        print("SSL:", smtp_ssl)
        return False

    try:
        if smtp_ssl:
            # Conexión SSL directa
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
                server.ehlo()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.sendmail(msg["From"], msg["To"], msg.as_string())

        else:
            # Conexión normal + STARTTLS si está disponible
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.ehlo()
                try:
                    server.starttls()
                    server.ehlo()
                except Exception:
                    print("Advertencia: no se pudo iniciar STARTTLS")

                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)

                server.sendmail(msg["From"], msg["To"], msg.as_string())

        print("Correo enviado correctamente ✔")
        return True

    except Exception as e:
        print("Error enviando correo:", str(e))
        return False


def enviar_correo_comentario(destinatario, asunto, mensaje_html):
    msg = MIMEMultipart("alternative")
    msg["From"] = "soporte@estacioneslapopular.com"
    msg["To"] = destinatario
    msg["Subject"] = asunto

    html_part = MIMEText(mensaje_html, "html")
    msg.attach(html_part)

    with smtplib.SMTP(MAILTRAP_HOST, MAILTRAP_PORT) as server:
        server.login(MAILTRAP_USER, MAILTRAP_PASS)
        server.sendmail(msg["From"], destinatario, msg.as_string())

    print("Correo enviado correctamente (capturado en Mailtrap)")

# Obtener todos los tickets (para ADMIN)
@tickets_bp.route('/tickets', methods=['GET'])
def get_tickets():
    try:
        tickets = db.session.query(
            Ticket.id,
            Ticket.titulo,
            Ticket.descripcion,
            Ticket.estado,
            Ticket.prioridad,
            Ticket.fecha_creacion,
            Ticket.fecha_resolucion,
            Ticket.creador_id,
            Ticket.asignado_id,
            Ticket.categoria,
            Usuario.nombre.label('creador_nombre'),
        ).outerjoin(
            Usuario, Ticket.creador_id == Usuario.id
        ).order_by(
            Ticket.fecha_creacion.desc()
        ).all()
        
        tickets_data = []
        for ticket in tickets:
            # Obtener información del técnico asignado
            tecnico = None
            if ticket.asignado_id:
                tecnico = Usuario.query.get(ticket.asignado_id)
            
            tickets_data.append({
                'id': ticket.id,
                'titulo': ticket.titulo,
                'descripcion': ticket.descripcion,
                'estado': ticket.estado,
                'categoria': ticket.categoria,
                'prioridad': ticket.prioridad,
                'fecha_creacion': ticket.fecha_creacion.isoformat() if ticket.fecha_creacion else None,
                'fecha_resolucion': ticket.fecha_resolucion.isoformat() if ticket.fecha_resolucion else None,
                'creador': {
                    'id': ticket.creador_id,
                    'nombre': ticket.creador_nombre,
                },
                'asignado': {
                    'id': ticket.asignado_id,
                    'nombre': tecnico.nombre if tecnico else 'Sin asignar'
                }
            })
        
        return jsonify({
            'success': True,
            'data': tickets_data,
            'total': len(tickets_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error al obtener tickets',
            'error': str(e)
        }), 500

# Obtener tickets por usuario (creados por él o asignados a él)
@tickets_bp.route('/tickets/usuario/<int:usuario_id>', methods=['GET'])
def get_tickets_by_usuario(usuario_id):
    try:
        # Verificar que el usuario existe
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado'
            }), 404
        
        # Obtener tickets creados por el usuario O asignados al usuario
        tickets = db.session.query(
            Ticket.id,
            Ticket.titulo,
            Ticket.descripcion,
            Ticket.estado,
            Ticket.prioridad,
            Ticket.fecha_creacion,
            Ticket.fecha_resolucion,
            Ticket.creador_id,
            Ticket.asignado_id,
            Ticket.categoria
        ).filter(
            or_(
                Ticket.creador_id == usuario_id,
                Ticket.asignado_id == usuario_id
            )
        ).order_by(
            Ticket.fecha_creacion.desc()
        ).all()
        
        tickets_data = []
        for ticket in tickets:
            # Obtener información del creador y técnico asignado
            creador = Usuario.query.get(ticket.creador_id) if ticket.creador_id else None
            tecnico = Usuario.query.get(ticket.asignado_id) if ticket.asignado_id else None
            categoria = ticket.categoria
            
            tickets_data.append({
                'id': ticket.id,
                'titulo': ticket.titulo,
                'descripcion': ticket.descripcion,
                'estado': ticket.estado,
                'prioridad': ticket.prioridad,
                'fecha_creacion': ticket.fecha_creacion.isoformat() if ticket.fecha_creacion else None,
                'fecha_resolucion': ticket.fecha_resolucion.isoformat() if ticket.fecha_resolucion else None,
                'es_creador': ticket.creador_id == usuario_id,
                'es_asignado': ticket.asignado_id == usuario_id,
                'categoria': categoria,
                'creador': {
                    'id': ticket.creador_id,
                    'nombre': creador.nombre if creador else 'Usuario eliminado'
                },
                'asignado': {
                    'id': ticket.asignado_id,
                    'nombre': tecnico.nombre if tecnico else 'Sin asignar'
                }
            })
        
        return jsonify({
            'success': True,
            'data': tickets_data,
            'usuario': {
                'id': usuario.id,
                'nombre': usuario.nombre,
                'estacion_id': usuario.estacion_id,
                'rol_id': usuario.rol_id
            },
            'total': len(tickets_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error al obtener tickets por usuario',
            'error': str(e)
        }), 500

# Crear nuevo ticket
@tickets_bp.route('/tickets', methods=['POST'])
def create_ticket():
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        titulo = data.get('titulo')
        descripcion = data.get('descripcion')
        creador_id = data.get('creador_id')
        prioridad_input = data.get('prioridad', 1)  # Puede ser string o int
        categoria = data.get('categoria', 1)  # Puede ser string o int
        
        # Convertir prioridad de string a int si es necesario
        if isinstance(prioridad_input, str):
            prioridad_map = {
                'baja': 1,
                'media': 2,
                'alta': 3
            }
            prioridad = prioridad_map.get(prioridad_input.lower(), 1)
        else:
            prioridad = prioridad_input if prioridad_input in [1, 2, 3] else 1
        
        if not all([titulo, descripcion, creador_id]):
            return jsonify({
                'success': False,
                'message': 'Faltan datos requeridos: titulo, descripcion, creador_id'
            }), 400
        
        # Verificar que el usuario creador existe
        usuario = Usuario.query.get(creador_id)
        if not usuario or not usuario.activo:
            return jsonify({
                'success': False,
                'message': 'Usuario creador no encontrado o inactivo'
            }), 404
        
        # Asignar automáticamente al usuario con ID 1 si no se especifica asignado
        asignado_id = data.get('asignado_id')
        if not asignado_id:
            # Verificar que el usuario con ID 1 existe y está activo
            usuario_admin = Usuario.query.get(1)
            if usuario_admin and usuario_admin.activo:
                asignado_id = 1
        
        # Crear nuevo ticket
        nuevo_ticket = Ticket(
            titulo=titulo,
            descripcion=descripcion,
            creador_id=creador_id,
            asignado_id=asignado_id,
            estado=1,  # 1=abierto por defecto
            prioridad=prioridad,
            fecha_creacion=datetime.now(),
            fecha_resolucion=None,
            categoria=categoria
        )
        
        db.session.add(nuevo_ticket)
        db.session.commit()

        datos_ticket = {
            "titulo": nuevo_ticket.titulo,
            "prioridad": nuevo_ticket.prioridad,
            "estado": "Abierto",
            "descripcion": nuevo_ticket.descripcion,
            "nombre_usuario": usuario.nombre,
            "fecha": nuevo_ticket.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
            "año": datetime.now().year,
            "ticket_id": nuevo_ticket.id,
            "url_ticket": os.getenv('APP_TICKET_URL', '#')
        }
        sistema = Usuario.query.get(1)
        destinatario = sistema.correo if sistema and getattr(sistema, 'correo', None) else os.getenv('SMTP_TO_DEFAULT')
        html_content = render_template("correo_ticket.html", **datos_ticket)
        try:
            threading.Thread(target=enviar_correo_ticket, args=(html_content, destinatario), daemon=True).start()
        except Exception:
            pass
        
        return jsonify({
            'success': True,
            'message': 'Ticket creado exitosamente',
            'data': {
                'id': nuevo_ticket.id,
                'titulo': nuevo_ticket.titulo,
                'descripcion': nuevo_ticket.descripcion,
                'estado': nuevo_ticket.estado,
                'prioridad': nuevo_ticket.prioridad,
                'fecha_creacion': nuevo_ticket.fecha_creacion.isoformat(),
                'creador_id': nuevo_ticket.creador_id,
                'asignado_id': nuevo_ticket.asignado_id,
                'categoria': nuevo_ticket.categoria
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error al crear ticket',
            'error': str(e)
        }), 500

# Obtener ticket por ID
@tickets_bp.route('/tickets/<int:ticket_id>', methods=['GET'])
def get_ticket_by_id(ticket_id):
    try:
        ticket = Ticket.query.get(ticket_id)
        
        if not ticket:
            return jsonify({
                'success': False,
                'message': 'Ticket no encontrado'
            }), 404
        
        # Obtener información del creador y técnico asignado
        creador = Usuario.query.get(ticket.creador_id) if ticket.creador_id else None
        tecnico = Usuario.query.get(ticket.asignado_id) if ticket.asignado_id else None
        
        ticket_data = {
            'id': ticket.id,
            'titulo': ticket.titulo,
            'descripcion': ticket.descripcion,
            'estado': ticket.estado,
            'prioridad': ticket.prioridad,
            'fecha_creacion': ticket.fecha_creacion.isoformat() if ticket.fecha_creacion else None,
            'fecha_resolucion': ticket.fecha_resolucion.isoformat() if ticket.fecha_resolucion else None,
            'creador': {
                'id': ticket.creador_id,
                'nombre': creador.nombre if creador else 'Usuario eliminado',
            },
            'asignado': {
                'id': ticket.asignado_id,
                'nombre': tecnico.nombre if tecnico else 'Sin asignar'
            }
        }
        
        return jsonify({
            'success': True,
            'data': ticket_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error al obtener ticket',
            'error': str(e)
        }), 500

# Actualizar ticket
@tickets_bp.route('/tickets/<int:ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    try:
        data = request.get_json()
        
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({
                'success': False,
                'message': 'Ticket no encontrado'
            }), 404
        
        # Actualizar campos si se proporcionan
        if 'titulo' in data:
            ticket.titulo = data['titulo']
        if 'descripcion' in data:
            ticket.descripcion = data['descripcion']
        if 'estado' in data:
            ticket.estado = data['estado']
        if 'prioridad' in data:
            ticket.prioridad = data['prioridad']
        if 'asignado_id' in data:
            ticket.asignado_id = data['asignado_id']
        
        # Si se marca como resuelto, agregar fecha de resolución
        if data.get('estado') in [3, 4]:  # resuelto o cerrado
            ticket.fecha_resolucion = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Ticket actualizado exitosamente',
            'data': {
                'id': ticket.id,
                'titulo': ticket.titulo,
                'descripcion': ticket.descripcion,
                'estado': ticket.estado,
                'prioridad': ticket.prioridad,
                'fecha_resolucion': ticket.fecha_resolucion.isoformat() if ticket.fecha_resolucion else None
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error al actualizar ticket',
            'error': str(e)
        }), 500

# Actualizar estado del ticket
@tickets_bp.route('/tickets/<int:ticket_id>/estado', methods=['PATCH'])
def update_ticket_status(ticket_id):
    try:
        data = request.get_json()
        estado = data.get('estado')
        
        if estado is None:
            return jsonify({
                'success': False,
                'message': 'Estado es requerido'
            }), 400
        
        # Validar estados permitidos (1=abierto, 2=en_progreso, 3=resuelto, 4=cerrado)
        estados_validos = [1, 2, 3, 4]
        if estado not in estados_validos:
            return jsonify({
                'success': False,
                'message': f'Estado inválido. Estados permitidos: {estados_validos}'
            }), 400
        
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({
                'success': False,
                'message': 'Ticket no encontrado'
            }), 404
        
        ticket.estado = estado
        
        # Si se marca como resuelto o cerrado, agregar fecha de resolución
        if estado in [3, 4]:
            ticket.fecha_resolucion = datetime.now()
        
        db.session.commit()
        
        estados_nombres = {1: 'abierto', 2: 'en_progreso', 3: 'resuelto', 4: 'cerrado'}
        
        return jsonify({
            'success': True,
            'message': f'Estado del ticket actualizado a: {estados_nombres.get(estado, estado)}',
            'data': {
                'id': ticket.id,
                'estado': ticket.estado,
                'fecha_resolucion': ticket.fecha_resolucion.isoformat() if ticket.fecha_resolucion else None
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error al actualizar estado del ticket',
            'error': str(e)
        }), 500

# Asignar ticket a técnico
@tickets_bp.route('/tickets/<int:ticket_id>/asignar', methods=['PATCH'])
def assign_ticket(ticket_id):
    try:
        data = request.get_json()
        asignado_id = data.get('asignado_id')
        
        if not asignado_id:
            return jsonify({
                'success': False,
                'message': 'ID del técnico es requerido'
            }), 400
        
        # Verificar que el técnico existe
        tecnico = Usuario.query.get(asignado_id)
        if not tecnico or not tecnico.activo:
            return jsonify({
                'success': False,
                'message': 'Técnico no encontrado o inactivo'
            }), 404
        
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({
                'success': False,
                'message': 'Ticket no encontrado'
            }), 404
        
        ticket.asignado_id = asignado_id
        
        # Si el ticket estaba abierto, cambiarlo a en_progreso
        if ticket.estado == 1:  # abierto
            ticket.estado = 2  # en_progreso
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Ticket asignado a {tecnico.nombre}',
            'data': {
                'id': ticket.id,
                'asignado_id': ticket.asignado_id,
                'asignado_nombre': tecnico.nombre,
                'estado': ticket.estado
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error al asignar ticket',
            'error': str(e)
        }), 500

# Obtener estadísticas de tickets
@tickets_bp.route('/tickets/estadisticas', methods=['GET'])
def get_ticket_stats():
    try:
        # Estadísticas por estado
        stats_estado = db.session.query(
            Ticket.estado,
            func.count(Ticket.id).label('cantidad')
        ).group_by(Ticket.estado).all()
        
        # Estadísticas por prioridad
        stats_prioridad = db.session.query(
            Ticket.prioridad,
            func.count(Ticket.id).label('cantidad')
        ).group_by(Ticket.prioridad).all()
        
        # Total de tickets
        total_tickets = db.session.query(func.count(Ticket.id)).scalar()
        
        # Tickets sin asignar
        tickets_sin_asignar = db.session.query(
            func.count(Ticket.id)
        ).filter(Ticket.asignado_id.is_(None)).scalar()
        
        # Mapear números a nombres
        estados_nombres = {1: 'abierto', 2: 'en_progreso', 3: 'resuelto', 4: 'cerrado'}
        prioridades_nombres = {1: 'baja', 2: 'media', 3: 'alta'}
        
        estadisticas = {
            'total_tickets': total_tickets,
            'tickets_sin_asignar': tickets_sin_asignar,
            'por_estado': {estados_nombres.get(stat.estado, f'estado_{stat.estado}'): stat.cantidad for stat in stats_estado},
            'por_prioridad': {prioridades_nombres.get(stat.prioridad, f'prioridad_{stat.prioridad}'): stat.cantidad for stat in stats_prioridad}
        }
        
        return jsonify({
            'success': True,
            'data': estadisticas
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error al obtener estadísticas',
            'error': str(e)
        }), 500

# Eliminar ticket
@tickets_bp.route('/tickets/<int:ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    try:
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({
                'success': False,
                'message': 'Ticket no encontrado'
            }), 404
        
        # Guardar información antes de eliminar
        ticket_info = {
            'id': ticket.id,
            'titulo': ticket.titulo
        }
        
        db.session.delete(ticket)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Ticket "{ticket_info["titulo"]}" eliminado exitosamente',
            'data': ticket_info
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error al eliminar ticket',
            'error': str(e)
        }), 500

@tickets_bp.get('/tickets/<int:ticket_id>/comentarios')
def get_comentarios(ticket_id):
    comentarios = (db.session.query(TicketComentario, Usuario.nombre.label('usuario_nombre'))
        .join(Usuario, TicketComentario.usuario_id == Usuario.id)
        .filter(TicketComentario.ticket_id == ticket_id)
        .order_by(TicketComentario.created_at.asc())
        .all())

    return jsonify([
        {
            'id': comentario.id,
            'comentario': comentario.comentario,
            'created_at': comentario.created_at.isoformat(),
            'usuario': {'id': comentario.usuario_id, 'nombre': nombre}
        }
        for comentario, nombre in comentarios
    ])

@tickets_bp.post('/tickets/<int:ticket_id>/comentarios')
def add_comentario(ticket_id):
    data = request.get_json(silent=True) or {}
    comentario = (data.get('comentario') or '').strip()

    usuario_id = request.headers.get('token_usuario_id') or data.get('usuario_id')
    try:
        usuario_id = int(usuario_id)
    except (TypeError, ValueError):
        usuario_id = None

    if not comentario:
        return jsonify({'success': False, 'message': 'Comentario requerido'}), 400
    if not usuario_id:
        return jsonify({'success': False, 'message': 'Usuario no autenticado'}), 401

    db.session.add(TicketComentario(ticket_id=ticket_id, usuario_id=usuario_id, comentario=comentario))
    db.session.commit()

    # Enviar correo al usuario que comentó
    enviar_correo_comentario(
        destinatario="soportesistemas@estacioneslapopular.com",
        asunto="Nuevo comentario en tu ticket",
        mensaje_html=f"""
            <h3>Has recibido un nuevo comentario en tu ticket</h3>
            <p>Comentario: {comentario}</p>
            <p>Recuerda que puedes ver todos los comentarios en el sistema.</p>
        """
    )

    return jsonify({'success': True}), 200

