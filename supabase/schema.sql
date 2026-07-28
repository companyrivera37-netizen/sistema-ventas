-- Ejecutar en el SQL Editor de Supabase (proyecto nuevo, capa gratuita)
-- Sistema de ventas (contado / credito) con catalogo de productos.

create extension if not exists "pgcrypto";

create sequence ventas_codigo_seq start 1;

create table usuarios (
  id uuid primary key default gen_random_uuid(),
  nombre text not null,
  email text not null unique,
  password_hash text not null,
  rol text not null default 'admin',
  creado_en timestamptz not null default now()
);

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
  origen text not null default 'manual',   -- 'scrapeado' | 'manual'
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
  creado_por uuid references usuarios(id),
  creado_en timestamptz not null default now()
);

create table cobros (
  id uuid primary key default gen_random_uuid(),
  venta_id uuid not null references ventas(id),
  fecha_cobro date not null default current_date,
  monto numeric(10,2) not null,
  metodo_pago text not null default 'efectivo' check (metodo_pago in ('efectivo', 'yape', 'transferencia')),
  notas text,
  registrado_por uuid references usuarios(id),
  creado_en timestamptz not null default now()
);

create index idx_ventas_cliente on ventas(cliente_id);
create index idx_ventas_producto on ventas(producto_id);
create index idx_ventas_estado on ventas(estado);
create index idx_cobros_venta on cobros(venta_id);

-- Nota de seguridad: esta app accede a Supabase SOLO desde el backend Flask
-- usando la service_role key (nunca se expone al navegador), por lo que no
-- se definen politicas de Row Level Security: el control de acceso vive en
-- el servidor Flask (login de staff + rutas protegidas).

-- Si al crear el proyecto desactivaste "Automatically expose new tables",
-- corre tambien esto para que el service_role tenga permisos (incluye las
-- secuencias: sin esto, insertar en `ventas` falla con "permission denied
-- for sequence ventas_codigo_seq" porque el codigo VT-000001 se genera con
-- nextval() en esa secuencia):
-- grant all privileges on all tables in schema public to service_role;
-- grant all privileges on all sequences in schema public to service_role;
-- alter default privileges in schema public grant all privileges on tables to service_role;
-- alter default privileges in schema public grant all privileges on sequences to service_role;
