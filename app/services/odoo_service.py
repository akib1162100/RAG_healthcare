"""
OdooService — pushes AI-generated HTML back to Odoo via JSON-RPC API.

All Odoo communication uses the Bearer-authenticated JSON-RPC API.
No XML-RPC is used.
"""
import logging
import aiohttp
from app.core.config import settings

logger = logging.getLogger(__name__)


class OdooService:
    """Service to push results back to Odoo via JSON-RPC API with Bearer auth."""

    def __init__(self):
        self.instances = {
            cfg["instance_id"]: cfg for cfg in settings.get_odoo_instances()
        }
        default_cfg = settings.get_default_odoo_instance()
        self.url = default_cfg["url"]
        self.api_key = default_cfg["api_key"]
        self.db = default_cfg["db"]
        self.default_instance_id = default_cfg["instance_id"]

    def _get_instance_config(self, instance_id: str = None) -> dict:
        if instance_id and instance_id in self.instances:
            return self.instances[instance_id]
        return self.instances.get(self.default_instance_id, {
            "instance_id": self.default_instance_id,
            "url": self.url,
            "api_key": self.api_key,
            "db": self.db,
        })

    def _headers(self, api_key: str) -> dict:
        """Standard headers for Odoo JSON-RPC API calls."""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def _call_api(self, endpoint: str, params: dict, instance_id: str = None) -> dict:
        """
        Make a JSON-RPC API call to Odoo.

        Args:
            endpoint: API path (e.g., '/api/rag/patient/update_html')
            params: JSON-RPC params dict

        Returns:
            Parsed JSON response dict
        """
        cfg = self._get_instance_config(instance_id)
        url = f"{cfg['url']}{endpoint}"
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": params,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload, headers=self._headers(cfg["api_key"]),
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                if "error" in data:
                    error_msg = data["error"].get("message", str(data["error"]))
                    raise RuntimeError(f"Odoo API error: {error_msg}")
                return data.get("result", {})

    async def update_patient_medical_html(
        self, patient_id: int,
        summary_html: str = None,
        details_html: str = None,
        instance_id: str = None,
    ) -> bool:
        """
        Push AI-generated HTML back to res.partner record via JSON-RPC API.
        This allows the RAG server to 'report back' once background processing is finished.
        """
        vals = {}
        if summary_html:
            vals['medical_summary_html'] = summary_html
        if details_html:
            vals['medical_details_html'] = details_html

        if not vals:
            return True

        try:
            await self._call_api(
                "/api/rag/patient/update_html",
                {"partner_id": patient_id, **vals},
                instance_id=instance_id,
            )
            logger.info(f"Successfully pushed background AI update back to Odoo Partner ID {patient_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to push update back to Odoo Partner {patient_id}: {e}")
            return False
