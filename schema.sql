-- ============================================================
-- Aria V2 — Supabase Schema
-- Run this in: Supabase Dashboard → SQL Editor → New query
-- ============================================================

-- Users (synced from Google OAuth)
create table if not exists public.users (
  id          text primary key,              -- Google sub
  email       text unique not null,
  name        text not null default '',
  picture     text not null default '',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- Conversations
create table if not exists public.conversations (
  id          uuid primary key default gen_random_uuid(),
  user_id     text not null references public.users(id) on delete cascade,
  created_at  timestamptz not null default now()
);
create index if not exists idx_conversations_user on public.conversations(user_id);

-- Messages
create table if not exists public.messages (
  id                uuid primary key default gen_random_uuid(),
  conversation_id   uuid not null references public.conversations(id) on delete cascade,
  role              text not null check (role in ('user', 'assistant')),
  content           text not null,
  created_at        timestamptz not null default now()
);
create index if not exists idx_messages_conv on public.messages(conversation_id);
create index if not exists idx_messages_search on public.messages using gin(to_tsvector('spanish', content));

-- Products
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
create index if not exists idx_products_user on public.products(user_id);
create index if not exists idx_products_status on public.products(status);

-- Persistent memory (key-value per user)
create table if not exists public.memory (
  id          text primary key,              -- "{user_id}:{key}"
  user_id     text not null references public.users(id) on delete cascade,
  key         text not null,
  value       text not null,
  updated_at  timestamptz not null default now()
);
create index if not exists idx_memory_user on public.memory(user_id);

-- ── RLS ─────────────────────────────────────────────────────
-- Backend uses service_role key which bypasses RLS.
-- These policies protect direct/anon access if ever needed.

alter table public.users        enable row level security;
alter table public.conversations enable row level security;
alter table public.messages      enable row level security;
alter table public.products      enable row level security;
alter table public.memory        enable row level security;

-- Allow service_role full access (backend key)
create policy "service_role full access" on public.users        for all using (true);
create policy "service_role full access" on public.conversations for all using (true);
create policy "service_role full access" on public.messages      for all using (true);
create policy "service_role full access" on public.products      for all using (true);
create policy "service_role full access" on public.memory        for all using (true);
