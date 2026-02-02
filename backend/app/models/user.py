"""
VendeFlow - Modelo de Usuario
=============================
Define la estructura de la tabla 'users' en la base de datos.

DIFERENCIAS CON REVÍSTETE:
- Usamos SQLAlchemy 2.0 (sintaxis Mapped más moderna)
- Sin roles buyer/seller (aquí todos son vendedores)
- Campos específicos para e-commerce manager
"""

from datetime import datetime
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class User(db.Model):
    """
    Modelo de Usuario para VendeFlow.
    
    Representa a un vendedor/e-commerce manager que usa la plataforma.
    """
    
    __tablename__ = 'users'
    
    # ═══════════════════════════════════════════════════════════
    # CAMPOS PRINCIPALES
    # ═══════════════════════════════════════════════════════════
    
    id: int = db.Column(db.Integer, primary_key=True)
    
    # Información de autenticación
    email: str = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash: str = db.Column(db.String(256), nullable=False)
    
    # Información personal
    first_name: str = db.Column(db.String(80), nullable=False)
    last_name: str = db.Column(db.String(80), nullable=False)
    
    # Información de la empresa/negocio
    company_name: Optional[str] = db.Column(db.String(100), nullable=True)
    phone: Optional[str] = db.Column(db.String(20), nullable=True)
    
    # Estado de la cuenta
    is_active: bool = db.Column(db.Boolean, default=True, nullable=False)
    is_verified: bool = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: Optional[datetime] = db.Column(db.DateTime, nullable=True)
    
    # ═══════════════════════════════════════════════════════════
    # RELACIONES (las agregaremos después)
    # ═══════════════════════════════════════════════════════════
    
    # products = db.relationship('Product', back_populates='user', cascade='all, delete-orphan')
    # platform_connections = db.relationship('PlatformConnection', back_populates='user')
    
    # ═══════════════════════════════════════════════════════════
    # MÉTODOS DE CONTRASEÑA
    # ═══════════════════════════════════════════════════════════
    
    def set_password(self, password: str) -> None:
        """
        Hashea y guarda la contraseña.
        
        NUNCA guardamos contraseñas en texto plano.
        Usamos werkzeug.security que implementa PBKDF2.
        
        Args:
            password: Contraseña en texto plano
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """
        Verifica si la contraseña es correcta.
        
        Args:
            password: Contraseña a verificar
            
        Returns:
            True si coincide, False si no
        """
        return check_password_hash(self.password_hash, password)
    
    # ═══════════════════════════════════════════════════════════
    # MÉTODOS DE SERIALIZACIÓN
    # ═══════════════════════════════════════════════════════════
    
    def to_dict(self) -> dict:
        """
        Convierte el usuario a diccionario.
        
        IMPORTANTE: Nunca incluimos password_hash en la respuesta.
        
        Returns:
            Diccionario con datos del usuario (sin contraseña)
        """
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'company_name': self.company_name,
            'phone': self.phone,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    # ═══════════════════════════════════════════════════════════
    # MÉTODOS ESPECIALES
    # ═══════════════════════════════════════════════════════════
    
    def __repr__(self) -> str:
        """Representación del objeto para debugging."""
        return f'<User {self.email}>'
