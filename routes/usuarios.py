# routes/usuarios.py
from flask import Blueprint, request, jsonify
from models import db, Usuario, Rol, Estacion
import jwt, datetime

SECRET_KEY = 'mi_clave_secreta_segura'  # Usa una más segura y guárdala como variable de entorno


usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')


    usuario = Usuario.query.filter_by(usuario=username).first()

    if not usuario or usuario.password != password:
        return jsonify({'success': False, 'message': 'Credenciales incorrectas'}), 401

    if not usuario.activo:
        return jsonify({'success': False, 'message': 'Usuario inactivo'}), 403

    if usuario.rol and hasattr(usuario.rol, 'activo') and not usuario.rol.activo:
        return jsonify({'success': False, 'message': 'Rol inactivo'}), 403

    token = jwt.encode({
        'user_id': usuario.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }, SECRET_KEY, algorithm='HS256')

    return jsonify({'success': True, 'message': 'Login exitoso', 'token': token, 'estacion_id': usuario.estacion_id, 'rol_id': usuario.rol_id, 'usuario_id': usuario.id, 'nombre': usuario.nombre, 'rol_nombre': usuario.rol.nombre})

@usuarios_bp.route('/getUsuarios', methods=['GET'])
def getUsuarios():
    try:
        usuarios = Usuario.query.all()
        usuarios_data = []
        for u in usuarios:
            usuarios_data.append({
                'id': u.id,
                'nombre': u.nombre,
                'usuario': u.usuario,
                'password': u.password,
                'activo': u.activo,
                'rol_id': u.rol_id,
                'correo': u.correo,
                'rol': {
                    'id': u.rol.id,
                    'nombre': u.rol.nombre
                } if u.rol else None,
                'estacion_id': u.estacion_id,
                'estacion': {
                    'id': u.estacion.id,
                    'nombre': u.estacion.nombre
                } if u.estacion else None
            })
        return jsonify({'success': True, 'usuarios': usuarios_data})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al obtener los usuarios', 'error': str(e)}), 500


@usuarios_bp.route('/newUsuario', methods=['POST'])
def newUsuario():
    data = request.get_json()
    print(data)
    try:
        # Obtener los datos del usuario del JSON
        nombre = data.get('nombre')
        usuario = data.get('usuario')
        password = data.get('password')
        activo = data.get('activo')
        rol_id = data.get('rol_id')
        estacion_id = data.get('estacion_id')
        correo = data.get('correo')

        # Validar que todos los campos obligatorios estén presentes
        if nombre is None or usuario is None or password is None or rol_id is None or estacion_id is None or activo is None or correo is None:
            return jsonify({'success': False, 'message': 'Faltan datos obligatorios'}), 400


        # Validar que el rol_id exista
        rol = Rol.query.get(rol_id)
        if not rol:
            return jsonify({'success': False, 'message': 'El rol_id no existe'}), 400

        # Validar que el estacion_id exista
        estacion = Estacion.query.get(estacion_id)
        if not estacion:
            return jsonify({'success': False, 'message': 'El estacion_id no existe'}), 400

        # Crear un nuevo usuario
        nuevo_usuario = Usuario(
            nombre=nombre,
            usuario=usuario,
            password=password,
            activo=activo,
            rol_id=rol_id,
            estacion_id=estacion_id,
            correo=correo
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Usuario creado exitosamente'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al procesar la solicitud', 'error': str(e)}), 500

@usuarios_bp.route('/updateUsuario/<int:id>', methods=['PUT'])
def updateUsuario(id):
    try:
        usuario = Usuario.query.get(id)
        if not usuario:
            return jsonify({'success': False, 'message': 'El usuario no existe'}), 400

        data = request.get_json()

        usuario.nombre = data.get('nombre', usuario.nombre)
        usuario.usuario = data.get('usuario', usuario.usuario)
        usuario.rol_id = data.get('rol_id', usuario.rol_id)
        usuario.estacion_id = data.get('estacion_id', usuario.estacion_id)
        usuario.activo = data.get('activo', usuario.activo)
        usuario.correo = data.get('correo', usuario.correo)
        usuario.activo = data.get('activo', usuario.activo)

        db.session.commit()  # <--- ESTO es lo que guarda los cambios en la base de datos

        return jsonify({'success': True, 'message': 'Usuario actualizado correctamente'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al procesar la solicitud', 'error': str(e)}), 500
