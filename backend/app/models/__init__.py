"""
VendeFlow - Modelos de Base de Datos
====================================
Exporta todos los modelos desde un solo lugar.
"""

from app.models.user import User

# Cuando agreguemos más modelos, los importamos aquí:
# from app.models.product import Product
# from app.models.inventory import Inventory

__all__ = ['User']
