"""
VendeFlow - Schemas de Producto
===============================
Define la estructura y validación de datos para productos.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════════════
# SCHEMA PARA CREAR PRODUCTO
# ═══════════════════════════════════════════════════════════

class ProductCreate(BaseModel):
    """
    Schema para crear un nuevo producto.
    """
    
    sku: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Código único del producto (SKU)"
    )
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Nombre del producto"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=50000,  # HTML de Shopify puede ser largo
        description="Descripción del producto"
    )
    
    price: float = Field(
        ...,
        ge=0,
        description="Precio de venta"
    )
    
    cost: Optional[float] = Field(
        None,
        ge=0,
        description="Costo de adquisición"
    )
    
    quantity: int = Field(
        default=0,
        ge=0,
        description="Cantidad en stock"
    )
    
    min_stock: int = Field(
        default=5,
        ge=0,
        description="Cantidad mínima antes de alerta"
    )
    
    category: Optional[str] = Field(
        None,
        max_length=200,
        description="Categoría del producto"
    )
    
    brand: Optional[str] = Field(
        None,
        max_length=200,
        description="Marca del producto"
    )
    
    image_url: Optional[str] = Field(
        None,
        max_length=2000,  # URLs de Shopify/CDN pueden ser largas
        description="URL de la imagen del producto"
    )
    
    @field_validator('sku', 'name')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Elimina espacios al inicio y final."""
        return v.strip()
    
    @field_validator('sku')
    @classmethod
    def validate_sku(cls, v: str) -> str:
        """Valida formato del SKU."""
        v = v.upper()
        allowed = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
        if not all(c in allowed for c in v):
            raise ValueError('SKU solo puede contener letras, números, guiones y guiones bajos')
        return v


# ═══════════════════════════════════════════════════════════
# SCHEMA PARA ACTUALIZAR PRODUCTO
# ═══════════════════════════════════════════════════════════

class ProductUpdate(BaseModel):
    """
    Schema para actualizar un producto.
    Todos los campos son opcionales.
    """
    
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=50000)
    price: Optional[float] = Field(None, ge=0)
    cost: Optional[float] = Field(None, ge=0)
    quantity: Optional[int] = Field(None, ge=0)
    min_stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, max_length=200)
    brand: Optional[str] = Field(None, max_length=200)
    image_url: Optional[str] = Field(None, max_length=2000)
    is_active: Optional[bool] = None
    
    @field_validator('sku')
    @classmethod
    def validate_sku(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato del SKU si se proporciona."""
        if v is None:
            return v
        v = v.strip().upper()
        allowed = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
        if not all(c in allowed for c in v):
            raise ValueError('SKU solo puede contener letras, números, guiones y guiones bajos')
        return v


# ═══════════════════════════════════════════════════════════
# SCHEMA PARA RESPUESTA
# ═══════════════════════════════════════════════════════════

class ProductResponse(BaseModel):
    """
    Schema para respuesta de producto.
    """
    
    id: int
    user_id: int
    sku: str
    name: str
    description: Optional[str] = None
    price: float
    cost: Optional[float] = None
    quantity: int
    min_stock: int
    category: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    shopify_id: Optional[str] = None
    amazon_id: Optional[str] = None
    mercadolibre_id: Optional[str] = None
    is_active: bool
    is_low_stock: bool
    profit_margin: Optional[float] = None
    platforms_connected: List[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
# SCHEMA PARA LISTA DE PRODUCTOS
# ═══════════════════════════════════════════════════════════

class ProductList(BaseModel):
    """Schema para lista paginada de productos."""
    
    products: List[ProductResponse]
    total: int
    page: int
    per_page: int
    pages: int
