from __future__ import annotations
import uuid
from datetime import datetime
from src.db.client import get_supabase


class UserRepository:
    @staticmethod
    def upsert(google_sub: str, email: str, name: str, picture: str = "") -> dict:
        db = get_supabase()
        res = db.table("users").upsert(
            {
                "id": google_sub,
                "email": email,
                "name": name,
                "picture": picture,
                "updated_at": datetime.utcnow().isoformat(),
            },
            on_conflict="id",
        ).execute()
        return res.data[0] if res.data else {}

    @staticmethod
    def get(user_id: str) -> dict | None:
        db = get_supabase()
        res = db.table("users").select("*").eq("id", user_id).maybe_single().execute()
        return res.data


class ConversationRepository:
    @staticmethod
    def create(user_id: str) -> str:
        db = get_supabase()
        conv_id = str(uuid.uuid4())
        db.table("conversations").insert(
            {"id": conv_id, "user_id": user_id, "created_at": datetime.utcnow().isoformat()}
        ).execute()
        return conv_id

    @staticmethod
    def list(user_id: str) -> list[dict]:
        db = get_supabase()
        res = (
            db.table("conversations")
            .select("id, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(30)
            .execute()
        )
        return res.data or []

    @staticmethod
    def get_messages(conv_id: str, user_id: str) -> list[dict]:
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
            .limit(40)
            .execute()
        )
        return [{"role": r["role"], "content": r["content"]} for r in (res.data or [])]

    @staticmethod
    def add_message(conv_id: str, role: str, content: str) -> None:
        db = get_supabase()
        db.table("messages").insert(
            {
                "id": str(uuid.uuid4()),
                "conversation_id": conv_id,
                "role": role,
                "content": content,
                "created_at": datetime.utcnow().isoformat(),
            }
        ).execute()

    @staticmethod
    def search(query: str, user_id: str, limit: int = 5) -> list[dict]:
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
    def create(data: dict, user_id: str) -> dict:
        db = get_supabase()
        record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": data.get("status", "draft"),
            "type": data.get("type", "course"),
            "title": data.get("title", data.get("topic", "Sin título")),
            "topic": data.get("topic", ""),
            "description": data.get("description", ""),
            "price": float(data.get("price", 0)),
            "content_json": data,
        }
        res = db.table("products").insert(record).execute()
        return res.data[0] if res.data else record

    @staticmethod
    def handle(inputs: dict, user_id: str) -> dict:
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
            return ProductRepository.create(inputs.get("data", {}), user_id)

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
    def analytics(period: str, user_id: str) -> dict:
        db = get_supabase()
        interval = {
            "today": "1 day",
            "week": "7 days",
            "month": "30 days",
            "all": "3650 days",
        }.get(period, "7 days")

        res = (
            db.table("products")
            .select("id, title, type, price, status, created_at")
            .eq("user_id", user_id)
            .gte("created_at", f"(now() - interval '{interval}')")
            .execute()
        )
        data = res.data or []
        published = [p for p in data if p["status"] == "published"]
        by_type: dict[str, int] = {}
        for p in data:
            by_type[p["type"]] = by_type.get(p["type"], 0) + 1

        return {
            "period": period,
            "total_products": len(data),
            "published": len(published),
            "revenue_potential": sum(p["price"] for p in published),
            "by_type": by_type,
            "products": data,
        }

    @staticmethod
    def handle_monetization(inputs: dict, user_id: str) -> dict:
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


class MemoryRepository:
    """Persistent memory entries: facts Aria learns about the user."""

    @staticmethod
    def add(user_id: str, key: str, value: str) -> None:
        db = get_supabase()
        db.table("memory").upsert(
            {
                "id": f"{user_id}:{key}",
                "user_id": user_id,
                "key": key,
                "value": value,
                "updated_at": datetime.utcnow().isoformat(),
            },
            on_conflict="id",
        ).execute()

    @staticmethod
    def get_all(user_id: str) -> list[dict]:
        db = get_supabase()
        res = (
            db.table("memory")
            .select("key, value, updated_at")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .execute()
        )
        return res.data or []

    @staticmethod
    def format_for_context(user_id: str) -> str:
        entries = MemoryRepository.get_all(user_id)
        if not entries:
            return ""
        lines = [f"- {e['key']}: {e['value']}" for e in entries]
        return "Conocimiento persistente sobre el usuario:\n" + "\n".join(lines)
