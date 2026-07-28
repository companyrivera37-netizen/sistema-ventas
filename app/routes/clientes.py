from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from ..services import clientes as clientes_service
from ..supabase_client import get_supabase

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")


@clientes_bp.route("/")
@login_required
def listar():
    sb = get_supabase()
    termino = request.args.get("q", "").strip()
    if termino:
        clientes = clientes_service.buscar(termino, limite=50)
    else:
        clientes = sb.table("clientes").select("*").order("creado_en", desc=True).limit(100).execute().data
    return render_template("clientes/listar.html", clientes=clientes, termino=termino)


@clientes_bp.route("/api/buscar")
@login_required
def api_buscar():
    """Autocompletado usado en el formulario de nueva venta."""
    termino = request.args.get("q", "")
    return jsonify(clientes_service.buscar(termino))


@clientes_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        sb = get_supabase()
        cliente = (
            sb.table("clientes")
            .insert(
                {
                    "nombres": request.form["nombres"].strip(),
                    "celular": request.form["celular"].strip(),
                    "direccion": request.form.get("direccion", "").strip() or None,
                }
            )
            .execute()
        )
        flash("Cliente registrado correctamente", "success")
        if request.form.get("volver_a_venta"):
            return redirect(url_for("ventas.nueva", cliente_id=cliente.data[0]["id"]))
        return redirect(url_for("clientes.listar"))
    return render_template("clientes/nuevo.html")


@clientes_bp.route("/<cliente_id>")
@login_required
def detalle(cliente_id):
    sb = get_supabase()
    cliente = sb.table("clientes").select("*").eq("id", cliente_id).single().execute().data
    ventas = (
        sb.table("ventas")
        .select("*, productos(nombre)")
        .eq("cliente_id", cliente_id)
        .order("creado_en", desc=True)
        .execute()
        .data
    )
    return render_template("clientes/detalle.html", cliente=cliente, ventas=ventas)
