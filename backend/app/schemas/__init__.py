"""
VendeFlow - Schemas de Validación
=================================
Exporta todos los schemas desde un solo lugar.
"""

from app.schemas.user_schema import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate
)

from app.schemas.product_schema import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductList
)

__all__ = [
    # User schemas
    'UserCreate',
    'UserLogin', 
    'UserResponse',
    'UserUpdate',
    # Product schemas
    'ProductCreate',
    'ProductUpdate',
    'ProductResponse',
    'ProductList'
]
