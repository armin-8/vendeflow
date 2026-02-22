"""
VendeFlow - Modelo de Conexión de Plataforma
=============================================

Guarda las credenciales de conexión con plataformas externas
(Shopify, Amazon, Mercado Libre) por usuario.

¿POR QUÉ UN MODELO SEPARADO?
-----------------------------
- Cada usuario puede conectar múltiples tiendas
- Guardamos el access_token de forma segura
- Podemos rastrear cuándo se conectó y sincronizó
"""

from datetime import datetime
from app import db


class PlatformConnection(db.Model):
    """
    Modelo para guardar conexiones con plataformas externas.
    
    Un usuario puede tener múltiples conexiones (varias tiendas).
    """
    
    __tablename__ = 'platform_connections'
    
    # ═══════════════════════════════════════════════════════════
    # CAMPOS PRINCIPALES
    # ═══════════════════════════════════════════════════════════
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Tipo de plataforma: 'shopify', 'amazon', 'mercadolibre'
    platform = db.Column(db.String(50), nullable=False)
    
    # Nombre/identificador de la tienda (ej: 'ra-outdoorstore')
    store_name = db.Column(db.String(255), nullable=False)
    
    # Access Token (encriptado en producción)
    access_token = db.Column(db.String(500), nullable=False)
    
    # Scope/permisos otorgados
    scope = db.Column(db.String(500), nullable=True)
    
    # ═══════════════════════════════════════════════════════════
    # ESTADO
    # ═══════════════════════════════════════════════════════════
    
    is_active = db.Column(db.Boolean, default=True)
    
    # ═══════════════════════════════════════════════════════════
    # TIMESTAMPS
    # ═══════════════════════════════════════════════════════════
    
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_synced_at = db.Column(db.DateTime, nullable=True)
    
    # ═══════════════════════════════════════════════════════════
    # RELACIONES
    # ═══════════════════════════════════════════════════════════
    
    user = db.relationship('User', backref=db.backref('connections', lazy=True))
    
    # ═══════════════════════════════════════════════════════════
    # CONSTRAINT: Un usuario no puede conectar la misma tienda dos veces
    # ═══════════════════════════════════════════════════════════
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'platform', 'store_name', name='unique_user_platform_store'),
    )
    
    def __repr__(self):
        return f'<PlatformConnection {self.platform}:{self.store_name}>'
    
    def to_dict(self):
        """Convierte a diccionario (sin exponer el token)."""
        return {
            'id': self.id,
            'platform': self.platform,
            'store_name': self.store_name,
            'is_active': self.is_active,
            'connected_at': self.connected_at.isoformat() if self.connected_at else None,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
        }
