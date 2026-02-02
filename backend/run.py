"""
VendeFlow - Punto de Entrada
============================
Este archivo inicia el servidor Flask.

Para ejecutar:
    python run.py
    
O con Flask CLI:
    flask run
"""

from app import create_app

# Crear la aplicación
app = create_app()

if __name__ == '__main__':
    # Ejecutar servidor de desarrollo
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )
