"""
VendeFlow - Helper para registrar logs de sincronización
=========================================================

Centraliza la creación de logs para que los endpoints de sync/import
no tengan que repetir la misma lógica.

Uso desde cualquier route:
    from app.utils.log_helper import log_sync
    log_sync(user_id=1, platform='shopify', action='sync',
             status='success', items_ok=5, items_failed=0)
"""

from app import db
from app.models.sync_log import SyncLog


def log_sync(user_id: int, platform: str, action: str, status: str,
             sku: str = None, items_ok: int = 0, items_failed: int = 0,
             error_detail: str = None):
    """
    Registra una operación de sincronización o importación.

    Args:
        user_id:      ID del usuario que hizo la operación
        platform:     'shopify', 'mercadolibre', 'amazon'
        action:       'sync' o 'import'
        status:       'success' o 'error'
        sku:          SKU específico (None si fue masivo)
        items_ok:     Productos procesados correctamente
        items_failed: Productos que fallaron
        error_detail: Mensaje de error si hubo
    """
    try:
        log = SyncLog(
            user_id=user_id,
            platform=platform,
            action=action,
            status=status,
            sku=sku,
            items_ok=items_ok,
            items_failed=items_failed,
            error_detail=error_detail
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        # Los logs nunca deben romper el flujo principal
        # Si falla guardar el log, solo lo imprimimos
        db.session.rollback()
        print(f"[LOG ERROR] No se pudo guardar log: {e}")
