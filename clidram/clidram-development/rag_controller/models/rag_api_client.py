import requests
import json
import logging
from odoo import models, api
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)

class RagApiClient(models.AbstractModel):
    _name = 'rag.api.client'
    _description = 'RAG API Client'

    @api.model
    def _get_api_config(self):
        rag_api_url = self.env['ir.config_parameter'].sudo().get_param('rag_controller.rag_api_url', '')
        rag_api_key = self.env['ir.config_parameter'].sudo().get_param('rag_controller.rag_api_key', '')
        
        if not rag_api_url:
            raise UserError('RAG API URL is not configured. Please configure it in the general settings.')
            
        return rag_api_url.rstrip('/'), rag_api_key

    @api.model
    def _make_request(self, endpoint, payload=None, method='POST'):
        url, api_key = self._get_api_config()
        full_url = f"{url}{endpoint}"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if api_key:
            headers['Authorization'] = f"Bearer {api_key}"
            
        try:
            if method == 'POST':
                response = requests.post(full_url, json=payload, headers=headers, timeout=30)
            elif method == 'GET':
                response = requests.get(full_url, params=payload, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(full_url, json=payload, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"RAG API Request failed: {e}")
            raise UserError(f"Failed to communicate with the RAG system: {str(e)}")

    @api.model
    def query_patient(self, patient_seq, prompt, limit=5):
        """Query patient history"""
        payload = {
            "patient_seq": patient_seq,
            "prompt": prompt,
            "limit": limit
        }
        return self._make_request('/api/v1/rag/query-patient', payload=payload)

    @api.model
    def query_prescriptions(self, prompt, diagnosis_code=None, date_from=None, date_to=None, limit=10):
        """Search prescriptions"""
        payload = {
            "prompt": prompt,
            "limit": limit
        }
        if diagnosis_code:
            payload["diagnosis_code"] = diagnosis_code
        if date_from:
            payload["date_from"] = date_from
        if date_to:
            payload["date_to"] = date_to
            
        return self._make_request('/api/v1/rag/query-prescriptions', payload=payload)
        
    @api.model
    def trigger_indexing(self, models_list=None, incremental=False, limit=None):
        """Trigger ETL indexing"""
        if models_list is None:
            models_list = ["wk.appointment", "prescription.order.knk", "res.partner", "medical.disease"]
            
        payload = {
            "models": models_list,
            "incremental": incremental
        }
        if limit:
            payload["limit"] = limit
            
        return self._make_request('/api/v1/etl/index-medical', payload=payload)
        
    @api.model
    def get_index_status(self):
        """Get ETL index status"""
        return self._make_request('/api/v1/etl/index-status', method='GET')
    @api.model
    def chat(self, prompt, session_id, patient_seq=None, reset=False):
        """Conversational chat endpoint"""
        payload = {
            "prompt": prompt,
            "session_id": session_id,
            "reset": reset
        }
        if patient_seq:
            payload["patient_seq"] = patient_seq
            
        return self._make_request('/api/v1/rag/chat', payload=payload)
