import requests
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from ..services import scraper_producto
from ..services.storage import ArchivoInvalido, subir_archivo, subir_bytes
from ..services.whatsapp import link_whatsapp_producto
from ..supabase_client import get_supabase

productos_bp = Blueprint("productos", __name__, url_prefix="/productos")

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)


@productos_bp.route("/")
@login_required
def listar():
    sb = get_supabase()
    productos = (
        sb.table("productos")
        .select("*")
        .eq("activo", True)
        .order("creado_en", desc=True)
        .execute()
        .data
    )
    return render_template("productos/listar.html", productos=productos)


@productos_bp.route("/scrape-link", methods=["POST"])
@login_required
def scrape_link():
    url = (request.get_json(silent=True) or {}).get("url", "").strip()
    if not url:
        return jsonify({"ok": False, "error": "Falta la URL del producto."}), 400
    try:
        datos = scraper_producto.obtener_datos_producto(url)
    except scraper_producto.ScrapingNoSoportado as exc:
        return jsonify({"ok": False, "error": str(exc)}), 422
    except scraper_producto.ScrapingFallido as exc:
        return jsonify({"ok": False, "error": str(exc)}), 502
    return jsonify({"ok": True, "datos": datos})


def _descargar_e_importar_imagen(imagen_url: str) -> str | None:
    """Descarga una imagen de una tienda externa y la re-sube a Storage propio,
    para no depender de que el CDN original la siga sirviendo."""
    try:
        resp = requests.get(imagen_url, headers={"User-Agent": _USER_AGENT}, timeout=20)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "image/jpeg").split(";")[0]
        return subir_bytes("productos", resp.content, content_type, "catalogo")
    except Exception:
        return None


@productos_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        sb = get_supabase()
        origen = request.form.get("origen", "manual")

        imagenes_urls = [None, None, None]
        try:
            if origen == "scrapeado":
                seleccionadas = request.form.getlist("imagen_scrapeada")[:3]
                for i, url_img in enumerate(seleccionadas):
                    imagenes_urls[i] = _descargar_e_importar_imagen(url_img)
            else:
                if request.files.get("imagen") and request.files["imagen"].filename:
                    imagenes_urls[0] = subir_archivo("productos", request.files["imagen"], "catalogo")
        except ArchivoInvalido as error:
            flash(str(error), "error")
            return redirect(url_for("productos.nuevo"))

        sb.table("productos").insert(
            {
                "nombre": request.form["nombre"].strip(),
                "descripcion": request.form.get("descripcion", "").strip() or None,
                "categoria": request.form.get("categoria", "otro").strip() or "otro",
                "marca": request.form.get("marca", "").strip() or None,
                "costo": float(request.form.get("costo") or 0),
                "precio_venta": float(request.form["precio_venta"]),
                "stock": int(request.form["stock"]) if request.form.get("stock") else None,
                "imagen_url": imagenes_urls[0],
                "imagen_url_2": imagenes_urls[1],
                "imagen_url_3": imagenes_urls[2],
                "origen": origen,
                "url_referencia": request.form.get("url_referencia", "").strip() or None,
                "precio_referencia": float(request.form["precio_referencia"])
                if request.form.get("precio_referencia")
                else None,
            }
        ).execute()
        flash("Producto agregado al catálogo", "success")
        return redirect(url_for("productos.listar"))
    return render_template("productos/nuevo.html")


@productos_bp.route("/<producto_id>/editar", methods=["GET", "POST"])
@login_required
def editar(producto_id):
    sb = get_supabase()
    if request.method == "POST":
        datos = {
            "nombre": request.form["nombre"].strip(),
            "descripcion": request.form.get("descripcion", "").strip() or None,
            "categoria": request.form.get("categoria", "otro").strip() or "otro",
            "marca": request.form.get("marca", "").strip() or None,
            "costo": float(request.form.get("costo") or 0),
            "precio_venta": float(request.form["precio_venta"]),
            "stock": int(request.form["stock"]) if request.form.get("stock") else None,
            "activo": request.form.get("activo") == "on",
        }
        try:
            if request.files.get("imagen") and request.files["imagen"].filename:
                datos["imagen_url"] = subir_archivo("productos", request.files["imagen"], "catalogo")
        except ArchivoInvalido as error:
            flash(str(error), "error")
            return redirect(url_for("productos.editar", producto_id=producto_id))

        sb.table("productos").update(datos).eq("id", producto_id).execute()
        flash("Producto actualizado", "success")
        return redirect(url_for("productos.detalle", producto_id=producto_id))
    producto = sb.table("productos").select("*").eq("id", producto_id).single().execute().data
    return render_template("productos/editar.html", producto=producto)


@productos_bp.route("/<producto_id>")
@login_required
def detalle(producto_id):
    sb = get_supabase()
    producto = sb.table("productos").select("*").eq("id", producto_id).single().execute().data
    link_compartir = link_whatsapp_producto(producto)
    return render_template("productos/detalle.html", producto=producto, link_compartir=link_compartir)
