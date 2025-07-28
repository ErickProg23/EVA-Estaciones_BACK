# config.py
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:admin123@localhost/eva-estaciones'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
