"""
VendeFlow - Modelo de Conexión de Plataforma
=============================================

Guarda las credenciales de conexión con plataformas externas
(Shopify, Amazon, Mercado Libre) por usuario.

SEGURIDAD:
----------
Los tokens se encriptan automáticamente al guardar y se
desencriptan al leer. La BD nunca contiene tokens en texto plano.
"""

from datetime import datetime, timedelta
from app import db
from app.utils.encryption import encrypt_token, decrypt_token, is_encrypted


class PlatformConnection(db.Model):
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

    # ─── TOKENS ENCRIPTADOS ────────────────────────────────────
    # Estos campos guardan los tokens ENCRIPTADOS en la BD.
    # NUNCA accedas directamente a estos campos desde fuera del modelo.
    # Usa las propiedades access_token y refresh_token en su lugar.
    # ───────────────────────────────────────────────────────────
    _access_token = db.Column('access_token', db.Text, nullable=False)
    _refresh_token = db.Column('refresh_token', db.Text, nullable=True)

    # Scope/permisos otorgados
    scope = db.Column(db.String(500), nullable=True)

    # ID del usuario en la plataforma externa (ej: user_id de ML)
    external_user_id = db.Column(db.String(100), nullable=True)

    # Fecha de expiración del access_token (solo ML)
    token_expires_at = db.Column(db.DateTime, nullable=True)

    # ═══════════════════════════════════════════════════════════
    # ESTADO Y TIMESTAMPS
    # ═══════════════════════════════════════════════════════════

    is_active = db.Column(db.Boolean, default=True)
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # ═══════════════════════════════════════════════════════════
    # RELACIONES
    # ═══════════════════════════════════════════════════════════

    user = db.relationship('User', backref=db.backref('connections', lazy=True))

    # ═══════════════════════════════════════════════════════════
    # CONSTRAINT
    # ═══════════════════════════════════════════════════════════

    __table_args__ = (
        db.UniqueConstraint('user_id', 'platform', 'store_name', name='unique_user_platform_store'),
    )

    # ═══════════════════════════════════════════════════════════
    # PROPIEDADES — Encriptación/Desencriptación automática
    # ═══════════════════════════════════════════════════════════
    #
    # ¿POR QUÉ PROPIEDADES EN VEZ DE COLUMNAS DIRECTAS?
    # ---------------------------------------------------
    # Con @property podemos interceptar los get/set del token.
    # Cuando alguien hace:
    #   connection.access_token = "shpss_abc123"   → encripta automáticamente
    #   token = connection.access_token             → desencripta automáticamente
    #
    # El resto del código (services, routes) no necesita saber
    # que los tokens están encriptados — todo es transparente.

    @property
    def access_token(self) -> str:
        """Desencripta y retorna el access_token."""
        if not self._access_token:
            return self._access_token
        return decrypt_token(self._access_token)

    @access_token.setter
    def access_token(self, value: str):
        """Encripta el access_token antes de guardarlo."""
        if not value:
            self._access_token = value
            return
        # Solo encriptar si no está ya encriptado
        if is_encrypted(value):
            self._access_token = value
        else:
            self._access_token = encrypt_token(value)

    @property
    def refresh_token(self) -> str:
        """Desencripta y retorna el refresh_token."""
        if not self._refresh_token:
            return self._refresh_token
        return decrypt_token(self._refresh_token)

    @refresh_token.setter
    def refresh_token(self, value: str):
        """Encripta el refresh_token antes de guardarlo."""
        if not value:
            self._refresh_token = value
            return
        if is_encrypted(value):
            self._refresh_token = value
        else:
            self._refresh_token = encrypt_token(value)

    # ═══════════════════════════════════════════════════════════
    # MÉTODO HELPER: ¿El token de ML está por vencer?
    # ═══════════════════════════════════════════════════════════

    @property
    def is_token_expired(self) -> bool:
        """
        Verifica si el access_token de ML ya expiró.
        Incluye un margen de 5 minutos para refrescar antes de que venza.
        """
        if self.platform != 'mercadolibre':
            return False
        if not self.token_expires_at:
            return True
        return datetime.utcnow() >= (self.token_expires_at - timedelta(minutes=5))

    def __repr__(self):
        return f'<PlatformConnection {self.platform}:{self.store_name}>'

    def to_dict(self):
        """Convierte a diccionario — NUNCA expone los tokens."""
        return {
            'id': self.id,
            'platform': self.platform,
            'store_name': self.store_name,
            'is_active': self.is_active,
            'external_user_id': self.external_user_id,
            'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
            'connected_at': self.connected_at.isoformat() if self.connected_at else None,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
        }
