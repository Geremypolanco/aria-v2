-- ============================================================
-- Aria V2 — Supabase Schema
-- Ejecutar en: Supabase Dashboard > SQL Editor
-- ============================================================

-- Usuarios (sincronizados desde Google OAuth)
create table if not exists public.users (
  id          text primary key,           -- google sub
  email       text unique not null,
  name        text not null default '',
  picture     text not null default '',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- Conversaciones
create table if not exists public.conversations (
  id          uuid primary key default gen_random_uuid(),
  user_id     text not null references public.users(id) on delete cascade,
  created_at  timestamptz not null default now()
);
create index if not exists conversations_user_id_idx on public.conversations(user_id);

-- Mensajes
create table if not exists public.messages (
  id                uuid primary key default gen_random_uuid(),
  conversation_id   uuid not null references public.conversations(id) on delete cascade,
  role              text not null check (role in ('user', 'assistant')),
  content           text not null,
  created_at        timestamptz not null default now()
);
create index if not exists messages_conversation_id_idx on public.messages(conversation_id);
-- Índice para búsqueda full-text
create index if not exists messages_content_fts_idx on public.messages using gin(to_tsvector('spanish', content));

-- Productos digitales
create table if not exists public.products (
  id            uuid primary key default gen_random_uuid(),
  user_id       text not null references public.users(id) on delete cascade,
  type          text not null check (type in ('course', 'ebook', 'bundle')),
  title         text not null,
  topic         text not null default '',
  description   text not null default '',
  price         numeric(10,2) not null default 0,
  status        text not null default 'draft' check (status in ('draft', 'published', 'archived')),
  content_json  jsonb,
  created_at    timestamptz not null default now()
);
create index if not exists products_user_id_idx on public.products(user_id);
create index if not exists products_status_idx on public.products(status);

-- RLS: cada usuario solo ve sus propios datos
alter table public.users         enable row level security;
alter table public.conversations  enable row level security;
alter table public.messages       enable row level security;
alter table public.products       enable row level security;

-- Políticas (el backend usa service_role key que bypasea RLS)
create policy "service role bypass" on public.users         for all using (true);
create policy "service role bypass" on public.conversations  for all using (true);
create policy "service role bypass" on public.messages       for all using (true);
create policy "service role bypass" on public.products       for all using (true);
