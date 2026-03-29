"""
Script para encriptar tokens existentes en la BD.

Detecta tokens en texto plano y los encripta.
Los tokens ya encriptados (empiezan con 'gAAAAA') se ignoran.

Uso:
    cd ~/Desktop/vendeflow/backend
    source venv/bin/activate
    python scripts/encrypt_existing_tokens.py
"""
from app import create_app, db
from app.models.platform_connection import PlatformConnection
from app.utils.encryption import encrypt_token, is_encrypted

app = create_app()

with app.app_context():
    connections = PlatformConnection.query.all()
    
    if not connections:
        print("No hay conexiones en la BD.")
    else:
        updated = 0
        skipped = 0

        for conn in connections:
            changed = False

            # Encriptar access_token si está en texto plano
            raw_access = conn._access_token
            if raw_access and not is_encrypted(raw_access):
                conn._access_token = encrypt_token(raw_access)
                changed = True
                print(f"✅ access_token encriptado: {conn.platform}:{conn.store_name}")

            # Encriptar refresh_token si está en texto plano
            raw_refresh = conn._refresh_token
            if raw_refresh and not is_encrypted(raw_refresh):
                conn._refresh_token = encrypt_token(raw_refresh)
                changed = True
                print(f"✅ refresh_token encriptado: {conn.platform}:{conn.store_name}")

            if changed:
                updated += 1
            else:
                skipped += 1
                print(f"⏭️  Ya encriptado (ignorado): {conn.platform}:{conn.store_name}")

        db.session.commit()
        print(f"\n🎉 Listo: {updated} conexiones encriptadas, {skipped} ya estaban encriptadas.")
