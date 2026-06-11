import httpx
import logging
from typing import Dict, Any, Optional
from src.core.config import settings

logger = logging.getLogger(__name__)

class ShopifyTool:
    """
    Unified Shopify Tool for real-world Admin API interactions.
    No simulations. No Zapier.
    """
    def __init__(self):
        self.shop_url = settings.SHOPIFY_URL
        self.token = settings.SHOPIFY_ADMIN_TOKEN
        
        # Format shop URL
        if self.shop_url and not self.shop_url.startswith("https://"):
            self.shop_url = f"https://{self.shop_url}"
        if self.shop_url and not self.shop_url.endswith("/admin/api/2024-04"):
            self.shop_url = f"{self.shop_url.rstrip('/')}/admin/api/2024-04"

    def is_configured(self) -> bool:
        return bool(self.shop_url and self.token)

    async def create_product(self, title: str, body_html: str, vendor: str, product_type: str, price: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured():
            return {"success": False, "error": "Shopify no configurado: SHOPIFY_URL o SHOPIFY_ADMIN_TOKEN ausentes."}

        headers = {
            "X-Shopify-Access-Token": self.token,
            "Content-Type": "application/json"
        }

        product_data = {
            "product": {
                "title": title,
                "body_html": body_html,
                "vendor": vendor,
                "product_type": product_type,
                "status": "active",
                "variants": [
                    {
                        "price": price,
                        "inventory_policy": "deny",
                        "fulfillment_service": "manual",
                        "inventory_management": None
                    }
                ]
            }
        }

        if image_url:
            product_data["product"]["images"] = [{"src": image_url}]

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.shop_url}/products.json",
                    json=product_data,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 201:
                    product = response.json().get("product", {})
                    shop_domain = self.shop_url.split("//")[1].split("/")[0]
                    return {
                        "success": True,
                        "product_id": product.get("id"),
                        "shop_url": f"https://{shop_domain}/products/{product.get('handle')}"
                    }
                else:
                    logger.error(f"Shopify error: {response.status_code} - {response.text}")
                    return {"success": False, "error": f"Error de Shopify: {response.status_code}", "details": response.json()}
            except Exception as e:
                logger.exception("Failed to create Shopify product")
                return {"success": False, "error": str(e)}

shopify_tool = ShopifyTool()
