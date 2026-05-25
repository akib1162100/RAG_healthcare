import odoo
from odoo import api, SUPERUSER_ID

def main():
    odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf'])
    registry = odoo.registry('odoo')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        url_param = env['ir.config_parameter'].sudo().get_param('rag_controller.rag_api_url', '')
        print("rag_controller.rag_api_url:", url_param)
        
        # Now try to test the rag api client
        try:
            client = env['rag.api.client']
            result = client.chat(prompt="Hello RAG", session_id="test_odoo_session_1")
            print("Chat API Client test response:", result)
        except Exception as e:
            print("Error connecting from Odoo to RAG API:", e)

if __name__ == '__main__':
    main()
