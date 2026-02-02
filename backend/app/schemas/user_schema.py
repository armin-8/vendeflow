"""
VendeFlow - Schemas de Usuario
==============================
Define la estructura y validación de datos para usuarios.

¿QUÉ ES PYDANTIC Y POR QUÉ LO USAMOS?
-------------------------------------
En Revístete, validabas manualmente así:

    if "email" not in data or not data["email"]:
        return jsonify({"error": "Missing email"}), 400

Con Pydantic, defines la estructura UNA VEZ y la validación es automática:

    class UserCreate(BaseModel):
        email: EmailStr  # ← Valida que sea email automáticamente

VENTAJAS:
- Código más limpio
- Errores más descriptivos
- Documentación automática
- Type hints para tu IDE
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


# ═══════════════════════════════════════════════════════════
# SCHEMA PARA REGISTRO
# ═══════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    """
    Schema para crear un nuevo usuario.
    
    Ejemplo de uso:
        data = request.get_json()
        user_data = UserCreate(**data)  # ← Valida automáticamente
    """
    
    email: EmailStr = Field(
        ...,  # ... significa que es requerido
        description="Email del usuario",
        examples=["usuario@ejemplo.com"]
    )
    
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="Contraseña (mínimo 6 caracteres)"
    )
    
    first_name: str = Field(
        ...,
        min_length=2,
        max_length=80,
        description="Nombre del usuario"
    )
    
    last_name: str = Field(
        ...,
        min_length=2,
        max_length=80,
        description="Apellido del usuario"
    )
    
    company_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Nombre de la empresa (opcional)"
    )
    
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Teléfono (opcional)"
    )
    
    # Validador personalizado para el nombre
    @field_validator('first_name', 'last_name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        """Valida que el nombre no sea solo espacios."""
        if not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()


# ═══════════════════════════════════════════════════════════
# SCHEMA PARA LOGIN
# ═══════════════════════════════════════════════════════════

class UserLogin(BaseModel):
    """Schema para iniciar sesión."""
    
    email: EmailStr = Field(
        ...,
        description="Email del usuario"
    )
    
    password: str = Field(
        ...,
        description="Contraseña"
    )


# ═══════════════════════════════════════════════════════════
# SCHEMA PARA RESPUESTA
# ═══════════════════════════════════════════════════════════

class UserResponse(BaseModel):
    """
    Schema para respuesta de usuario.
    
    IMPORTANTE: No incluye password por seguridad.
    """
    
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    full_name: str
    company_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        """Configuración del schema."""
        from_attributes = True  # Permite crear desde objetos SQLAlchemy


# ═══════════════════════════════════════════════════════════
# SCHEMA PARA ACTUALIZACIÓN
# ═══════════════════════════════════════════════════════════

class UserUpdate(BaseModel):
    """
    Schema para actualizar usuario.
    
    Todos los campos son opcionales porque el usuario
    puede querer actualizar solo algunos.
    """
    
    first_name: Optional[str] = Field(None, min_length=2, max_length=80)
    last_name: Optional[str] = Field(None, min_length=2, max_length=80)
    company_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    
    # Para cambio de contraseña
    current_password: Optional[str] = Field(None, description="Contraseña actual (requerida para cambiar)")
    new_password: Optional[str] = Field(None, min_length=6, description="Nueva contraseña")
