"""
VendeFlow - Servicio de Importación
====================================

Este servicio maneja la lógica para importar productos desde archivos
Excel (.xlsx) o CSV (.csv).

SOPORTA MÚLTIPLES FORMATOS DE COLUMNAS:
- Inglés: sku, name, price, cost, quantity, min_stock, category, brand
- Español: SKU, NOMBRE, PRECIO, COSTO, UNIDADES, STOCK, CATEGORIA, MARCA
"""

import pandas as pd
from typing import List, Dict, Tuple
from werkzeug.datastructures import FileStorage


# ═══════════════════════════════════════════════════════════
# MAPEO DE COLUMNAS (soporta múltiples idiomas/formatos)
# ═══════════════════════════════════════════════════════════

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
    
    # Cantidad (UNIDADES)
    'quantity': 'quantity',
    'cantidad': 'quantity',
    'unidades': 'quantity',
    'variant inventory qty': 'quantity',
    'inventory': 'quantity',
    'inventario': 'quantity',
    
    # Stock mínimo (STOCK)
    'min_stock': 'min_stock',
    'stock': 'min_stock',
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

REQUIRED_COLUMNS = ['sku', 'name', 'price']
OPTIONAL_COLUMNS = ['description', 'cost', 'quantity', 'min_stock', 'category', 'brand', 'image_url']


# ═══════════════════════════════════════════════════════════
# FUNCIÓN: NORMALIZAR NOMBRES DE COLUMNAS
# ═══════════════════════════════════════════════════════════

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza los nombres de columnas al formato estándar.
    Maneja columnas duplicadas agregando sufijo.
    """
    new_columns = []
    seen_columns = {}
    
    for col in df.columns:
        col_lower = col.lower().strip()
        
        # Buscar en el mapeo
        if col_lower in COLUMN_MAPPING:
            new_name = COLUMN_MAPPING[col_lower]
        else:
            new_name = col_lower
        
        # Manejar duplicados
        if new_name in seen_columns:
            seen_columns[new_name] += 1
            new_name = f"{new_name}_{seen_columns[new_name]}"
        else:
            seen_columns[new_name] = 0
        
        new_columns.append(new_name)
    
    df.columns = new_columns
    return df


# ═══════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL: LEER ARCHIVO
# ═══════════════════════════════════════════════════════════

def read_import_file(file: FileStorage) -> Tuple[List[Dict], List[str]]:
    """
    Lee un archivo Excel o CSV y retorna los datos como lista de diccionarios.
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
            try:
                df = pd.read_csv(file, encoding='utf-8')
            except UnicodeDecodeError:
                file.seek(0)
                df = pd.read_csv(file, encoding='latin-1')
    
    except Exception as e:
        return [], [f'Error al leer el archivo: {str(e)}']
    
    # ─────────────────────────────────────────────────────────
    # PASO 3: Normalizar nombres de columnas
    # ─────────────────────────────────────────────────────────
    
    original_columns = list(df.columns)
    df = normalize_columns(df)
    
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
    # PASO 5: Procesar cada fila
    # ─────────────────────────────────────────────────────────
    
    products = []
    
    for index, row in df.iterrows():
        row_num = index + 2
        
        # Validar SKU
        sku = get_cell_value(row, 'sku', '')
        if not sku:
            errors.append(f'Fila {row_num}: SKU vacío, se omitió')
            continue
        
        # Validar nombre
        name = get_cell_value(row, 'name', '')
        if not name:
            errors.append(f'Fila {row_num}: Nombre vacío, se omitió')
            continue
        
        # Validar precio
        price = get_cell_value(row, 'price', 0, value_type='float')
        if price < 0:
            errors.append(f'Fila {row_num}: Precio negativo, se puso 0')
            price = 0
        
        # Crear diccionario del producto
        product = {
            'sku': str(sku).strip().upper(),
            'name': str(name).strip(),
            'price': price,
            'description': get_cell_value(row, 'description', None),
            'cost': get_cell_value(row, 'cost', None, value_type='float'),
            'quantity': get_cell_value(row, 'quantity', 0, value_type='int'),
            'min_stock': get_cell_value(row, 'min_stock', 5, value_type='int'),
            'category': get_cell_value(row, 'category', None),
            'brand': get_cell_value(row, 'brand', None),
            'image_url': get_cell_value(row, 'image_url', None),
        }
        
        products.append(product)
    
    if not products:
        errors.append('No se encontraron productos válidos en el archivo')
    
    return products, errors


# ═══════════════════════════════════════════════════════════
# FUNCIÓN: OBTENER VALOR DE CELDA DE FORMA SEGURA
# ═══════════════════════════════════════════════════════════

def get_cell_value(row, column_name: str, default, value_type: str = 'string'):
    """
    Obtiene el valor de una celda de forma segura.
    
    Maneja casos especiales como:
    - Columna no existe
    - Valor es NaN
    - Valor es Serie (columna duplicada)
    """
    
    # Si la columna no existe, retornar default
    if column_name not in row.index:
        return default
    
    value = row[column_name]
    
    # Si es una Serie (columna duplicada), tomar el primer valor
    if isinstance(value, pd.Series):
        value = value.iloc[0]
    
    # Si es NaN o None, retornar default
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    
    # Convertir string 'nan' a default
    if isinstance(value, str) and value.lower().strip() == 'nan':
        return default
    
    # Convertir según el tipo
    try:
        if value_type == 'int':
            return int(float(value))
        elif value_type == 'float':
            return float(value)
        else:
            # String
            result = str(value).strip()
            return result if result else default
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
            'sku': ['sku', 'SKU', 'codigo', 'código'],
            'name': ['name', 'nombre', 'NOMBRE', 'Title'],
            'price': ['price', 'precio', 'PRECIO'],
            'cost': ['cost', 'costo', 'COSTO'],
            'quantity': ['quantity', 'unidades', 'UNIDADES'],
            'min_stock': ['min_stock', 'stock', 'STOCK'],
            'category': ['category', 'categoria', 'CATEGORIA'],
            'brand': ['brand', 'marca', 'MARCA'],
        },
        'example': {
            'sku': 'PROD-001',
            'name': 'Producto de Ejemplo',
            'price': 99.99,
            'cost': 50.00,
            'quantity': 100,
            'min_stock': 10,
            'category': 'Electrónicos',
            'brand': 'MiMarca',
        }
    }
