"""
Script para vincular un producto de VendeFlow con su publicación de Mercado Libre.
Uso: python vincular_ml.py
"""
from app import create_app, db
from app.models.product import Product

app = create_app()

with app.app_context():
    sku = 'H8-1016-PROT'
    ml_id = 'MLM1573942576'
    
    p = Product.query.filter_by(sku=sku).first()
    
    if not p:
        print(f"❌ No se encontró el producto con SKU: {sku}")
    else:
        p.mercadolibre_id = ml_id
        db.session.commit()
        print(f"✅ Producto vinculado correctamente:")
        print(f"   SKU:            {p.sku}")
        print(f"   Nombre:         {p.name}")
        print(f"   Stock:          {p.quantity}")
        print(f"   Mercado Libre:  {p.mercadolibre_id}")
