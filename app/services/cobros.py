from calendar import monthrange
from datetime import date, timedelta

from ..supabase_client import get_supabase


def _fin_de_mes(fecha_base: date) -> date:
    ultimo_dia_mes_actual = monthrange(fecha_base.year, fecha_base.month)[1]
    fin_mes_actual = date(fecha_base.year, fecha_base.month, ultimo_dia_mes_actual)
    if fecha_base < fin_mes_actual:
        return fin_mes_actual
    # Ya estamos en (o despues de) el ultimo dia del mes: programar para el siguiente.
    mes, anio = fecha_base.month + 1, fecha_base.year
    if mes > 12:
        mes, anio = 1, anio + 1
    ultimo_dia_siguiente = monthrange(anio, mes)[1]
    return date(anio, mes, ultimo_dia_siguiente)


def calcular_proxima_fecha(frecuencia: str, fecha_base: date, fecha_manual: date | None = None):
    """Fecha sugerida del proximo cobro segun la frecuencia pactada con el cliente."""
    if frecuencia == "quincena":
        return fecha_base + timedelta(days=15)
    if frecuencia == "fin_de_mes":
        return _fin_de_mes(fecha_base)
    if frecuencia == "manual":
        return fecha_manual
    return None


def recalcular_venta(venta_id: str) -> dict:
    """Recalcula saldo_pendiente, estado y proxima_fecha_cobro de una venta a credito
    a partir de sus cobros registrados, y guarda los cambios en Supabase.

    Se centraliza aca porque se necesita tanto al registrar un cobro nuevo como
    al editar/borrar uno existente.
    """
    sb = get_supabase()
    venta = sb.table("ventas").select("*").eq("id", venta_id).single().execute().data
    if venta["tipo_venta"] != "credito":
        return venta

    cobros = sb.table("cobros").select("monto, fecha_cobro").eq("venta_id", venta_id).execute().data
    total_cobrado = sum(float(c["monto"]) for c in cobros)
    saldo = round(float(venta["monto_total"]) - float(venta["adelanto"]) - total_cobrado, 2)
    saldo = max(saldo, 0)

    datos = {"saldo_pendiente": saldo}
    if saldo <= 0:
        datos["estado"] = "pagado"
        datos["proxima_fecha_cobro"] = None
    else:
        datos["estado"] = "pendiente"
        if venta["frecuencia_cobro"] in ("quincena", "fin_de_mes") and cobros:
            ultima_fecha = max(date.fromisoformat(c["fecha_cobro"]) for c in cobros)
            datos["proxima_fecha_cobro"] = calcular_proxima_fecha(
                venta["frecuencia_cobro"], ultima_fecha
            ).isoformat()
        # frecuencia 'manual' o sin cobros aun: se deja la proxima_fecha_cobro como esta,
        # el usuario la ajusta a mano si hace falta.

    sb.table("ventas").update(datos).eq("id", venta_id).execute()
    venta.update(datos)
    return venta
