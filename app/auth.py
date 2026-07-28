from flask_login import LoginManager, UserMixin

from .supabase_client import get_supabase

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Inicia sesión para continuar."


class Usuario(UserMixin):
    def __init__(self, id, nombre, email, rol):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.rol = rol


@login_manager.user_loader
def load_user(user_id):
    sb = get_supabase()
    res = sb.table("usuarios").select("*").eq("id", user_id).limit(1).execute()
    if not res.data:
        return None
    u = res.data[0]
    return Usuario(u["id"], u["nombre"], u["email"], u["rol"])
