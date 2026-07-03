"""
VendeFlow - Rutas de Inteligencia Artificial
=============================================

ENDPOINTS:
- GET  /api/ai/status              → Verificar que Ollama está corriendo
- POST /api/ai/generate-listing    → Genera contenido multi-plataforma
- POST /api/ai/improve-description → Mejora una descripción existente
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.services.ai_service import ai_service

bp = Blueprint('ai', __name__, url_prefix='/api/ai')


# ═══════════════════════════════════════════════════════════
# ENDPOINT: VERIFICAR ESTADO DE OLLAMA
# ═══════════════════════════════════════════════════════════

@bp.route('/status', methods=['GET'])
@jwt_required()
def get_status():
    """Verifica que Ollama está corriendo y el modelo disponible."""
    success, message = ai_service.health_check()
    return jsonify({
        'available': success,
        'message': message,
        'model': ai_service.MODEL
    }), 200 if success else 503


# ═══════════════════════════════════════════════════════════
# ENDPOINT: GENERAR LISTING MULTI-PLATAFORMA
# ═══════════════════════════════════════════════════════════

@bp.route('/generate-listing', methods=['POST'])
@jwt_required()
def generate_listing():
    """
    Genera contenido optimizado para múltiples plataformas con Ollama.

    BODY:
    {
        "name": "Filtro Polar Pro Hero 8",
        "description": "Filtro para buceo...",
        "category": "Fotografía y Video",
        "brand": "Polar Pro",
        "price": 899.00,
        "platforms": ["shopify", "mercadolibre"]
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'Se requiere JSON en el request'}), 400

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'El nombre del producto es requerido'}), 400

    valid_platforms = ['shopify', 'mercadolibre', 'amazon']
    platforms = data.get('platforms', valid_platforms)
    platforms = [p for p in platforms if p in valid_platforms]

    if not platforms:
        return jsonify({'success': False, 'error': 'Selecciona al menos una plataforma válida'}), 400

    try:
        listing = ai_service.generate_listing(
            name=name,
            description=data.get('description', ''),
            category=data.get('category', ''),
            brand=data.get('brand', ''),
            price=float(data.get('price', 0)),
            platforms=platforms
        )

        return jsonify({'success': True, 'listing': listing}), 200

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error inesperado: {str(e)}'}), 500


# ═══════════════════════════════════════════════════════════
# ENDPOINT: MEJORAR DESCRIPCIÓN EXISTENTE
# ═══════════════════════════════════════════════════════════

@bp.route('/improve-description', methods=['POST'])
@jwt_required()
def improve_description():
    """
    Mejora una descripción existente para una plataforma específica.

    BODY:
    {
        "description": "Texto actual...",
        "platform": "mercadolibre"
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'Se requiere JSON en el request'}), 400

    description = data.get('description', '').strip()
    platform = data.get('platform', '').strip().lower()

    if not description:
        return jsonify({'success': False, 'error': 'La descripción es requerida'}), 400

    if platform not in ['shopify', 'mercadolibre', 'amazon']:
        return jsonify({'success': False, 'error': 'Plataforma inválida'}), 400

    try:
        improved = ai_service.improve_description(description, platform)
        return jsonify({'success': True, 'description': improved}), 200

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error inesperado: {str(e)}'}), 500
