from urllib.parse import quote


def normalizar_celular_pe(celular: str) -> str:
    numero = "".join(ch for ch in (celular or "") if ch.isdigit())
    if len(numero) == 9 and numero.startswith("9"):
        numero = "51" + numero
    return numero


def link_whatsapp_producto(producto: dict, celular: str | None = None) -> str:
    """Link de WhatsApp con la ficha del producto lista para enviar a un cliente.

    Solo nombre + descripcion completa (sin marca ni precio, y sin recortar
    la descripcion a la mitad) -- es informacion para que el cliente conozca
    el producto, no una cotizacion.

    Si no se pasa celular, genera un link "abierto" (sin numero) para que el
    usuario elija el contacto desde su propio WhatsApp.
    """
    partes = [producto["nombre"]]
    if producto.get("descripcion"):
        partes.append(producto["descripcion"].strip())
    mensaje = "\n\n".join(partes)

    if celular:
        numero = normalizar_celular_pe(celular)
        return f"https://wa.me/{numero}?text={quote(mensaje)}"
    return f"https://wa.me/?text={quote(mensaje)}"


def link_whatsapp_recordatorio_cobro(venta: dict) -> str:
    """Link de WhatsApp para recordarle a un cliente su saldo pendiente."""
    cliente = venta.get("clientes") or {}
    producto = venta.get("productos") or {}
    mensaje = (
        f"Hola {cliente.get('nombres', '')}, te recuerdo que tienes un saldo pendiente de "
        f"S/ {venta['saldo_pendiente']:.2f} por {producto.get('nombre', 'tu compra')}"
        + (f", con cobro programado para el {venta['proxima_fecha_cobro']}." if venta.get("proxima_fecha_cobro") else ".")
    )
    numero = normalizar_celular_pe(cliente.get("celular", ""))
    return f"https://wa.me/{numero}?text={quote(mensaje)}"
