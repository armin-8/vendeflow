"""
VendeFlow - Utilidades
======================
Funciones auxiliares compartidas.
"""


def format_currency(amount: float, currency: str = 'MXN') -> str:
    """
    Formatea un monto como moneda.
    
    Args:
        amount: Cantidad a formatear
        currency: Código de moneda (default: MXN)
    
    Returns:
        String formateado (ej: "$1,234.56 MXN")
    """
    return f"${amount:,.2f} {currency}"


def sanitize_string(value: str) -> str:
    """
    Limpia un string de caracteres peligrosos.
    
    Args:
        value: String a limpiar
    
    Returns:
        String sanitizado
    """
    if not value:
        return ""
    return value.strip()
