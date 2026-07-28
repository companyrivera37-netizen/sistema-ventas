# Sistema de Ventas

App de una sola página (`index.html`) para registrar ventas al contado y al
crédito (con adelanto y cuotas programadas), con catálogo de productos y un
panel de inversión/ganancia. Corre 100% en el navegador, sin backend propio:
habla directo con Supabase usando `supabase-js` y la `publishable key`.
Pensada para usarse desde el celular, alojada gratis en GitHub Pages.

## Cómo funciona

- **Login**: Supabase Auth (correo + contraseña) — los usuarios se crean
  desde el dashboard de Supabase (Authentication > Users), no hay registro
  público.
- **Productos**: catálogo con foto, costo (tu inversión) y precio de venta.
  Se cargan a mano (nombre, categoría, costo, precio, foto). Cada producto
  tiene una ficha con botón para compartir la info completa por WhatsApp.
- **Nueva venta**: eliges el producto de una galería de imágenes, buscas o
  creas el cliente, y eliges contado o crédito. En crédito puedes registrar
  un adelanto y programar el cobro del saldo por quincena, fin de mes, o
  una fecha específica.
- **Cobros**: en cada venta a crédito registras los pagos parciales que
  recibes; el saldo y la próxima fecha de cobro se recalculan solos, hasta
  que la venta queda pagada.
- **Por cobrar**: lista de todos los créditos pendientes ordenada por fecha,
  con un botón para recordarle el pago al cliente por WhatsApp.
- **Inicio**: cuánto has cobrado, cuánto te falta cobrar, tu inversión
  (costo de lo vendido) y tu ganancia realizada (la parte de lo ya cobrado
  que supera el costo — sube conforme cobras cada cuota).

## 1. Configurar Supabase

1. Crea un proyecto en https://supabase.com (o usa el que ya tengas para
   este sistema).
2. **SQL Editor** → corre [`supabase/schema.sql`](supabase/schema.sql)
   completo (crea las tablas, activa Row Level Security, y da los permisos
   necesarios al rol `authenticated`).
3. **Storage** → crea un bucket público llamado `productos`.
4. **Authentication > Users** → **Add user** para cada persona que vaya a
   usar el sistema (correo + contraseña, marcar "Auto Confirm User").
5. **Project Settings > API Keys** → copia la **Publishable key**
   (`sb_publishable_...`, no la Secret) y el **Project ID** (para armar la
   URL `https://<project-id>.supabase.co`).

## 2. Configurar `index.html`

Abre `index.html` y edita estas dos líneas cerca del inicio del `<script>`:

```js
const SB_URL = 'https://tu-project-id.supabase.co';
const SB_KEY = 'sb_publishable_xxxxxxxxxxxxxxxxxxxx';
```

La `publishable key` es segura para dejar directo en el archivo (a
diferencia de la `secret key`, que nunca debe ir aquí) — el control de
acceso real lo dan las políticas de Row Level Security del paso anterior.

## 3. Probar localmente

Cualquier servidor estático sirve, por ejemplo:
```
python -m http.server 8000
```
y abre http://localhost:8000/index.html

## 4. Publicar en GitHub Pages

1. Sube `index.html` a la rama `main` del repo (raíz, no en una subcarpeta).
2. En GitHub: **Settings → Pages** → **Source: Deploy from a branch** →
   **Branch: main / (root)** → **Save**.
3. Espera 1-2 minutos; el link queda en
   `https://<tu-usuario>.github.io/<nombre-del-repo>/`.

Cualquier cambio futuro: edita `index.html`, haz commit y push — GitHub
Pages lo re-publica solo en 1-2 minutos.
