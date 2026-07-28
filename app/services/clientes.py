from ..supabase_client import get_supabase


def buscar(termino: str, limite: int = 8) -> list[dict]:
    """Busca clientes por nombre o celular (usado en el autocompletado de 'nueva venta'
    y en el buscador del listado de clientes).

    Dos consultas separadas (una por nombre, otra por celular) en vez de un
    solo `.or_()` con el termino interpolado en la cadena de filtro de
    PostgREST: evita que un termino con comas/parentesis rompa o altere la
    sintaxis del filtro.
    """
    termino = (termino or "").strip()
    if not termino:
        return []
    sb = get_supabase()
    patron = f"%{termino}%"
    por_nombre = (
        sb.table("clientes")
        .select("id, nombres, celular, direccion, creado_en")
        .ilike("nombres", patron)
        .limit(limite)
        .execute()
        .data
    )
    por_celular = (
        sb.table("clientes")
        .select("id, nombres, celular, direccion, creado_en")
        .ilike("celular", patron)
        .limit(limite)
        .execute()
        .data
    )
    vistos = {}
    for c in por_nombre + por_celular:
        vistos[c["id"]] = c
    return sorted(vistos.values(), key=lambda c: c["nombres"])[:limite]
