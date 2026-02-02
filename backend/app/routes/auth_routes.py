"""
VendeFlow - Rutas de Autenticación
==================================
Endpoints para registro, login y gestión de usuarios.

DIFERENCIAS CON REVÍSTETE:
--------------------------
1. Usamos Blueprint para organizar rutas (igual que antes)
2. Usamos Pydantic para validación (nuevo)
3. Manejo de errores centralizado (nuevo)
4. Código más limpio y documentado

ENDPOINTS:
- POST /api/auth/register  - Registrar nuevo usuario
- POST /api/auth/login     - Iniciar sesión
- GET  /api/auth/me        - Obtener usuario actual
- PUT  /api/auth/me        - Actualizar perfil
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, 
    jwt_required, 
    get_jwt_identity
)
from pydantic import ValidationError

from app import db
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserLogin, UserUpdate

# Crear Blueprint
bp = Blueprint('auth', __name__, url_prefix='/api/auth')


# ═══════════════════════════════════════════════════════════
# REGISTRO DE USUARIO
# ═══════════════════════════════════════════════════════════

@bp.route('/register', methods=['POST'])
def register():
    """
    Registra un nuevo usuario.
    
    Request Body:
        {
            "email": "usuario@ejemplo.com",
            "password": "mipassword123",
            "first_name": "Juan",
            "last_name": "Pérez",
            "company_name": "Mi Empresa" (opcional),
            "phone": "+52 123 456 7890" (opcional)
        }
    
    Returns:
        201: Usuario creado exitosamente + token
        400: Error de validación
        409: Email ya existe
    """
    
    # 1. Verificar que hay JSON en el request
    if not request.is_json:
        return jsonify({'error': 'Se requiere JSON en el request'}), 400
    
    # 2. Validar datos con Pydantic
    try:
        data = request.get_json()
        user_data = UserCreate(**data)
    except ValidationError as e:
        # Pydantic nos da errores detallados
        return jsonify({
            'error': 'Error de validación',
            'details': e.errors()
        }), 400
    
    # 3. Verificar si el email ya existe
    existing_user = User.query.filter_by(email=user_data.email).first()
    if existing_user:
        return jsonify({'error': 'El email ya está registrado'}), 409
    
    # 4. Crear nuevo usuario
    new_user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        company_name=user_data.company_name,
        phone=user_data.phone
    )
    new_user.set_password(user_data.password)
    
    # 5. Guardar en base de datos
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear usuario: {str(e)}'}), 500
    
    # 6. Crear token JWT
    access_token = create_access_token(identity=str(new_user.id))
    
    # 7. Retornar respuesta exitosa
    return jsonify({
        'message': 'Usuario registrado exitosamente',
        'token': access_token,
        'user': new_user.to_dict()
    }), 201


# ═══════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════

@bp.route('/login', methods=['POST'])
def login():
    """
    Inicia sesión y retorna un token JWT.
    
    Request Body:
        {
            "email": "usuario@ejemplo.com",
            "password": "mipassword123"
        }
    
    Returns:
        200: Login exitoso + token
        400: Error de validación
        401: Credenciales incorrectas
    """
    
    # 1. Verificar JSON
    if not request.is_json:
        return jsonify({'error': 'Se requiere JSON en el request'}), 400
    
    # 2. Validar datos
    try:
        data = request.get_json()
        login_data = UserLogin(**data)
    except ValidationError as e:
        return jsonify({
            'error': 'Error de validación',
            'details': e.errors()
        }), 400
    
    # 3. Buscar usuario
    user = User.query.filter_by(email=login_data.email).first()
    
    # 4. Verificar credenciales
    if not user or not user.check_password(login_data.password):
        return jsonify({'error': 'Email o contraseña incorrectos'}), 401
    
    # 5. Verificar que la cuenta esté activa
    if not user.is_active:
        return jsonify({'error': 'La cuenta está desactivada'}), 401
    
    # 6. Actualizar último login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # 7. Crear token
    access_token = create_access_token(identity=str(user.id))
    
    # 8. Retornar respuesta
    return jsonify({
        'message': 'Login exitoso',
        'token': access_token,
        'user': user.to_dict()
    }), 200


# ═══════════════════════════════════════════════════════════
# OBTENER USUARIO ACTUAL
# ═══════════════════════════════════════════════════════════

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Obtiene los datos del usuario autenticado.
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: Datos del usuario
        401: No autenticado
        404: Usuario no encontrado
    """
    
    # get_jwt_identity() nos da el ID del usuario del token
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


# ═══════════════════════════════════════════════════════════
# ACTUALIZAR PERFIL
# ═══════════════════════════════════════════════════════════

@bp.route('/me', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Actualiza el perfil del usuario autenticado.
    
    Headers:
        Authorization: Bearer <token>
    
    Request Body (todos opcionales):
        {
            "first_name": "Juan",
            "last_name": "Pérez",
            "company_name": "Nueva Empresa",
            "phone": "+52 999 888 7777",
            "current_password": "actual123",
            "new_password": "nueva456"
        }
    
    Returns:
        200: Perfil actualizado
        400: Error de validación
        401: Contraseña actual incorrecta
    """
    
    # 1. Obtener usuario actual
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    # 2. Validar datos
    if not request.is_json:
        return jsonify({'error': 'Se requiere JSON en el request'}), 400
    
    try:
        data = request.get_json()
        update_data = UserUpdate(**data)
    except ValidationError as e:
        return jsonify({
            'error': 'Error de validación',
            'details': e.errors()
        }), 400
    
    # 3. Actualizar campos si se proporcionaron
    if update_data.first_name:
        user.first_name = update_data.first_name
    
    if update_data.last_name:
        user.last_name = update_data.last_name
    
    if update_data.company_name is not None:
        user.company_name = update_data.company_name
    
    if update_data.phone is not None:
        user.phone = update_data.phone
    
    # 4. Cambio de contraseña (requiere contraseña actual)
    if update_data.new_password:
        if not update_data.current_password:
            return jsonify({
                'error': 'Se requiere la contraseña actual para cambiarla'
            }), 400
        
        if not user.check_password(update_data.current_password):
            return jsonify({'error': 'Contraseña actual incorrecta'}), 401
        
        user.set_password(update_data.new_password)
    
    # 5. Guardar cambios
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar: {str(e)}'}), 500
    
    return jsonify({
        'message': 'Perfil actualizado exitosamente',
        'user': user.to_dict()
    }), 200
