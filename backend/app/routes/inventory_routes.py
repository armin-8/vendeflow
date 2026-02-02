"""
VendeFlow - Rutas de Inventario
===============================
Endpoints para gestión de productos e inventario.

(Lo desarrollaremos en la siguiente fase)

ENDPOINTS PLANEADOS:
- GET    /api/inventory           - Listar productos
- POST   /api/inventory           - Crear producto
- GET    /api/inventory/<id>      - Obtener producto
- PUT    /api/inventory/<id>      - Actualizar producto
- DELETE /api/inventory/<id>      - Eliminar producto
- POST   /api/inventory/import    - Importar desde CSV/Excel
"""

from flask import Blueprint, jsonify

bp = Blueprint('inventory', __name__, url_prefix='/api/inventory')


@bp.route('/', methods=['GET'])
def get_inventory():
    """
    Placeholder - Retorna mensaje de que está en desarrollo.
    """
    return jsonify({
        'message': 'Módulo de inventario en desarrollo',
        'status': 'coming_soon'
    }), 200
