"""Trae nombre/imagenes/precio/descripcion de la pagina de UN producto
pegando su link, para precargar el formulario de "nuevo producto".

A diferencia del scraper de listados del proyecto de prestamos (que necesita
Playwright porque el listado se renderiza 100% client-side), la pagina de
DETALLE de producto de Falabella trae un bloque
<script type="application/ld+json"> con los datos del producto (schema.org
Product) ya en el HTML inicial -- confirmado bajando una pagina real con
requests. No hace falta navegador headless.

Para agregar otra tienda: sumar su dominio a `_PARSERS` con una funcion que
reciba el HTML (str) y devuelva el mismo dict que `_parse_falabella`.
"""
import html
import json
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)


class ScrapingNoSoportado(Exception):
    """La URL no pertenece a una tienda soportada todavia."""


class ScrapingFallido(Exception):
    """La tienda es soportada pero no se pudo extraer el producto (pagina caida, cambio de estructura, etc.)."""


def _limpiar_descripcion(desc_raw: str) -> str:
    if not desc_raw:
        return ""
    # Falabella escapa el HTML de la descripcion dos veces (&amp;lt;h2&amp;gt;...).
    desc = html.unescape(html.unescape(desc_raw))
    return BeautifulSoup(desc, "html.parser").get_text("\n").strip()


def _parse_falabella(pagina_html: str) -> dict:
    soup = BeautifulSoup(pagina_html, "html.parser")
    producto_ld = None
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string)
        except (TypeError, ValueError):
            continue
        if isinstance(data, dict) and data.get("@type") == "Product":
            producto_ld = data
            break

    if producto_ld is None:
        raise ScrapingFallido("No se encontró la información del producto en esa página.")

    nombre = html.unescape(producto_ld.get("name") or "").strip()

    marca = None
    brand = producto_ld.get("brand")
    if isinstance(brand, dict):
        marca = brand.get("name")

    imagenes = producto_ld.get("image") or []
    if isinstance(imagenes, str):
        imagenes = [imagenes]
    imagenes = [i for i in imagenes if i][:3]

    offers = producto_ld.get("offers") or []
    if isinstance(offers, dict):
        offers = [offers]
    precios = []
    for offer in offers:
        try:
            precios.append(float(offer.get("price")))
        except (TypeError, ValueError):
            continue
    precio_referencia = min(precios) if precios else None

    descripcion = _limpiar_descripcion(producto_ld.get("description") or "")

    if not nombre:
        raise ScrapingFallido("La página no trajo el nombre del producto.")

    return {
        "nombre": nombre,
        "marca": marca,
        "imagenes": imagenes,
        "precio_referencia": precio_referencia,
        "descripcion": descripcion,
    }


_PARSERS = {
    "www.falabella.com.pe": _parse_falabella,
    "falabella.com.pe": _parse_falabella,
}


def obtener_datos_producto(url: str) -> dict:
    """Devuelve {nombre, marca, imagenes: [...], precio_referencia, descripcion} para `url`."""
    dominio = urlparse(url).netloc.lower()
    parser = _PARSERS.get(dominio)
    if parser is None:
        raise ScrapingNoSoportado(
            f"Todavía no se soporta la tienda de esa URL ({dominio or 'desconocida'})."
        )

    try:
        resp = requests.get(url, headers={"User-Agent": _USER_AGENT}, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise ScrapingFallido(f"No se pudo abrir esa página: {exc}") from exc

    return parser(resp.text)
