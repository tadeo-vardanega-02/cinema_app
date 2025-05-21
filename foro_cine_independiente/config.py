import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'esta-es-una-clave-secreta-muy-segura'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'foro.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
