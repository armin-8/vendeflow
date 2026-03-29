"""
VendeFlow - Rutas de Logs de Sincronización
=============================================

ENDPOINTS:
- GET /api/logs              → Historial de sincronizaciones del usuario
- GET /api/logs/stats        → Estadísticas de sincronización
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.sync_log import SyncLog

bp = Blueprint('logs', __name__, url_prefix='/api/logs')


# ═══════════════════════════════════════════════════════════
# ENDPOINT: LISTAR LOGS
# ═══════════════════════════════════════════════════════════

@bp.route('', methods=['GET'])
@jwt_required()
def get_logs():
    """
    Retorna el historial de sincronizaciones del usuario.

    Query params opcionales:
        platform: filtrar por 'shopify' o 'mercadolibre'
        action:   filtrar por 'sync' o 'import'
        status:   filtrar por 'success' o 'error'
        limit:    número de logs (default: 50, max: 200)
    """
    user_id = get_jwt_identity()

    platform = request.args.get('platform')
    action = request.args.get('action')
    status = request.args.get('status')
    limit = min(request.args.get('limit', 50, type=int), 200)

    query = SyncLog.query.filter_by(user_id=int(user_id))

    if platform:
        query = query.filter_by(platform=platform)
    if action:
        query = query.filter_by(action=action)
    if status:
        query = query.filter_by(status=status)

    logs = query.order_by(SyncLog.created_at.desc()).limit(limit).all()

    return jsonify({
        'logs': [log.to_dict() for log in logs],
        'total': len(logs)
    }), 200


# ═══════════════════════════════════════════════════════════
# ENDPOINT: ESTADÍSTICAS DE LOGS
# ═══════════════════════════════════════════════════════════

@bp.route('/stats', methods=['GET'])
@jwt_required()
def get_log_stats():
    """
    Retorna estadísticas de sincronización del usuario.

    Útil para el dashboard — saber de un vistazo cuántas
    sincronizaciones exitosas/fallidas hay por plataforma.
    """
    user_id = get_jwt_identity()

    all_logs = SyncLog.query.filter_by(user_id=int(user_id)).all()

    # Calcular estadísticas
    total = len(all_logs)
    success = sum(1 for l in all_logs if l.status == 'success')
    errors = sum(1 for l in all_logs if l.status == 'error')
    total_items_ok = sum(l.items_ok for l in all_logs)
    total_items_failed = sum(l.items_failed for l in all_logs)

    # Por plataforma
    by_platform = {}
    for log in all_logs:
        p = log.platform
        if p not in by_platform:
            by_platform[p] = {'total': 0, 'success': 0, 'errors': 0}
        by_platform[p]['total'] += 1
        if log.status == 'success':
            by_platform[p]['success'] += 1
        else:
            by_platform[p]['errors'] += 1

    # Último log por plataforma
    last_sync = {}
    for log in all_logs:
        p = log.platform
        if p not in last_sync:
            last_sync[p] = log.created_at.isoformat() if log.created_at else None

    return jsonify({
        'stats': {
            'total': total,
            'success': success,
            'errors': errors,
            'total_items_ok': total_items_ok,
            'total_items_failed': total_items_failed,
            'by_platform': by_platform,
            'last_sync': last_sync
        }
    }), 200
