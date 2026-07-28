-- Ejecutar en el SQL Editor de Supabase (proyecto nuevo, capa gratuita)
-- Sistema de ventas (contado / credito) con catalogo de productos.
-- App estatica: se accede directo desde el navegador con la publishable
-- key + Supabase Auth (sin backend propio), por eso todas las tablas usan
-- Row Level Security.

create extension if not exists "pgcrypto";

create sequence ventas_codigo_seq start 1;

create table clientes (
  id uuid primary key default gen_random_uuid(),
  nombres text not null,
  celular text not null,
  dni text,
  direccion text,
  creado_en timestamptz not null default now()
);

create table productos (
  id uuid primary key default gen_random_uuid(),
  nombre text not null,
  descripcion text,
  categoria text not null default 'otro',
  marca text,
  costo numeric(10,2) not null default 0,
  precio_venta numeric(10,2) not null,
  stock integer,
  imagen_url text,
  imagen_url_2 text,
  imagen_url_3 text,
  origen text not null default 'manual',
  url_referencia text,
  precio_referencia numeric(10,2),
  activo boolean not null default true,
  creado_en timestamptz not null default now()
);

create table ventas (
  id uuid primary key default gen_random_uuid(),
  codigo text default ('VT-' || lpad(nextval('ventas_codigo_seq')::text, 6, '0')),
  cliente_id uuid not null references clientes(id),
  producto_id uuid not null references productos(id),
  cantidad integer not null default 1,
  precio_unitario numeric(10,2) not null,
  costo_unitario numeric(10,2) not null,
  monto_total numeric(10,2) not null,
  tipo_venta text not null check (tipo_venta in ('contado', 'credito')),
  adelanto numeric(10,2) not null default 0,
  frecuencia_cobro text check (frecuencia_cobro in ('quincena', 'fin_de_mes', 'manual')),
  proxima_fecha_cobro date,
  saldo_pendiente numeric(10,2) not null default 0,
  estado text not null default 'pagado' check (estado in ('pagado', 'pendiente')),
  fecha_venta date not null default current_date,
  notas text,
  creado_por uuid references auth.users(id),
  creado_en timestamptz not null default now()
);

create table cobros (
  id uuid primary key default gen_random_uuid(),
  venta_id uuid not null references ventas(id),
  fecha_cobro date not null default current_date,
  monto numeric(10,2) not null,
  metodo_pago text not null default 'efectivo' check (metodo_pago in ('efectivo', 'yape', 'transferencia')),
  notas text,
  registrado_por uuid references auth.users(id),
  creado_en timestamptz not null default now()
);

create index idx_ventas_cliente on ventas(cliente_id);
create index idx_ventas_producto on ventas(producto_id);
create index idx_ventas_estado on ventas(estado);
create index idx_cobros_venta on cobros(venta_id);

-- Row Level Security: la publishable key SI respeta RLS (a diferencia de la
-- service_role que usaba la version anterior con backend Flask). Cualquier
-- usuario de Supabase Auth logueado tiene acceso completo -- es un sistema
-- de 1-2 personas de confianza, no hace falta granularidad por fila.
alter table clientes enable row level security;
alter table productos enable row level security;
alter table ventas enable row level security;
alter table cobros enable row level security;

create policy "auth_full_access" on clientes for all to authenticated using (true) with check (true);
create policy "auth_full_access" on productos for all to authenticated using (true) with check (true);
create policy "auth_full_access" on ventas for all to authenticated using (true) with check (true);
create policy "auth_full_access" on cobros for all to authenticated using (true) with check (true);

-- Politicas de Storage (bucket "productos", debe crearse como publico desde
-- el dashboard): la lectura publica ya la da el bucket publico, esto
-- habilita subir/editar/borrar desde el navegador autenticado.
create policy "auth_upload_productos" on storage.objects for insert to authenticated with check (bucket_id = 'productos');
create policy "auth_update_productos" on storage.objects for update to authenticated using (bucket_id = 'productos');
create policy "auth_delete_productos" on storage.objects for delete to authenticated using (bucket_id = 'productos');

-- Si al crear el proyecto desactivaste "Automatically expose new tables",
-- el rol `authenticated` no recibe permisos de tabla por defecto (RLS solo
-- controla filas, no la tabla en si) -- sin esto la app falla con
-- "permission denied for table X":
grant select, insert, update, delete on clientes, productos, ventas, cobros to authenticated;
grant usage, select on sequence ventas_codigo_seq to authenticated;

-- Crear los usuarios de acceso desde Authentication > Users en el dashboard
-- de Supabase (o via el admin API) -- no hay registro publico.
