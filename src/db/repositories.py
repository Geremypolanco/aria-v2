from __future__ import annotations
import uuid
from datetime import datetime
from src.db.supabase import get_supabase


class ConversationRepository:

    @staticmethod
    async def create(user_id: str) -> str:
        db = get_supabase()
        conv_id = str(uuid.uuid4())
        db.table("conversations").insert({
            "id": conv_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
        return conv_id

    @staticmethod
    async def list(user_id: str) -> list[dict]:
        db = get_supabase()
        res = (
            db.table("conversations")
            .select("id, created_at, messages(content, role, created_at)")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        return res.data or []

    @staticmethod
    async def get_messages(conv_id: str, user_id: str) -> list[dict]:
        db = get_supabase()
        # Verify ownership
        conv = (
            db.table("conversations")
            .select("id")
            .eq("id", conv_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        if not conv.data:
            return []

        res = (
            db.table("messages")
            .select("role, content")
            .eq("conversation_id", conv_id)
            .order("created_at")
            .execute()
        )
        return [{"role": r["role"], "content": r["content"]} for r in (res.data or [])]

    @staticmethod
    async def add_message(conv_id: str, role: str, content: str) -> None:
        db = get_supabase()
        db.table("messages").insert({
            "id": str(uuid.uuid4()),
            "conversation_id": conv_id,
            "role": role,
            "content": content,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()

    @staticmethod
    async def search(query: str, user_id: str, limit: int = 5) -> list[dict]:
        """Búsqueda full-text en mensajes del usuario."""
        db = get_supabase()
        res = (
            db.table("messages")
            .select("role, content, created_at, conversations!inner(user_id)")
            .eq("conversations.user_id", user_id)
            .ilike("content", f"%{query}%")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []


class ProductRepository:

    @staticmethod
    async def create(data: dict, user_id: str) -> dict:
        db = get_supabase()
        record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": data.get("status", "draft"),
            "type": data.get("type"),
            "topic": data.get("topic"),
            "title": data.get("title", data.get("topic", "Sin título")),
            "description": data.get("description", ""),
            "price": data.get("price", 0),
            "content_json": data,
        }
        res = db.table("products").insert(record).execute()
        return res.data[0] if res.data else record

    @staticmethod
    async def handle(inputs: dict, user_id: str) -> dict:
        db = get_supabase()
        action = inputs["action"]

        if action == "list":
            res = (
                db.table("products")
                .select("id, title, type, price, status, created_at")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            return {"products": res.data or []}

        if action == "create":
            return await ProductRepository.create(inputs.get("data", {}), user_id)

        if action == "update":
            product_id = inputs.get("product_id")
            if not product_id:
                return {"error": "product_id requerido"}
            res = (
                db.table("products")
                .update(inputs.get("data", {}))
                .eq("id", product_id)
                .eq("user_id", user_id)
                .execute()
            )
            return {"updated": res.data[0] if res.data else None}

        if action == "delete":
            product_id = inputs.get("product_id")
            db.table("products").delete().eq("id", product_id).eq("user_id", user_id).execute()
            return {"deleted": product_id}

        return {"error": f"Acción desconocida: {action}"}

    @staticmethod
    async def handle_monetization(inputs: dict, user_id: str) -> dict:
        db = get_supabase()
        m_type = inputs["type"]
        action = inputs["action"]
        data = inputs.get("data", {})

        table_map = {
            "article": "content_articles",
            "affiliate_link": "affiliate_links",
            "subscriber": "email_subscribers"
        }
        table = table_map.get(m_type)
        if not table:
            return {"error": f"Tipo de monetización desconocido: {m_type}"}

        if action == "create":
            data["user_id"] = user_id
            res = db.table(table).insert(data).execute()
            return {"success": True, "data": res.data[0] if res.data else data}

        if action == "list":
            res = db.table(table).select("*").eq("user_id", user_id).execute()
            return {f"{m_type}s": res.data or []}

        if action == "delete":
            item_id = data.get("id")
            if not item_id:
                return {"error": "id requerido para eliminar"}
            db.table(table).delete().eq("id", item_id).eq("user_id", user_id).execute()
            return {"deleted": item_id}

        return {"error": f"Acción desconocida: {action}"}

    @staticmethod
    async def analytics(period: str, user_id: str) -> dict:
        db = get_supabase()

        from datetime import timedelta
        period_delta = {
            "today": timedelta(days=1),
            "week":  timedelta(days=7),
            "month": timedelta(days=30),
            "all":   timedelta(days=3650),
        }.get(period, timedelta(days=7))

        since = (datetime.utcnow() - period_delta).isoformat()

        products = (
            db.table("products")
            .select("id, title, type, price, status, created_at")
            .eq("user_id", user_id)
            .gte("created_at", since)
            .execute()
        )

        data = products.data or []
        total_revenue = sum(p["price"] for p in data if p["status"] == "published")
        by_type: dict = {}
        for p in data:
            by_type[p["type"]] = by_type.get(p["type"], 0) + 1

        return {
            "period": period,
            "total_products": len(data),
            "total_revenue_potential": total_revenue,
            "by_type": by_type,
            "products": data,
        }


class UserRepository:

    @staticmethod
    async def upsert(google_sub: str, email: str, name: str, picture: str = "") -> dict:
        db = get_supabase()
        res = (
            db.table("users")
            .upsert(
                {
                    "id": google_sub,
                    "email": email,
                    "name": name,
                    "picture": picture,
                    "updated_at": datetime.utcnow().isoformat(),
                },
                on_conflict="id",
            )
            .execute()
        )
        return res.data[0] if res.data else {}

    @staticmethod
    async def get(user_id: str) -> dict | None:
        db = get_supabase()
        res = (
            db.table("users")
            .select("*")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        return res.data
