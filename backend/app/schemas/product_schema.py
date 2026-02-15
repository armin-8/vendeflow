"""
VendeFlow - Schemas de Producto
===============================
Define la estructura y validación de datos para productos.

RECUERDA:
- Pydantic valida automáticamente los datos
- Si algo no cumple, lanza error descriptivo
- Evita validaciones manuales repetitivas
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
    
    Campos requeridos: sku, name, price
    Campos opcionales: description, cost, quantity, etc.
    """
    
    sku: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Código único del producto (SKU)"
    )
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Nombre del producto"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=5000,
        description="Descripción del producto"
    )
    
    price: float = Field(
        ...,
        ge=0,  # greater or equal to 0
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
        max_length=100,
        description="Categoría del producto"
    )
    
    brand: Optional[str] = Field(
        None,
        max_length=100,
        description="Marca del producto"
    )
    
    image_url: Optional[str] = Field(
        None,
        max_length=500,
        description="URL de la imagen del producto"
    )
    
    # Validador para limpiar espacios
    @field_validator('sku', 'name')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Elimina espacios al inicio y final."""
        return v.strip()
    
    # Validador para SKU (solo alfanuméricos y guiones)
    @field_validator('sku')
    @classmethod
    def validate_sku(cls, v: str) -> str:
        """Valida formato del SKU."""
        v = v.upper()  # Convertir a mayúsculas
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
    
    Todos los campos son opcionales porque el usuario
    puede querer actualizar solo algunos.
    """
    
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    price: Optional[float] = Field(None, ge=0)
    cost: Optional[float] = Field(None, ge=0)
    quantity: Optional[int] = Field(None, ge=0)
    min_stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(None, max_length=500)
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
        """Configuración del schema."""
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
