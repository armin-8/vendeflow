"""
VendeFlow - Modelo de Producto
==============================
Define la estructura de la tabla 'products' en la base de datos.

Este es el modelo central del MVP - representa los productos
del inventario del usuario.
"""

from datetime import datetime
from typing import Optional

from app import db


class Product(db.Model):
    """
    Modelo de Producto para VendeFlow.
    
    Representa un producto en el inventario del usuario.
    Puede estar conectado a Shopify, Amazon y/o Mercado Libre.
    """
    
    __tablename__ = 'products'
    
    # ═══════════════════════════════════════════════════════════
    # CAMPOS PRINCIPALES
    # ═══════════════════════════════════════════════════════════
    
    id: int = db.Column(db.Integer, primary_key=True)
    
    # Relación con usuario (cada producto pertenece a un usuario)
    user_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Información básica del producto
    sku: str = db.Column(db.String(50), nullable=False)  # Código único del producto
    name: str = db.Column(db.String(200), nullable=False)
    description: Optional[str] = db.Column(db.Text, nullable=True)
    
    # Precio y stock
    price: float = db.Column(db.Float, nullable=False, default=0.0)
    cost: Optional[float] = db.Column(db.Float, nullable=True)  # Costo de adquisición
    quantity: int = db.Column(db.Integer, nullable=False, default=0)
    min_stock: int = db.Column(db.Integer, nullable=False, default=5)  # Alerta de stock bajo
    
    # Información adicional
    category: Optional[str] = db.Column(db.String(100), nullable=True)
    brand: Optional[str] = db.Column(db.String(100), nullable=True)
    image_url: Optional[str] = db.Column(db.String(500), nullable=True)
    
    # ═══════════════════════════════════════════════════════════
    # IDs DE PLATAFORMAS EXTERNAS
    # ═══════════════════════════════════════════════════════════
    # Cuando sincronicemos con las plataformas, guardaremos sus IDs aquí
    
    shopify_id: Optional[str] = db.Column(db.String(100), nullable=True)
    amazon_id: Optional[str] = db.Column(db.String(100), nullable=True)
    mercadolibre_id: Optional[str] = db.Column(db.String(100), nullable=True)
    
    # ═══════════════════════════════════════════════════════════
    # ESTADO Y TIMESTAMPS
    # ═══════════════════════════════════════════════════════════
    
    is_active: bool = db.Column(db.Boolean, default=True, nullable=False)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at: Optional[datetime] = db.Column(db.DateTime, nullable=True)
    
    # ═══════════════════════════════════════════════════════════
    # RELACIONES
    # ═══════════════════════════════════════════════════════════
    
    # Relación con User
    user = db.relationship('User', backref=db.backref('products', lazy='dynamic'))
    
    # ═══════════════════════════════════════════════════════════
    # ÍNDICES Y CONSTRAINTS
    # ═══════════════════════════════════════════════════════════
    
    # SKU debe ser único por usuario
    __table_args__ = (
        db.UniqueConstraint('user_id', 'sku', name='unique_user_sku'),
    )
    
    # ═══════════════════════════════════════════════════════════
    # MÉTODOS
    # ═══════════════════════════════════════════════════════════
    
    @property
    def is_low_stock(self) -> bool:
        """Verifica si el producto tiene stock bajo."""
        return self.quantity <= self.min_stock
    
    @property
    def profit_margin(self) -> Optional[float]:
        """Calcula el margen de ganancia si hay costo definido."""
        if self.cost and self.cost > 0:
            return ((self.price - self.cost) / self.price) * 100
        return None
    
    @property
    def platforms_connected(self) -> list:
        """Retorna lista de plataformas donde está el producto."""
        platforms = []
        if self.shopify_id:
            platforms.append('shopify')
        if self.amazon_id:
            platforms.append('amazon')
        if self.mercadolibre_id:
            platforms.append('mercadolibre')
        return platforms
    
    def to_dict(self) -> dict:
        """
        Convierte el producto a diccionario.
        
        Returns:
            Diccionario con todos los datos del producto
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sku': self.sku,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'cost': self.cost,
            'quantity': self.quantity,
            'min_stock': self.min_stock,
            'category': self.category,
            'brand': self.brand,
            'image_url': self.image_url,
            'shopify_id': self.shopify_id,
            'amazon_id': self.amazon_id,
            'mercadolibre_id': self.mercadolibre_id,
            'is_active': self.is_active,
            'is_low_stock': self.is_low_stock,
            'profit_margin': self.profit_margin,
            'platforms_connected': self.platforms_connected,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None
        }
    
    def __repr__(self) -> str:
        """Representación del objeto para debugging."""
        return f'<Product {self.sku}: {self.name}>'
