import xmlrpc.client

def odoo_message_post_test():
    url = 'http://localhost:8069'
    db = 'cli'
    username = 'admin'
    password = 'admin'
    
    try:
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, username, password, {})
        
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        
        # Find the active Discuss channel id = 119
        channel_id = 119
        
        # Send a message
        print("Authenticating successful... UID:", uid)
        print("Sending message to channel 119 to trigger the RAG bot via native Odoo API")
        
        msg = models.execute_kw(db, uid, password,
            'mail.channel', 'message_post',
            [channel_id],
            {'body': "@rag_bot patient_id: 20250600042005 What are their complaints (api trigger test)?", 'message_type': 'comment'}
        )
        print("Message posting returned ID:", msg)
        
    except Exception as e:
        print("Odoo connection failed:", e)

if __name__ == "__main__":
    odoo_message_post_test()
