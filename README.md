# Aria V2 — Agente Autónomo de Productos Digitales

Aria V2 es un agente de IA autónomo construido con **Claude API**, **FastAPI**, **Supabase** y **Google OAuth2**. Genera cursos, ebooks y bundles de productos digitales, gestiona un catálogo con persistencia real y responde en streaming via SSE.

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI + Python 3.11 |
| IA | Anthropic Claude (claude-opus-4-5) con tool_use |
| Base de datos | Supabase (PostgreSQL) |
| Auth | Google OAuth2 + JWT |
| Frontend | HTML + TailwindCSS + SSE streaming |
| Deploy | Vercel (serverless Python) |

## Arquitectura

```
api/main.py          ← Entry point FastAPI + SSE streaming
src/core/agent.py    ← Loop agente Claude con tool_use
src/core/tools.py    ← Definición y ejecución de tools
src/core/config.py   ← Settings con pydantic-settings
src/auth/router.py   ← Google OAuth2 → JWT
src/auth/jwt.py      ← create/decode JWT
src/auth/dependencies.py ← get_current_user FastAPI dep
src/db/supabase.py   ← Cliente Supabase singleton
src/db/repositories.py ← ConversationRepo, ProductRepo, UserRepo
static/index.html    ← Frontend con SSE real (sin alert())
supabase_schema.sql  ← Schema SQL completo para Supabase
```

## Variables de entorno

Copia `.env.example` a `.env` y completa:

```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
JWT_SECRET=...          # openssl rand -hex 32
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...  # service_role key
```

En Vercel, configura estas variables en **Settings > Environment Variables**.

## Setup Supabase

1. Crea un proyecto en [supabase.com](https://supabase.com)
2. Ve a **SQL Editor** y ejecuta el contenido de `supabase_schema.sql`
3. Copia la **service_role key** (Settings > API) como `SUPABASE_SERVICE_KEY`

## Desarrollo local

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
```

## Deploy

El proyecto se despliega automáticamente en Vercel al hacer push a `main`.
