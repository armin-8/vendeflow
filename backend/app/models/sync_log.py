"""
VendeFlow - Modelo de Log de Sincronización
=============================================

Registra cada operación de sync/import para trazabilidad completa.

¿POR QUÉ ES CRÍTICO EN PRODUCCIÓN?
------------------------------------
Sin logs: cliente dice "mi stock no se actualizó" → no podemos saber qué pasó
Con logs: vemos exactamente qué sincronizó, cuándo, con qué resultado

EJEMPLO DE LOG:
---------------
user_id=1 | platform=shopify | action=sync | sku=H8-1016-PROT | 
status=success | items_ok=1 | items_failed=0 | 2026-03-29 15:30:00
"""

from datetime import datetime
from app import db


class SyncLog(db.Model):
    """
    Registro de operaciones de sincronización e importación.
    """

    __tablename__ = 'sync_logs'

    # ═══════════════════════════════════════════════════════════
    # CAMPOS PRINCIPALES
    # ═══════════════════════════════════════════════════════════

    id = db.Column(db.Integer, primary_key=True)

    # ¿Quién hizo la operación?
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # ¿En qué plataforma? 'shopify', 'mercadolibre', 'amazon'
    platform = db.Column(db.String(50), nullable=False)

    # ¿Qué operación? 'sync' (VendeFlow → plataforma) o 'import' (plataforma → VendeFlow)
    action = db.Column(db.String(20), nullable=False)

    # ¿Resultado? 'success' o 'error'
    status = db.Column(db.String(20), nullable=False)

    # SKU específico (si fue sync por SKU) o None (si fue masivo)
    sku = db.Column(db.String(100), nullable=True)

    # Contadores
    items_ok = db.Column(db.Integer, default=0)      # Productos procesados correctamente
    items_failed = db.Column(db.Integer, default=0)  # Productos que fallaron

    # Detalle del error (si hubo)
    error_detail = db.Column(db.Text, nullable=True)

    # ═══════════════════════════════════════════════════════════
    # TIMESTAMPS
    # ═══════════════════════════════════════════════════════════

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ═══════════════════════════════════════════════════════════
    # RELACIONES
    # ═══════════════════════════════════════════════════════════

    user = db.relationship('User', backref=db.backref('sync_logs', lazy='dynamic'))

    def __repr__(self):
        return f'<SyncLog {self.platform}:{self.action}:{self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'action': self.action,
            'status': self.status,
            'sku': self.sku,
            'items_ok': self.items_ok,
            'items_failed': self.items_failed,
            'error_detail': self.error_detail,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
