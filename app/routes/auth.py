import time
from collections import defaultdict

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from ..auth import Usuario
from ..supabase_client import get_supabase

auth_bp = Blueprint("auth", __name__)

MAX_INTENTOS_FALLIDOS = 5
VENTANA_BLOQUEO_SEGUNDOS = 15 * 60  # 15 minutos
_intentos_fallidos = defaultdict(list)


def _demasiados_intentos(email: str) -> bool:
    ahora = time.time()
    intentos = [t for t in _intentos_fallidos[email] if ahora - t < VENTANA_BLOQUEO_SEGUNDOS]
    _intentos_fallidos[email] = intentos
    return len(intentos) >= MAX_INTENTOS_FALLIDOS


def _registrar_intento_fallido(email: str) -> None:
    _intentos_fallidos[email].append(time.time())


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if _demasiados_intentos(email):
            flash("Demasiados intentos fallidos. Espera unos minutos antes de volver a intentar.", "error")
            return render_template("login.html")

        sb = get_supabase()
        res = sb.table("usuarios").select("*").eq("email", email).limit(1).execute()
        if res.data and check_password_hash(res.data[0]["password_hash"], password):
            _intentos_fallidos.pop(email, None)
            u = res.data[0]
            login_user(Usuario(u["id"], u["nombre"], u["email"], u["rol"]))
            return redirect(url_for("dashboard.index"))
        _registrar_intento_fallido(email)
        flash("Correo o contraseña incorrectos", "error")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
