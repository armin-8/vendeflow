"""
VendeFlow - Modelo de Usuario
=============================
Define la estructura de la tabla 'users' en la base de datos.
"""

from datetime import datetime
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class User(db.Model):
    __tablename__ = 'users'
    
    # ═══════════════════════════════════════════════════════════
    # CAMPOS PRINCIPALES
    # ═══════════════════════════════════════════════════════════
    
    id: int = db.Column(db.Integer, primary_key=True)
    
    email: str = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash: str = db.Column(db.String(256), nullable=False)
    
    first_name: str = db.Column(db.String(80), nullable=False)
    last_name: str = db.Column(db.String(80), nullable=False)
    
    company_name: Optional[str] = db.Column(db.String(100), nullable=True)
    phone: Optional[str] = db.Column(db.String(20), nullable=True)
    
    is_active: bool = db.Column(db.Boolean, default=True, nullable=False)
    is_verified: bool = db.Column(db.Boolean, default=False, nullable=False)
    
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: Optional[datetime] = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self) -> dict:
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
    
    def __repr__(self) -> str:
        return f'<User {self.email}>'
