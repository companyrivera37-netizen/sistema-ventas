import os

from dotenv import load_dotenv
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

from .auth import login_manager  # noqa: E402
from .routes.auth import auth_bp  # noqa: E402
from .routes.clientes import clientes_bp  # noqa: E402
from .routes.dashboard import dashboard_bp  # noqa: E402
from .routes.productos import productos_bp  # noqa: E402
from .routes.ventas import ventas_bp  # noqa: E402


def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    # Render define automaticamente la variable RENDER=true en produccion; en local
    # (sin HTTPS) queda en False para no bloquear la cookie de sesion al probar.
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("RENDER") == "true"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["EMPRESA_NOMBRE"] = os.environ.get("EMPRESA_NOMBRE", "Mi Tienda")
    app.config["EMPRESA_WHATSAPP"] = os.environ.get("EMPRESA_WHATSAPP", "")

    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(ventas_bp)

    return app
