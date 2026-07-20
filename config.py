# config.py
import os
from urllib.parse import quote_plus

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    DB_USER = "eva_estaciones"
    DB_PASSWORD = "admin23"  
    DB_HOST = "127.0.0.1"
    DB_NAME = "pruebas_eva_estaciones"

    # Forzamos la cadena directa eliminando el os.environ.get
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    