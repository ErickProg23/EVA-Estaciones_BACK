# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, Usuario
from config import Config
from routes.usuarios import usuarios_bp
from routes.estaciones import estacion_bp
from routes.rol import rol_bp
from routes.puestos import puestos_bp
from routes.personal import personal_bp
from routes.aspectos import aspecto_bp
from routes.evaluacion import evaluacion_bp
from routes.tickets import tickets_bp
from routes.reportes import reportes_bp
from routes.dashboard import dashboard_bp
from routes.productos import productos_bp
from routes.bombas import bombas_bp
from routes.lecturas_manuales import lecturas_manuales
from routes.materiales import materiales_bp
from routes.solicitudes_material import solicitudes_bp
from routes.configuraciones_litros import configuraciones_litros_bp



app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
CORS(app, origins=["http://localhost:8080"])  # Puerto de Vue

app.register_blueprint(usuarios_bp)
app.register_blueprint(estacion_bp)
app.register_blueprint(rol_bp)
app.register_blueprint(puestos_bp)
app.register_blueprint(personal_bp)
app.register_blueprint(aspecto_bp)
app.register_blueprint(evaluacion_bp)
app.register_blueprint(tickets_bp)
app.register_blueprint(reportes_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(productos_bp)
app.register_blueprint(bombas_bp)
app.register_blueprint(lecturas_manuales)
app.register_blueprint(materiales_bp)
app.register_blueprint(solicitudes_bp)
app.register_blueprint(configuraciones_litros_bp)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5005, debug=True)
