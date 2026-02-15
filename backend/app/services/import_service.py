"""
VendeFlow - Servicio de Importación
====================================

Este servicio maneja la lógica para importar productos desde archivos
Excel (.xlsx) o CSV (.csv).

¿QUÉ ES PANDAS?
---------------
Pandas es una librería de Python para manipular datos tabulares.
Piensa en ella como "Excel dentro de Python".

Términos importantes:
- DataFrame: Es como una hoja de Excel (tabla con filas y columnas)
- Series: Es una sola columna
- read_excel(): Lee archivos .xlsx
- read_csv(): Lee archivos .csv
"""

import pandas as pd
from typing import List, Dict, Tuple
from werkzeug.datastructures import FileStorage


# ═══════════════════════════════════════════════════════════
# COLUMNAS REQUERIDAS Y OPCIONALES
# ═══════════════════════════════════════════════════════════

# Columnas que DEBEN existir en el archivo
REQUIRED_COLUMNS = ['sku', 'name', 'price']

# Columnas opcionales que podemos importar
OPTIONAL_COLUMNS = ['description', 'cost', 'quantity', 'min_stock', 'category', 'brand', 'image_url']

# Todas las columnas válidas
ALL_VALID_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


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
    
    EJEMPLO DE USO:
    ---------------
    products, errors = read_import_file(uploaded_file)
    
    if errors:
        print("Hay problemas:", errors)
    else:
        print(f"Se leyeron {len(products)} productos")
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
            # read_excel() lee archivos de Excel
            # El parámetro 'engine' especifica qué librería usar
            df = pd.read_excel(file, engine='openpyxl')
        else:
            # read_csv() lee archivos CSV
            # encoding='utf-8' maneja caracteres especiales (acentos, ñ, etc.)
            df = pd.read_csv(file, encoding='utf-8')
    
    except Exception as e:
        return [], [f'Error al leer el archivo: {str(e)}']
    
    # ─────────────────────────────────────────────────────────
    # PASO 3: Limpiar nombres de columnas
    # ─────────────────────────────────────────────────────────
    
    # Convertir nombres de columnas a minúsculas y quitar espacios
    # Ejemplo: "  SKU  " → "sku"
    df.columns = df.columns.str.lower().str.strip()
    
    # ─────────────────────────────────────────────────────────
    # PASO 4: Validar columnas requeridas
    # ─────────────────────────────────────────────────────────
    
    missing_columns = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing_columns.append(col)
    
    if missing_columns:
        return [], [f'Faltan columnas requeridas: {", ".join(missing_columns)}']
    
    # ─────────────────────────────────────────────────────────
    # PASO 5: Procesar cada fila
    # ─────────────────────────────────────────────────────────
    
    products = []
    
    # iterrows() recorre cada fila del DataFrame
    # index = número de fila (0, 1, 2, ...)
    # row = los datos de esa fila
    for index, row in df.iterrows():
        
        # Número de fila para mensajes de error (sumamos 2: 1 por el header, 1 porque empieza en 0)
        row_num = index + 2
        
        # Validar que SKU no esté vacío
        sku = str(row.get('sku', '')).strip()
        if not sku or sku == 'nan':
            errors.append(f'Fila {row_num}: SKU vacío, se omitió')
            continue
        
        # Validar que nombre no esté vacío
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
            'sku': sku.upper(),  # SKU siempre en mayúsculas
            'name': name,
            'price': price
        }
        
        # Agregar campos opcionales si existen
        product['description'] = safe_string(row.get('description'))
        product['cost'] = safe_float(row.get('cost'))
        product['quantity'] = safe_int(row.get('quantity'), default=0)
        product['min_stock'] = safe_int(row.get('min_stock'), default=5)
        product['category'] = safe_string(row.get('category'))
        product['brand'] = safe_string(row.get('brand'))
        product['image_url'] = safe_string(row.get('image_url'))
        
        products.append(product)
    
    # ─────────────────────────────────────────────────────────
    # PASO 6: Retornar resultados
    # ─────────────────────────────────────────────────────────
    
    if not products:
        errors.append('No se encontraron productos válidos en el archivo')
    
    return products, errors


# ═══════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════

def safe_string(value) -> str:
    """
    Convierte un valor a string de forma segura.
    
    Maneja casos como:
    - None → None
    - NaN (Not a Number de pandas) → None
    - "  texto  " → "texto"
    """
    if value is None:
        return None
    
    if pd.isna(value):  # Verifica si es NaN
        return None
    
    text = str(value).strip()
    
    if text.lower() == 'nan' or text == '':
        return None
    
    return text


def safe_float(value, default: float = None) -> float:
    """
    Convierte un valor a float de forma segura.
    
    Ejemplos:
    - "123.45" → 123.45
    - "abc" → None (o el default)
    - None → None
    """
    if value is None or pd.isna(value):
        return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default: int = 0) -> int:
    """
    Convierte un valor a entero de forma segura.
    
    Ejemplos:
    - "100" → 100
    - "50.5" → 50
    - "abc" → 0 (o el default)
    """
    if value is None or pd.isna(value):
        return default
    
    try:
        return int(float(value))  # float primero para manejar "50.0"
    except (ValueError, TypeError):
        return default


# ═══════════════════════════════════════════════════════════
# FUNCIÓN: GENERAR PLANTILLA
# ═══════════════════════════════════════════════════════════

def get_template_columns() -> Dict:
    """
    Retorna información sobre las columnas para la plantilla.
    
    Útil para que el frontend muestre qué columnas espera el sistema.
    """
    return {
        'required': REQUIRED_COLUMNS,
        'optional': OPTIONAL_COLUMNS,
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
