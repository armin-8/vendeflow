"""
VendeFlow - Configuración de la Aplicación
==========================================
Este archivo centraliza toda la configuración del backend.
Usa variables de entorno para valores sensibles.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


class Config:
    """Configuración base compartida por todos los entornos."""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-cambiar')
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-dev-secret-cambiar')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # True para ver queries SQL en consola
    
    # CORS
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')


class DevelopmentConfig(Config):
    """Configuración para desarrollo local."""
    
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'sqlite:///vendeflow_dev.db'
    )
    SQLALCHEMY_ECHO = True  # Ver queries en desarrollo


class ProductionConfig(Config):
    """Configuración para producción."""
    
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # En producción, asegurar que las claves estén configuradas
    @classmethod
    def init_app(cls, app):
        # Validar que las variables críticas existan
        required_vars = ['SECRET_KEY', 'JWT_SECRET_KEY', 'DATABASE_URL']
        for var in required_vars:
            if not os.getenv(var):
                raise ValueError(f"Variable de entorno {var} es requerida en producción")


class TestingConfig(Config):
    """Configuración para tests."""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///vendeflow_test.db'


# Diccionario para seleccionar configuración
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Obtiene la configuración según el entorno."""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
