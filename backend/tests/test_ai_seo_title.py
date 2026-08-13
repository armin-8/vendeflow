"""
VendeFlow - Tests del formato del seo_title
=============================================

Formato objetivo:

    Nombre del producto | Descriptor con palabra clave + Gancho

Llama 3.2 acierta el formato pero falla en dos cosas de forma consistente:
se pasa del límite y hay que recortar (dejando conectores colgando), e inventa
ganchos que la descripción del usuario nunca mencionó.

`_ajustar_seo_title` corrige ambas de forma determinista, sin depender de que
el modelo obedezca. Estos tests no necesitan Ollama.
"""

from app.services.ai_service import AIService


SERVICIO = AIService()

# Descripción que SÍ menciona baterías de regalo
CON_BATERIAS = ('Camara de accion 5.3K. INCLUYE DOS BATERIAS EXTRA DE REGALO '
                'y tarjeta microSD de 64GB. Garantia de 2 anos.')

# Descripción que no ofrece nada extra
SIN_EXTRAS = 'Camara de accion 5.3K, estabilizacion HyperSmooth, pantalla tactil doble.'


# ═══════════════════════════════════════════════════════════
# LÍMITE DE LARGO
# ═══════════════════════════════════════════════════════════

def test_respeta_el_limite_de_70():
    largo = 'GoPro Hero Mission Pro | Camara de accion con sensor de 1 pulgada y estabilizacion avanzada'
    assert len(SERVICIO._ajustar_seo_title(largo, SIN_EXTRAS)) <= 70


def test_no_deja_conectores_colgando():
    """Un título que termina en 'y' o 'de' se lee partido."""
    largo = 'GoPro Hero Mission Pro | Camara de accion con sensor de 1 pulgada y estabilizacion'
    resultado = SERVICIO._ajustar_seo_title(largo, SIN_EXTRAS)

    ultima = resultado.split()[-1].lower()
    assert ultima not in AIService.CONECTORES
    assert not resultado.endswith(('|', '+', '-', ','))


def test_un_titulo_que_ya_cabe_no_se_toca():
    corto = 'Licuadora Oster Pro 1200 | Licuadora de vaso de vidrio termico'
    assert SERVICIO._ajustar_seo_title(corto, SIN_EXTRAS) == corto


# ═══════════════════════════════════════════════════════════
# EL GANCHO NO SE INVENTA
# ═══════════════════════════════════════════════════════════

def test_conserva_el_gancho_respaldado_por_la_descripcion():
    """'Baterias' aparece en la info del usuario → el gancho es legítimo."""
    titulo = 'GoPro Hero Mission Pro | Camara 5.3K + Baterias Gratis'
    resultado = SERVICIO._ajustar_seo_title(titulo, CON_BATERIAS)

    assert '+ Baterias Gratis' in resultado


def test_elimina_el_gancho_inventado():
    """
    El caso que motivó todo esto: el modelo agregaba '+ Accesorio' aunque la
    descripción no mencionara ningún accesorio. La IA organiza lo que dio el
    usuario, no inventa.
    """
    titulo = 'GoPro Hero Mission Pro | Camara de accion profesional + Accesorio'
    resultado = SERVICIO._ajustar_seo_title(titulo, SIN_EXTRAS)

    assert '+' not in resultado
    assert 'Accesorio' not in resultado
    assert resultado == 'GoPro Hero Mission Pro | Camara de accion profesional'


def test_el_respaldo_ignora_acentos_y_mayusculas():
    titulo = 'Producto X | Descriptor + Garantía Incluida'
    con_acento_distinto = 'Viene con garantia de dos anos.'

    assert 'Garantía' in SERVICIO._ajustar_seo_title(titulo, con_acento_distinto)


# ═══════════════════════════════════════════════════════════
# GANCHO MUTILADO POR EL RECORTE
# ═══════════════════════════════════════════════════════════

def test_quita_el_gancho_entero_si_el_recorte_lo_parte():
    """
    Mejor un título limpio sin gancho que uno terminado en '+ Acceso'.
    """
    titulo = 'GoPro Hero Mission Pro | Camara de accion profesional 5.3K + Baterias Extra de Regalo'
    resultado = SERVICIO._ajustar_seo_title(titulo, CON_BATERIAS)

    assert len(resultado) <= 70
    assert '+' not in resultado
    assert resultado == 'GoPro Hero Mission Pro | Camara de accion profesional 5.3K'


# ═══════════════════════════════════════════════════════════
# BORDES
# ═══════════════════════════════════════════════════════════

def test_titulo_vacio_no_truena():
    assert SERVICIO._ajustar_seo_title('', SIN_EXTRAS) == ''
    assert SERVICIO._ajustar_seo_title(None, SIN_EXTRAS) in ('', None)


def test_descripcion_vacia_quita_el_gancho():
    """Sin info del usuario, ningún gancho puede estar respaldado."""
    titulo = 'Producto X | Descriptor + Envio Gratis'
    assert '+' not in SERVICIO._ajustar_seo_title(titulo, '')


def test_normaliza_espacios_multiples():
    assert SERVICIO._ajustar_seo_title('Producto   X  |   Descriptor', SIN_EXTRAS) == 'Producto X | Descriptor'
