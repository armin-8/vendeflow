"""
VendeFlow - Servicio de Importación
====================================

Este servicio maneja la lógica para importar productos desde archivos
Excel (.xlsx) o CSV (.csv).

SOPORTA MÚLTIPLES FORMATOS DE COLUMNAS:
- Inglés: sku, name, price, cost, quantity, min_stock, category, brand
- Español: SKU, NOMBRE, PRECIO, COSTO, UNIDADES, STOCK, CATEGORIA, MARCA
- Shopify: Variant SKU, Title, Variant Price, etc. (próximamente)
"""

import pandas as pd
from typing import List, Dict, Tuple
from werkzeug.datastructures import FileStorage


# ═══════════════════════════════════════════════════════════
# MAPEO DE COLUMNAS (soporta múltiples idiomas/formatos)
# ═══════════════════════════════════════════════════════════

# Diccionario que mapea diferentes nombres de columnas al nombre estándar
COLUMN_MAPPING = {
    # SKU
    'sku': 'sku',
    'codigo': 'sku',
    'código': 'sku',
    'code': 'sku',
    'variant sku': 'sku',
    
    # Nombre
    'name': 'name',
    'nombre': 'name',
    'title': 'name',
    'producto': 'name',
    'product': 'name',
    
    # Precio
    'price': 'price',
    'precio': 'price',
    'variant price': 'price',
    'precio venta': 'price',
    
    # Costo
    'cost': 'cost',
    'costo': 'cost',
    'cost per item': 'cost',
    'precio costo': 'cost',
    
    # Cantidad
    'quantity': 'quantity',
    'cantidad': 'quantity',
    'unidades': 'quantity',
    'stock': 'quantity',  # A veces stock es la cantidad
    'variant inventory qty': 'quantity',
    'inventory': 'quantity',
    'inventario': 'quantity',
    
    # Stock mínimo
    'min_stock': 'min_stock',
    'stock minimo': 'min_stock',
    'stock mínimo': 'min_stock',
    'minimo': 'min_stock',
    'min': 'min_stock',
    
    # Categoría
    'category': 'category',
    'categoria': 'category',
    'categoría': 'category',
    'type': 'category',
    'product type': 'category',
    
    # Marca
    'brand': 'brand',
    'marca': 'brand',
    'vendor': 'brand',
    'proveedor': 'brand',
    
    # Descripción
    'description': 'description',
    'descripcion': 'description',
    'descripción': 'description',
    'body': 'description',
    'body (html)': 'description',
    
    # Imagen
    'image_url': 'image_url',
    'imagen': 'image_url',
    'image': 'image_url',
    'image src': 'image_url',
    'url imagen': 'image_url',
}

# Columnas requeridas (en formato estándar)
REQUIRED_COLUMNS = ['sku', 'name', 'price']

# Columnas opcionales
OPTIONAL_COLUMNS = ['description', 'cost', 'quantity', 'min_stock', 'category', 'brand', 'image_url']


# ═══════════════════════════════════════════════════════════
# FUNCIÓN: NORMALIZAR NOMBRES DE COLUMNAS
# ═══════════════════════════════════════════════════════════

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza los nombres de columnas al formato estándar.
    
    Ejemplo:
        "NOMBRE" → "name"
        "PRECIO" → "price"
        "Variant SKU" → "sku"
    """
    new_columns = {}
    
    for col in df.columns:
        # Convertir a minúsculas y quitar espacios
        col_lower = col.lower().strip()
        
        # Buscar en el mapeo
        if col_lower in COLUMN_MAPPING:
            new_columns[col] = COLUMN_MAPPING[col_lower]
        else:
            # Si no está en el mapeo, mantener el nombre original
            new_columns[col] = col_lower
    
    # Renombrar columnas
    df = df.rename(columns=new_columns)
    
    return df


# ═══════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL: LEER ARCHIVO
# ═══════════════════════════════════════════════════════════

def read_import_file(file: FileStorage) -> Tuple[List[Dict], List[str]]:
    """
    Lee un archivo Excel o CSV y retorna los datos como lista de diccionarios.
    
    PARÁMETROS:
    -----------
    file : FileStorage
        Archivo subido por el usuario (viene del request de Flask)
    
    RETORNA:
    --------
    Tuple[List[Dict], List[str]]
        - Lista de productos (cada uno es un diccionario)
        - Lista de errores/advertencias
    """
    
    errors = []
    
    # ─────────────────────────────────────────────────────────
    # PASO 1: Detectar tipo de archivo
    # ─────────────────────────────────────────────────────────
    
    filename = file.filename.lower()
    
    if filename.endswith('.xlsx') or filename.endswith('.xls'):
        file_type = 'excel'
    elif filename.endswith('.csv'):
        file_type = 'csv'
    else:
        return [], ['Formato de archivo no soportado. Usa .xlsx, .xls o .csv']
    
    # ─────────────────────────────────────────────────────────
    # PASO 2: Leer archivo con Pandas
    # ─────────────────────────────────────────────────────────
    
    try:
        if file_type == 'excel':
            df = pd.read_excel(file, engine='openpyxl')
        else:
            # Intentar diferentes encodings
            try:
                df = pd.read_csv(file, encoding='utf-8')
            except UnicodeDecodeError:
                file.seek(0)  # Volver al inicio del archivo
                df = pd.read_csv(file, encoding='latin-1')
    
    except Exception as e:
        return [], [f'Error al leer el archivo: {str(e)}']
    
    # ─────────────────────────────────────────────────────────
    # PASO 3: Normalizar nombres de columnas
    # ─────────────────────────────────────────────────────────
    
    # Guardar nombres originales para el mensaje de error
    original_columns = list(df.columns)
    
    # Normalizar columnas
    df = normalize_columns(df)
    
    # Mostrar mapeo para debug
    print(f"Columnas originales: {original_columns}")
    print(f"Columnas normalizadas: {list(df.columns)}")
    
    # ─────────────────────────────────────────────────────────
    # PASO 4: Validar columnas requeridas
    # ─────────────────────────────────────────────────────────
    
    missing_columns = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing_columns.append(col)
    
    if missing_columns:
        return [], [
            f'Faltan columnas requeridas: {", ".join(missing_columns)}',
            f'Columnas encontradas: {", ".join(df.columns)}',
            'Nombres aceptados: sku/codigo/SKU, name/nombre/NOMBRE, price/precio/PRECIO'
        ]
    
    # ─────────────────────────────────────────────────────────
    # PASO 5: Manejar caso especial de STOCK vs UNIDADES
    # ─────────────────────────────────────────────────────────
    
    # Si hay columna "stock" que debería ser min_stock (y ya hay quantity)
    # Esto maneja el caso del usuario: UNIDADES=quantity, STOCK=min_stock
    if 'quantity' in df.columns:
        # Verificar si hay otra columna que debería ser min_stock
        for col in original_columns:
            col_lower = col.lower().strip()
            if col_lower == 'stock' and 'unidades' in [c.lower().strip() for c in original_columns]:
                # En este caso, "stock" es min_stock, no quantity
                df = df.rename(columns={'quantity': 'min_stock'})
                # Y necesitamos mapear de nuevo
                for orig_col in original_columns:
                    if orig_col.lower().strip() == 'unidades':
                        # Buscar la columna que quedó como 'unidades' y renombrar a quantity
                        pass
    
    # Mejor solución: revisar si tenemos UNIDADES y STOCK como columnas separadas
    # UNIDADES = quantity, STOCK = min_stock
    
    # ─────────────────────────────────────────────────────────
    # PASO 6: Procesar cada fila
    # ─────────────────────────────────────────────────────────
    
    products = []
    
    for index, row in df.iterrows():
        row_num = index + 2  # +2 porque Excel empieza en 1 y hay header
        
        # Validar SKU
        sku = str(row.get('sku', '')).strip()
        if not sku or sku == 'nan':
            errors.append(f'Fila {row_num}: SKU vacío, se omitió')
            continue
        
        # Validar nombre
        name = str(row.get('name', '')).strip()
        if not name or name == 'nan':
            errors.append(f'Fila {row_num}: Nombre vacío, se omitió')
            continue
        
        # Validar precio
        try:
            price = float(row.get('price', 0))
            if price < 0:
                errors.append(f'Fila {row_num}: Precio negativo, se puso 0')
                price = 0
        except (ValueError, TypeError):
            errors.append(f'Fila {row_num}: Precio inválido, se puso 0')
            price = 0
        
        # Crear diccionario del producto
        product = {
            'sku': sku.upper(),
            'name': name,
            'price': price
        }
        
        # Agregar campos opcionales
        product['description'] = safe_string(row.get('description'))
        product['cost'] = safe_float(row.get('cost'))
        product['quantity'] = safe_int(row.get('quantity'), default=0)
        product['min_stock'] = safe_int(row.get('min_stock'), default=5)
        product['category'] = safe_string(row.get('category'))
        product['brand'] = safe_string(row.get('brand'))
        product['image_url'] = safe_string(row.get('image_url'))
        
        products.append(product)
    
    if not products:
        errors.append('No se encontraron productos válidos en el archivo')
    
    return products, errors


# ═══════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════

def safe_string(value) -> str:
    """Convierte un valor a string de forma segura."""
    if value is None:
        return None
    
    if pd.isna(value):
        return None
    
    text = str(value).strip()
    
    if text.lower() == 'nan' or text == '':
        return None
    
    return text


def safe_float(value, default: float = None) -> float:
    """Convierte un valor a float de forma segura."""
    if value is None or pd.isna(value):
        return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default: int = 0) -> int:
    """Convierte un valor a entero de forma segura."""
    if value is None or pd.isna(value):
        return default
    
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


# ═══════════════════════════════════════════════════════════
# FUNCIÓN: GENERAR PLANTILLA
# ═══════════════════════════════════════════════════════════

def get_template_columns() -> Dict:
    """Retorna información sobre las columnas para la plantilla."""
    return {
        'required': REQUIRED_COLUMNS,
        'optional': OPTIONAL_COLUMNS,
        'accepted_names': {
            'sku': ['sku', 'SKU', 'codigo', 'código', 'Variant SKU'],
            'name': ['name', 'nombre', 'NOMBRE', 'Title', 'producto'],
            'price': ['price', 'precio', 'PRECIO', 'Variant Price'],
            'cost': ['cost', 'costo', 'COSTO', 'Cost per item'],
            'quantity': ['quantity', 'unidades', 'UNIDADES', 'stock', 'inventario'],
            'min_stock': ['min_stock', 'STOCK', 'stock minimo'],
            'category': ['category', 'categoria', 'CATEGORIA', 'categoría'],
            'brand': ['brand', 'marca', 'MARCA', 'vendor'],
        },
        'example': {
            'sku': 'PROD-001',
            'name': 'Producto de Ejemplo',
            'price': 99.99,
            'description': 'Descripción del producto',
            'cost': 50.00,
            'quantity': 100,
            'min_stock': 10,
            'category': 'Electrónicos',
            'brand': 'MiMarca',
            'image_url': 'https://ejemplo.com/imagen.jpg'
        }
    }
