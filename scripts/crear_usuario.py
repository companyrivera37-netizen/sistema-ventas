"""Uso: python scripts/crear_usuario.py <nombre> <email> <password>

Crea el primer usuario administrador del panel (no hay registro publico).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from werkzeug.security import generate_password_hash  # noqa: E402

from app.supabase_client import get_supabase  # noqa: E402


def main():
    if len(sys.argv) != 4:
        print("Uso: python scripts/crear_usuario.py <nombre> <email> <password>")
        sys.exit(1)

    nombre, email, password = sys.argv[1:4]
    sb = get_supabase()
    sb.table("usuarios").insert(
        {
            "nombre": nombre,
            "email": email.strip().lower(),
            "password_hash": generate_password_hash(password),
            "rol": "admin",
        }
    ).execute()
    print(f"Usuario {email} creado correctamente.")


if __name__ == "__main__":
    main()
