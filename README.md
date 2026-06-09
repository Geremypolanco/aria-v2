# Aria V2 — Agente Cognitivo Autónomo

Agente autónomo de generación de ingresos con productos digitales. Construido con FastAPI, Claude API (tool_use + streaming), Supabase y desplegado en Vercel.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | FastAPI (serverless en Vercel) |
| AI | Anthropic Claude claude-opus-4-5 con tool_use |
| Base de datos | Supabase (Postgres) |
| Auth | Google OAuth2 + JWT |
| Frontend | HTML/CSS/JS vanilla con SSE streaming |

## Setup

### 1. Clonar y configurar entorno

```bash
git clone <repo>
cd aria-v2
cp .env.example .env
# Edita .env con tus credenciales
```

### 2. Base de datos

En Supabase Dashboard → SQL Editor → New query, pega y ejecuta el contenido de `schema.sql`.

### 3. Google OAuth

1. Ir a [console.cloud.google.com](https://console.cloud.google.com)
2. Crear proyecto → APIs & Services → Credentials → OAuth 2.0 Client ID
3. Authorized redirect URIs: `https://tu-dominio.vercel.app/auth/callback`
4. Copiar Client ID y Secret a `.env`

### 4. Deploy en Vercel

```bash
npm i -g vercel
vercel
```

Agregar variables de entorno en Vercel Dashboard → Settings → Environment Variables (todas las del `.env`).

### 5. Local

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
```

## Arquitectura

```
aria-v2/
├── api/
│   └── main.py          # FastAPI app + rutas
├── src/
│   ├── core/
│   │   ├── config.py    # Settings (pydantic)
│   │   └── agent.py     # Agentic loop con streaming
│   ├── tools/
│   │   └── registry.py  # Tool schemas + ejecutores
│   ├── auth/
│   │   ├── router.py    # Google OAuth + callback
│   │   ├── jwt.py       # Create/decode JWT
│   │   └── dependencies.py
│   └── db/
│       ├── client.py    # Supabase singleton
│       └── repositories.py
├── static/
│   └── index.html       # Frontend completo
├── schema.sql           # Esquema Supabase
├── vercel.json
└── requirements.txt
```

## Capacidades del agente

Aria ejecuta un loop autónomo de razonamiento:

1. **detect_opportunity** — analiza contexto y detecta nichos rentables
2. **generate_content** — genera cursos, ebooks y bundles completos con Claude
3. **manage_products** — lista, actualiza y publica el catálogo
4. **get_analytics** — métricas de productos y revenue potencial
5. **search_memory** — busca en historial de conversaciones
6. **save_memory** — persiste contexto del usuario entre sesiones
