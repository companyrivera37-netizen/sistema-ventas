# Sistema de Ventas

Panel para registrar ventas al contado y al crédito (con adelanto y cuotas
programadas), con un catálogo de productos que se puede llenar pegando el
link de un producto de Falabella (trae nombre/imagen/precio/descripción
automáticamente) o cargando un producto manualmente (ej. ropa).

Construido con Flask + Supabase (Postgres + Storage), pensado para
desplegar gratis en Render. Mismo patrón que el proyecto PrestaYa.

## 1. Crear el proyecto en Supabase

1. Entra a https://supabase.com y crea un proyecto **nuevo** (no reutilices
   el de otro sistema).
2. Ve a **Project Settings > API** y copia:
   - `Project URL` → `SUPABASE_URL`
   - `service_role` key (no la `anon`) → `SUPABASE_SERVICE_KEY`
3. Ve a **SQL Editor** y ejecuta el contenido de
   [`supabase/schema.sql`](supabase/schema.sql).
4. Ve a **Storage** y crea un bucket público llamado `productos` (para las
   fotos del catálogo).
5. Si desactivaste "Automatically expose new tables", corre también:
   ```sql
   grant all privileges on all tables in schema public to service_role;
   alter default privileges in schema public grant all privileges on tables to service_role;
   ```

## 2. Configurar el entorno local

```
cp .env.example .env
```
Pega ahí `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, una `SECRET_KEY` larga y
aleatoria, y opcionalmente `EMPRESA_NOMBRE` / `EMPRESA_WHATSAPP`.

```
python -m venv venv
./venv/Scripts/python.exe -m pip install -r requirements.txt
```

## 3. Crear el primer usuario

```
./venv/Scripts/python.exe scripts/crear_usuario.py "Tu Nombre" tu@correo.com "tu-clave"
```

## 4. Correr localmente

```
./venv/Scripts/python.exe run.py
```
Abre http://localhost:5000

## 5. Desplegar en Render

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn run:app`
- Variables de entorno: pega el contenido de tu `.env` con el botón
  "Add from .env" del panel de Render.
- Plan Free: el servicio "duerme" a los 15 min sin tráfico, el primer
  request tarda 30-60s en responder.

## Cómo funciona

- **Catálogo de productos** (`/productos`): pega un link de un producto de
  Falabella y trae automáticamente nombre, imágenes, precio de referencia y
  descripción; tú completas el costo (tu inversión) y el precio de venta.
  También puedes cargar un producto manualmente (ej. ropa) con foto propia.
  Cada producto tiene una ficha (`/productos/<id>`) con botón para
  compartir toda la información por WhatsApp cuando un cliente pregunte.
- **Nueva venta** (`/ventas/nueva`): eliges el producto de una galería de
  imágenes, buscas o creas el cliente, y eliges contado o crédito. En
  crédito puedes registrar un adelanto y programar el cobro del saldo por
  quincena, fin de mes, o una fecha específica.
- **Cobros**: en la ficha de cada venta a crédito (`/ventas/<id>`) registras
  cada pago parcial que recibes; el saldo y la próxima fecha de cobro se
  recalculan solos, hasta que la venta queda pagada.
- **Inicio** (`/`): cuánto has cobrado, cuánto te falta cobrar, tu inversión
  (costo de lo vendido) y tu ganancia realizada (la parte de lo ya cobrado
  que supera el costo — sube conforme cobras cada cuota), más la lista de
  créditos pendientes ordenada por fecha de cobro (resaltando los vencidos).
