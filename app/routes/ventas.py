from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..services import cobros as cobros_service
from ..services.fecha import hoy_peru
from ..services.whatsapp import link_whatsapp_recordatorio_cobro
from ..supabase_client import get_supabase

ventas_bp = Blueprint("ventas", __name__, url_prefix="/ventas")


@ventas_bp.route("/nueva", methods=["GET", "POST"])
@login_required
def nueva():
    sb = get_supabase()

    if request.method == "POST":
        cliente_id = request.form.get("cliente_id", "").strip()
        producto_id = request.form.get("producto_id", "").strip()
        if not cliente_id or not producto_id:
            flash("Elige un producto y un cliente antes de guardar la venta.", "error")
            return redirect(url_for("ventas.nueva"))

        producto = sb.table("productos").select("*").eq("id", producto_id).single().execute().data

        cantidad = int(request.form.get("cantidad") or 1)
        precio_unitario = float(request.form.get("precio_unitario") or producto["precio_venta"])
        monto_total = round(precio_unitario * cantidad, 2)
        tipo_venta = request.form["tipo_venta"]
        hoy = hoy_peru()

        datos = {
            "cliente_id": cliente_id,
            "producto_id": producto_id,
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
            "costo_unitario": producto["costo"],
            "monto_total": monto_total,
            "tipo_venta": tipo_venta,
            "fecha_venta": hoy.isoformat(),
            "notas": request.form.get("notas", "").strip() or None,
            "creado_por": current_user.id,
        }

        if tipo_venta == "credito":
            adelanto = float(request.form.get("adelanto") or 0)
            saldo = round(monto_total - adelanto, 2)
            frecuencia = request.form.get("frecuencia_cobro") or "manual"
            fecha_manual = None
            if frecuencia == "manual" and request.form.get("fecha_manual"):
                fecha_manual = date.fromisoformat(request.form["fecha_manual"])

            datos["adelanto"] = adelanto
            datos["frecuencia_cobro"] = frecuencia
            if saldo <= 0:
                datos["saldo_pendiente"] = 0
                datos["estado"] = "pagado"
                datos["proxima_fecha_cobro"] = None
            else:
                datos["saldo_pendiente"] = saldo
                datos["estado"] = "pendiente"
                proxima = cobros_service.calcular_proxima_fecha(frecuencia, hoy, fecha_manual)
                datos["proxima_fecha_cobro"] = proxima.isoformat() if proxima else None
        else:
            datos["adelanto"] = 0
            datos["saldo_pendiente"] = 0
            datos["estado"] = "pagado"
            datos["frecuencia_cobro"] = None
            datos["proxima_fecha_cobro"] = None

        venta = sb.table("ventas").insert(datos).execute()
        flash("Venta registrada correctamente", "success")
        return redirect(url_for("ventas.detalle", venta_id=venta.data[0]["id"]))

    productos = (
        sb.table("productos")
        .select("id, nombre, precio_venta, imagen_url")
        .eq("activo", True)
        .order("nombre")
        .execute()
        .data
    )

    cliente_prefill = None
    cliente_id_qs = request.args.get("cliente_id")
    if cliente_id_qs:
        cliente_prefill = sb.table("clientes").select("id, nombres, celular").eq("id", cliente_id_qs).single().execute().data

    return render_template(
        "ventas/nueva.html",
        productos=productos,
        producto_id_prefill=request.args.get("producto_id", ""),
        cliente_prefill=cliente_prefill,
    )


@ventas_bp.route("/por-cobrar")
@login_required
def por_cobrar():
    sb = get_supabase()
    hoy = hoy_peru().isoformat()
    ventas = (
        sb.table("ventas")
        .select("id, saldo_pendiente, proxima_fecha_cobro, clientes(nombres, celular), productos(nombre)")
        .eq("estado", "pendiente")
        .order("proxima_fecha_cobro")
        .execute()
        .data
    )
    for v in ventas:
        v["link_whatsapp"] = link_whatsapp_recordatorio_cobro(v)
    return render_template("ventas/por_cobrar.html", ventas=ventas, hoy=hoy)


@ventas_bp.route("/<venta_id>")
@login_required
def detalle(venta_id):
    sb = get_supabase()
    venta = (
        sb.table("ventas")
        .select("*, clientes(id, nombres, celular), productos(id, nombre, imagen_url)")
        .eq("id", venta_id)
        .single()
        .execute()
        .data
    )
    cobros = (
        sb.table("cobros")
        .select("*")
        .eq("venta_id", venta_id)
        .order("fecha_cobro", desc=True)
        .execute()
        .data
    )
    return render_template("ventas/detalle.html", venta=venta, cobros=cobros, hoy=hoy_peru().isoformat())


@ventas_bp.route("/<venta_id>/cobro", methods=["POST"])
@login_required
def registrar_cobro(venta_id):
    sb = get_supabase()
    monto = float(request.form["monto"])
    if monto <= 0:
        flash("El monto del cobro debe ser mayor a cero.", "error")
        return redirect(url_for("ventas.detalle", venta_id=venta_id))

    sb.table("cobros").insert(
        {
            "venta_id": venta_id,
            "fecha_cobro": request.form.get("fecha_cobro") or hoy_peru().isoformat(),
            "monto": monto,
            "metodo_pago": request.form.get("metodo_pago", "efectivo"),
            "notas": request.form.get("notas", "").strip() or None,
            "registrado_por": current_user.id,
        }
    ).execute()
    cobros_service.recalcular_venta(venta_id)
    flash("Cobro registrado", "success")
    return redirect(url_for("ventas.detalle", venta_id=venta_id))


@ventas_bp.route("/<venta_id>/proxima-fecha", methods=["POST"])
@login_required
def actualizar_proxima_fecha(venta_id):
    """Permite ajustar a mano la próxima fecha de cobro (frecuencia 'manual' o
    cuando el cliente pide reprogramar)."""
    sb = get_supabase()
    nueva_fecha = request.form.get("proxima_fecha_cobro") or None
    sb.table("ventas").update({"proxima_fecha_cobro": nueva_fecha}).eq("id", venta_id).execute()
    flash("Próxima fecha de cobro actualizada", "success")
    return redirect(url_for("ventas.detalle", venta_id=venta_id))
