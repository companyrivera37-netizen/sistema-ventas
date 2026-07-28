from collections import defaultdict

from flask import Blueprint, render_template
from flask_login import login_required

from ..services.fecha import hoy_peru
from ..supabase_client import get_supabase

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    sb = get_supabase()
    hoy = hoy_peru()

    ventas = (
        sb.table("ventas")
        .select(
            "id, tipo_venta, monto_total, costo_unitario, cantidad, adelanto, saldo_pendiente, "
            "estado, proxima_fecha_cobro, fecha_venta, clientes(nombres), productos(nombre)"
        )
        .execute()
        .data
    )

    cobros = sb.table("cobros").select("venta_id, monto").execute().data
    cobrado_por_venta = defaultdict(float)
    for c in cobros:
        cobrado_por_venta[c["venta_id"]] += float(c["monto"])

    total_cobrado = 0.0
    total_inversion = 0.0
    total_por_cobrar = 0.0
    ganancia_realizada = 0.0

    for v in ventas:
        costo_total_venta = float(v["costo_unitario"]) * v["cantidad"]
        total_inversion += costo_total_venta

        if v["tipo_venta"] == "contado":
            cobrado_venta = float(v["monto_total"])
        else:
            cobrado_venta = float(v["adelanto"]) + cobrado_por_venta.get(v["id"], 0.0)
            total_por_cobrar += float(v["saldo_pendiente"])

        total_cobrado += cobrado_venta

        # Ganancia realizada: solo la porcion de lo ya cobrado que corresponde
        # al margen de la venta (no al costo). Sube conforme se cobran cuotas.
        monto_total = float(v["monto_total"])
        if monto_total > 0:
            margen_venta = monto_total - costo_total_venta
            ganancia_realizada += cobrado_venta * (margen_venta / monto_total)

    pendientes = [v for v in ventas if v["estado"] == "pendiente"]
    pendientes.sort(key=lambda v: v["proxima_fecha_cobro"] or "9999-99-99")

    return render_template(
        "dashboard.html",
        total_cobrado=total_cobrado,
        total_por_cobrar=total_por_cobrar,
        total_inversion=total_inversion,
        ganancia_realizada=ganancia_realizada,
        pendientes=pendientes[:5],
        hoy=hoy.isoformat(),
    )
