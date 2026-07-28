import io
import uuid

from PIL import Image, ImageOps

from ..supabase_client import get_supabase

TAMANO_MAXIMO_LADO = 1600
UMBRAL_COMPRESION_BYTES = 500 * 1024  # 500 KB
EXTENSIONES_PERMITIDAS = {"jpg", "jpeg", "png", "webp", "heic", "heif"}
TAMANO_MAXIMO_SUBIDA_BYTES = 15 * 1024 * 1024  # 15 MB


class ArchivoInvalido(Exception):
    """Se lanza cuando el archivo subido no es una imagen valida o excede el tamano permitido."""


def _comprimir_si_corresponde(contenido: bytes, mimetype: str):
    """Si es una imagen pesada, la reescala/recomprime a JPEG.

    Devuelve (contenido, extension_forzada_o_None, content_type).
    """
    if not (mimetype or "").startswith("image/"):
        return contenido, None, mimetype

    if len(contenido) <= UMBRAL_COMPRESION_BYTES:
        return contenido, None, mimetype

    try:
        imagen = Image.open(io.BytesIO(contenido))
        imagen = ImageOps.exif_transpose(imagen)
        if imagen.mode != "RGB":
            imagen = imagen.convert("RGB")
        imagen.thumbnail((TAMANO_MAXIMO_LADO, TAMANO_MAXIMO_LADO))
        salida = io.BytesIO()
        imagen.save(salida, format="JPEG", quality=82, optimize=True)
        return salida.getvalue(), "jpg", "image/jpeg"
    except Exception:
        return contenido, None, mimetype


def subir_archivo(bucket: str, file_storage, carpeta: str = "") -> str:
    """Sube un archivo (FileStorage de Flask) a Supabase Storage y devuelve su URL publica."""
    sb = get_supabase()
    nombre_original = file_storage.filename or "archivo.jpg"
    ext = nombre_original.rsplit(".", 1)[-1].lower() if "." in nombre_original else ""
    content_type = file_storage.mimetype or ""

    if ext not in EXTENSIONES_PERMITIDAS or not content_type.startswith("image/"):
        raise ArchivoInvalido("Solo se permiten imágenes (jpg, png, webp, heic).")

    contenido = file_storage.read()
    if len(contenido) > TAMANO_MAXIMO_SUBIDA_BYTES:
        raise ArchivoInvalido("La imagen supera el tamaño máximo permitido (15 MB).")

    contenido, ext_forzada, content_type = _comprimir_si_corresponde(contenido, content_type)
    if ext_forzada:
        ext = ext_forzada

    ruta = f"{carpeta}/{uuid.uuid4()}.{ext}" if carpeta else f"{uuid.uuid4()}.{ext}"
    sb.storage.from_(bucket).upload(ruta, contenido, {"content-type": content_type})
    return sb.storage.from_(bucket).get_public_url(ruta)


def subir_bytes(bucket: str, contenido: bytes, content_type: str, carpeta: str = "") -> str:
    """Sube bytes ya descargados (ej. imagen scrapeada de otra tienda) a Supabase Storage."""
    sb = get_supabase()
    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(content_type, "jpg")
    contenido, ext_forzada, content_type = _comprimir_si_corresponde(contenido, content_type)
    if ext_forzada:
        ext = ext_forzada
    ruta = f"{carpeta}/{uuid.uuid4()}.{ext}" if carpeta else f"{uuid.uuid4()}.{ext}"
    sb.storage.from_(bucket).upload(ruta, contenido, {"content-type": content_type})
    return sb.storage.from_(bucket).get_public_url(ruta)
