"""
Data Extractor for Odoo Medical Models
Extracts data from Odoo PostgreSQL database with proper joins
"""
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
import logging

from .odoo_schema import ODOO_MODEL_MAPPING

logger = logging.getLogger(__name__)


class OdooDataExtractor:
    """Extract data from Odoo medical models"""
    
    def __init__(self, odoo_engine: AsyncEngine, vector_engine: AsyncEngine):
        self.engine = odoo_engine  # This will be unused for extraction now
        self.vector_engine = vector_engine
        self._odoo_config = None

    async def _get_odoo_config(self) -> Dict:
        """Fetch Odoo URL and API Key from env or config file"""
        if self._odoo_config:
            return self._odoo_config
            
        odoo_url = os.getenv('ODOO_URL', 'http://host.docker.internal:8069')
        api_key = os.getenv('ODOO_API_KEY', 'default_secret')
        
        import json
        config_path = "/app/odoo_config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config_data = json.load(f)
                    if config_data.get("odooUrl"):
                        odoo_url = config_data["odooUrl"]
                    if config_data.get("apiKey"):
                        api_key = config_data["apiKey"]
            except Exception as e:
                logger.error(f"Failed to read odoo config file: {e}")
                
        self._odoo_config = {"url": odoo_url, "api_key": api_key}
        return self._odoo_config

    async def _call_odoo_api(self, endpoint_suffix: str, params: Dict) -> Dict:
        """Invoke Odoo JSON-RPC API"""
        config = await self._get_odoo_config()
        import aiohttp
        
        headers = {"Authorization": f"Bearer {config['api_key']}"}
        url = f"{config['url']}{endpoint_suffix}"
        
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": params
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, json=payload, timeout=30) as response:
                if response.status != 200:
                    logger.error(f"Odoo API HTTP error {response.status} for {endpoint_suffix}")
                    return {"status": "error", "message": f"HTTP {response.status}"}
                
                resp_data = await response.json()
                if "result" in resp_data:
                    return resp_data["result"]
                elif "error" in resp_data:
                    logger.error(f"Odoo API Error for {endpoint_suffix}: {resp_data['error']}")
                    return {"status": "error", "message": resp_data["error"]}
                return {"status": "error", "message": "Unknown malformed response"}

    async def _get_ids(self, model: str, incremental: bool = True, limit: Optional[int] = None) -> List[int]:
        """Fetch record IDs via API list_ids"""
        domain = []
        if incremental and model in ['wk.appointment', 'prescription.order.knk']:
            domain.append(('is_rag_synced', '!=', True))
        
        if model == 'wk.appointment':
            domain.append(('appoint_state', '!=', 'rejected'))
        elif model == 'prescription.order.knk':
            domain.append(('state', '!=', 'cancelled'))
        elif model == 'res.partner':
            domain.append(('partner_type', '=', 'patient'))
            
        params = {
            "model": model,
            "domain": domain,
            "limit": limit,
            "offset": 0
        }
        
        res = await self._call_odoo_api("/api/rag/list_ids", params)
        if res.get("status") == "success":
            return res.get("data", [])
        return []

    async def extract_appointments(
        self, 
        limit: Optional[int] = None,
        since_date: Optional[datetime] = None,
        incremental: bool = True
    ) -> List[Dict]:
        """Extract appointment data via Bulk API"""
        domain = []
        if incremental:
            domain.append(('is_rag_synced', '!=', True))
        domain.append(('appoint_state', '!=', 'rejected'))
        
        params = {"domain": domain, "limit": limit}
        res = await self._call_odoo_api("/api/rag/appointments/fetch_all", params)
        
        appointments = res.get("data", []) if res.get("status") == "success" else []
        logger.info(f"Extracted {len(appointments)} appointments")
        return appointments

    async def extract_prescriptions(
        self,
        limit: Optional[int] = None,
        since_date: Optional[datetime] = None,
        incremental: bool = True
    ) -> List[Dict]:
        """Extract prescription data via Bulk API"""
        domain = []
        if incremental:
            domain.append(('is_rag_synced', '!=', True))
        domain.append(('state', '!=', 'cancelled'))
        
        params = {"domain": domain, "limit": limit}
        res = await self._call_odoo_api("/api/rag/prescriptions/fetch_all", params)
        
        prescriptions = res.get("data", []) if res.get("status") == "success" else []
        logger.info(f"Extracted {len(prescriptions)} prescriptions")
        return prescriptions

    async def extract_patients(
        self,
        limit: Optional[int] = None,
        since_date: Optional[datetime] = None,
        incremental: bool = True
    ) -> List[Dict]:
        """Extract patient data via Bulk API"""
        domain = [('partner_type', '=', 'patient')]
        if incremental:
            domain.append(('is_rag_synced', '!=', True))
            
        params = {"domain": domain, "limit": limit}
        res = await self._call_odoo_api("/api/rag/patients/fetch_all", params)
        
        patients = res.get("data", []) if res.get("status") == "success" else []
        logger.info(f"Extracted {len(patients)} patients")
        return patients

    async def extract_diseases(
        self,
        limit: Optional[int] = None,
        incremental: bool = False
    ) -> List[Dict]:
        """Extract disease data via Bulk API"""
        domain = []
        params = {"domain": domain, "limit": limit}
        res = await self._call_odoo_api("/api/rag/diseases/fetch_all", params)
        
        diseases = res.get("data", []) if res.get("status") == "success" else []
        logger.info(f"Extracted {len(diseases)} diseases")
        return diseases
    
    # The following helper methods are now handled by the Odoo Controller API
    # and are kept here as empty stubs or removed to avoid direct SQL usage.

    
    async def get_last_indexed_date(self, model_name: str) -> Optional[datetime]:
        """Get the last indexed date for a model from etl_metadata"""
        query = """
        SELECT last_write_date 
        FROM etl_metadata 
        WHERE odoo_model = :model_name
        """
        async with self.vector_engine.connect() as conn:
            result = await conn.execute(text(query), {'model_name': model_name})
            row = result.fetchone()
            return row[0] if row and row[0] else None
    
    async def update_etl_metadata(
        self, 
        model_name: str, 
        last_write_date: datetime,
        total_records: int,
        total_chunks: int
    ):
        """Update ETL metadata after indexing"""
        # Defensive check: Ensure last_write_date is a datetime object
        if isinstance(last_write_date, str):
            try:
                last_write_date = datetime.fromisoformat(last_write_date.replace('Z', '+00:00'))
            except Exception:
                last_write_date = datetime.now()

        query = """
        INSERT INTO etl_metadata (odoo_model, last_indexed_at, last_write_date, total_records, total_chunks)
        VALUES (:model_name, :indexed_at, :last_write_date, :total_records, :total_chunks)
        ON CONFLICT (odoo_model) 
        DO UPDATE SET 
            last_indexed_at = :indexed_at,
            last_write_date = :last_write_date,
            total_records = :total_records,
            total_chunks = :total_chunks
        """
        async with self.vector_engine.begin() as conn:
            await conn.execute(text(query), {
                'model_name': model_name,
                'indexed_at': datetime.now(),
                'last_write_date': last_write_date,
                'total_records': total_records,
                'total_chunks': total_chunks
            })

    async def get_existing_odoo_ids(self, odoo_model: str) -> set:
        """Fetch all unique odoo_res_id values currently in the vector DB for a given model"""
        query = "SELECT DISTINCT odoo_res_id FROM medical_rag_index WHERE odoo_model = :model_name"
        existing_ids = set()
        async with self.vector_engine.connect() as conn:
            result = await conn.execute(text(query), {'model_name': odoo_model})
            for row in result.fetchall():
                if row[0] is not None:
                    existing_ids.add(int(row[0]))
        return existing_ids

    async def mark_records_as_synced(self, odoo_model: str, record_ids: List[int]) -> int:
        """Mark records as synced in Odoo via API"""
        if not record_ids:
            return 0
            
        res = await self._call_odoo_api("/api/rag/mark_synced", {"model": odoo_model, "res_ids": record_ids})
        if res.get("status") == "success":
            count = res.get("count", len(record_ids))
            logger.info(f"Marked {count} records as synced for {odoo_model}")
            return count
        else:
            logger.error(f"Failed to mark records as synced for {odoo_model}: {res.get('message')}")
            return 0
