import re
import os

file_path = r'p:\RAG_healthcare\RAG_git\RAG_healthcare\app\api\v1\endpoints\rag.py'
with open(file_path, 'r', encoding='utf-8') as f:
    code = f.read()

if 'from fastapi import Header' not in code:
    code = code.replace('from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks', 
                        'from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header')

# We want to add these parameters to every endpoint
header_params = """    x_odoo_instance_id: str = Header("default", alias="X-Odoo-Instance-ID"),
    x_odoo_company_id: int = Header(1, alias="X-Odoo-Company-ID"),
"""

# Regex to find endpoint definitions
# Matches @router... async def func_name(
def replace_endpoint(match):
    prefix = match.group(0)
    if 'x_odoo_instance_id' in prefix:
        return prefix # Already modified
    # Inject right after the function def
    return prefix + "\n" + header_params

code = re.sub(r'(@router\.[a-z]+\(.*?\)\nasync def [a-zA-Z0-9_]+\()', replace_endpoint, code, flags=re.DOTALL)

# Now, we need to replace usages of request.instance_id with x_odoo_instance_id
code = re.sub(r'request\.instance_id or "default"', r'x_odoo_instance_id', code)
code = re.sub(r'request\.instance_id', r'x_odoo_instance_id', code)

# And inject company_id=x_odoo_company_id where instance_id=x_odoo_instance_id is passed
# Example: instance_id=x_odoo_instance_id,
code = re.sub(r'instance_id=x_odoo_instance_id,?', r'instance_id=x_odoo_instance_id, company_id=x_odoo_company_id,', code)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Modified rag.py")
