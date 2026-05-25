import re

file_path = r'p:\RAG_healthcare\RAG_git\RAG_healthcare\app\api\v1\endpoints\rag.py'
with open(file_path, 'r', encoding='utf-8') as f:
    code = f.read()

if 'from fastapi import Header' not in code:
    code = code.replace('from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks', 
                        'from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header')

# Inject headers safely right before session: AsyncSession
header_params = """    x_odoo_instance_id: str = Header("default", alias="X-Odoo-Instance-ID"),
    x_odoo_company_id: int = Header(1, alias="X-Odoo-Company-ID"),
    session: AsyncSession"""
code = code.replace("    session: AsyncSession", header_params)

# Replace request.instance_id with x_odoo_instance_id
code = re.sub(r'request\.instance_id or "default"', r'x_odoo_instance_id', code)
code = re.sub(r'request\.instance_id', r'x_odoo_instance_id', code)

# Inject company_id
code = re.sub(r'instance_id=x_odoo_instance_id,?', r'instance_id=x_odoo_instance_id, company_id=x_odoo_company_id,', code)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Modified rag.py successfully")
