# models.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(80), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    estacion_id = db.Column(db.Integer, db.ForeignKey('estacion.id'))
    rol_id = db.Column(db.Integer, db.ForeignKey('rol.id'))
    correo = db.Column(db.String(120), nullable=False)
    activo = db.Column(db.Boolean, default=True)

    #Relaciones
    rol = db.relationship('Rol', backref='usuarios')
    estacion = db.relationship('Estacion', backref='usuarios')

    def __init__(self, usuario, password, estacion_id, rol_id, nombre, activo, correo):
        self.usuario = usuario
        self.password = password
        self.estacion_id = estacion_id
        self.rol_id = rol_id
        self.nombre = nombre
        self.activo = activo
        self.correo = correo

class Rol(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    activo = db.Column(db.Boolean, default=True)

    def __init__(self, nombre, descripcion=None, activo=True):
        self.nombre = nombre
        self.descripcion = descripcion
        self.activo = activo

class Estacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    fecha_creacion = db.Column(db.DateTime, nullable=False)
    activo = db.Column(db.Boolean, default=True)

    def __init__(self, nombre, fecha_creacion, activo=True):
        self.nombre = nombre
        self.fecha_creacion = fecha_creacion
        self.activo = activo

class Puesto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    estacion_id = db.Column(db.Integer, db.ForeignKey('estacion.id'))
    activo = db.Column(db.Boolean, default=True)

    puesto_aspectos = db.relationship('PuestoAspecto', backref='puesto')


    def __init__(self, nombre, estacion_id, activo=True):
        self.nombre = nombre
        self.estacion_id = estacion_id
        self.activo = activo

class Aspecto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    activo = db.Column(db.Boolean, default=True)

    aspecto_puestos = db.relationship('PuestoAspecto', backref='aspecto')


    def __init__(self, nombre, activo=True):
        self.nombre = nombre
        self.activo = activo

class PuestoAspecto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    puesto_id = db.Column(db.Integer, db.ForeignKey('puesto.id'))
    aspecto_id = db.Column(db.Integer, db.ForeignKey('aspecto.id'))
    peso = db.Column(db.Integer, nullable=False)


    def __init__(self, puesto_id, aspecto_id, peso):
        self.puesto_id = puesto_id
        self.aspecto_id = aspecto_id
        self.peso = peso

    __table_args__ = (
        db.UniqueConstraint('puesto_id', 'aspecto_id', name='uq_puesto_aspecto'),
    )


class Notificacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    accion = db.Column(db.Integer, nullable=False)
    activo = db.Column(db.Boolean, default=True)

    def __init__(self, usuario_id, accion, activo=True):
        self.usuario_id = usuario_id
        self.accion = accion
        self.activo = activo

class Empleado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    puesto_id = db.Column(db.Integer, db.ForeignKey('puesto.id'))
    estacion_id = db.Column(db.Integer, db.ForeignKey('estacion.id'))
    num_empleado = db.Column(db.Integer, nullable=False)
    activo = db.Column(db.Boolean, default=True)

    #Relaciones
    puesto = db.relationship('Puesto', backref='empleados')
    estacion = db.relationship('Estacion', backref='empleados')

    def __init__(self, nombre, puesto_id, estacion_id, num_empleado, activo=True):
        self.nombre = nombre
        self.puesto_id = puesto_id
        self.estacion_id = estacion_id
        self.num_empleado = num_empleado
        self.activo = activo

class Evaluacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'))
    mes = db.Column(db.Integer, nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    fecha_evaluacion = db.Column(db.DateTime, nullable=False)
    calificacion_final = db.Column(db.Float, nullable=False)
    porcentaje_final = db.Column(db.Float, nullable=False)
    comentario = db.Column(db.Text, nullable=True)
    faltas = db.Column(db.Integer, nullable=False, default=0)
    incapacidad = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, empleado_id, mes, anio, fecha_evaluacion, calificacion_final, porcentaje_final, comentario, faltas=0, incapacidad=0):
        self.empleado_id = empleado_id
        self.mes = mes
        self.anio = anio
        self.fecha_evaluacion = fecha_evaluacion
        self.calificacion_final = calificacion_final
        self.porcentaje_final = porcentaje_final
        self.comentario = comentario
        self.faltas = faltas        
        self.incapacidad = incapacidad

class Detalle_Evaluacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    evaluacion_id = db.Column(db.Integer, db.ForeignKey('evaluacion.id'))
    aspecto_id = db.Column(db.Integer, db.ForeignKey('aspecto.id'))
    calificacion = db.Column(db.Float, nullable=False)
    
    def __init__(self, evaluacion_id, aspecto_id, calificacion):
        self.evaluacion_id = evaluacion_id
        self.aspecto_id = aspecto_id
        self.calificacion = calificacion

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    creador_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    asignado_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    estado = db.Column(db.Integer, nullable=False)
    categoria = db.Column(db.Integer, nullable=False)
    prioridad = db.Column(db.Integer, nullable=False)
    reparacion = db.Column(db.Text, nullable=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False)
    fecha_resolucion = db.Column(db.DateTime, nullable=True)

    def __init__(self, titulo, descripcion, creador_id, asignado_id, estado, categoria, prioridad, reparacion, fecha_creacion, fecha_resolucion):
        self.titulo = titulo
        self.descripcion = descripcion
        self.creador_id = creador_id
        self.asignado_id = asignado_id
        self.estado = estado
        self.prioridad = prioridad
        self.reparacion = reparacion
        self.categoria = categoria
        self.fecha_creacion = fecha_creacion
        self.fecha_resolucion = fecha_resolucion    

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    estacion_id = db.Column(db.Integer, db.ForeignKey('estacion.id'))
    activo = db.Column(db.Boolean, default=True)

    def __init__(self, nombre, precio, estacion_id, activo=True):
        self.nombre = nombre
        self.precio = precio
        self.estacion_id = estacion_id
        self.activo = activo

class Bomba(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_bomba = db.Column(db.String(100), nullable=False)
    estacion_id = db.Column(db.Integer, db.ForeignKey('estacion.id'))
    # El nombre en la BD sigue siendo 'producto', pero en Python se llama producto_id
    producto_id = db.Column('producto', db.Integer, db.ForeignKey('producto.id'))
    # Relación con Producto
    producto = db.relationship('Producto', backref='bombas')
    
    activo = db.Column(db.Boolean, default=True)

    def __init__(self, numero_bomba, estacion_id, producto_id, activo=True):
        self.numero_bomba = numero_bomba
        self.estacion_id = estacion_id
        self.producto_id = producto_id
        self.activo = activo

class LecturaManual(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_bomba = db.Column(db.Integer, db.ForeignKey('bomba.id'))
    fecha = db.Column(db.DateTime, nullable=False)
    turno = db.Column(db.Integer, nullable=False)
    estacion_id = db.Column(db.Integer, db.ForeignKey('estacion.id'))
    cantidad = db.Column(db.Numeric(18, 0, asdecimal=True), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))

    def __init__(self, numero_bomba, fecha, turno, estacion_id, cantidad, producto_id):
        self.numero_bomba = numero_bomba
        self.fecha = fecha
        self.turno = turno
        self.estacion_id = estacion_id
        self.cantidad = cantidad
        self.producto_id = producto_id

class TicketComentario(db.Model):
    __tablename__ = 'ticket_comentarios'
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    comentario = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __init__(self, ticket_id, usuario_id, comentario):
        self.ticket_id = ticket_id
        self.usuario_id = usuario_id
        self.comentario = comentario

class ComparativaTotal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estacion_id = db.Column(db.Integer, db.ForeignKey('estacion.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    turno = db.Column(db.Integer, nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    nexus_total = db.Column(db.Float, nullable=False, default=0.0)
    diferencia_lecturas = db.Column(db.Float, default=0.0)
    precio_unitario = db.Column(db.Float, default=0.0)
    diferencia_pesos = db.Column(db.Float, default=0.0)

    def __init__(self, estacion_id, fecha, turno, producto_id, nexus_total, diferencia_lecturas=0.0, precio_unitario=0.0, diferencia_pesos=0.0):
        self.estacion_id = estacion_id
        self.fecha = fecha
        self.turno = turno
        self.producto_id = producto_id
        self.nexus_total = nexus_total
        self.diferencia_lecturas = diferencia_lecturas
        self.precio_unitario = precio_unitario
        self.diferencia_pesos = diferencia_pesos

class Material(db.Model):
    __tablename__ = 'material'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    unidad = db.Column(db.String(50), nullable=False)
    activo = db.Column(db.Boolean, default=True)

    def __init__(self, nombre, unidad, activo=True):
        self.nombre = nombre
        self.unidad = unidad
        self.activo = activo

class EstacionMaterial(db.Model):
    __tablename__ = 'estacion_material'
    id = db.Column(db.Integer, primary_key=True)
    estacion_id = db.Column(db.Integer, db.ForeignKey('estacion.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    stock = db.Column(db.Float, nullable=False, default=0.0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=0.0)
    activo = db.Column(db.Boolean, default=True)

    # Relaciones
    estacion = db.relationship('Estacion', backref='materiales_asignados')
    material = db.relationship('Material', backref='estaciones_asignadas')

    __table_args__ = (
        db.UniqueConstraint('estacion_id', 'material_id', name='uq_estacion_material'),
    )

    def __init__(self, estacion_id, material_id, stock=0.0, stock_minimo=0.0, activo=True):
        self.estacion_id = estacion_id
        self.material_id = material_id
        self.stock = stock
        self.stock_minimo = stock_minimo
        self.activo = activo

class SolicitudMaterial(db.Model):
    __tablename__ = 'solicitudes_material'
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('estacion_material.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_solicitada = db.Column(db.DateTime, nullable=False, default=datetime.now)
    estado = db.Column(db.Enum('pendiente', 'aceptado', 'rechazado', 'cancelado', 'entregado','finalizado'), nullable=False, default='pendiente')
    comentario = db.Column(db.Text, nullable=True)

    # Relaciones
    estacion_material = db.relationship('EstacionMaterial', backref='solicitudes')
    usuario = db.relationship('Usuario', backref='solicitudes_material')

    def __init__(self, material_id, usuario_id, cantidad, estado='pendiente', comentario=None):
        self.material_id = material_id
        self.usuario_id = usuario_id
        self.cantidad = cantidad
        self.estado = estado
        self.comentario = comentario
        self.fecha_solicitada = datetime.now()