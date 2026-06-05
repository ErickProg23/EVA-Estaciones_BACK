# config.py
import os
from urllib.parse import quote_plus

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    DB_USER = "evaluev2_admin"
    DB_PASSWORD = quote_plus('rMi;U?WABw!f^0@O')  
    DB_HOST = "127.0.0.1"
    DB_NAME = "evaluev2_eva_estaciones_produccion"

    # Forzamos la cadena directa eliminando el os.environ.get
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    