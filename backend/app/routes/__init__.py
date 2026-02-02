"""
VendeFlow - Rutas de la API
===========================
Exporta todos los blueprints de rutas.
"""

from app.routes import auth_routes
from app.routes import inventory_routes

__all__ = ['auth_routes', 'inventory_routes']
