# Part of Odoo. See LICENSE file for full copyright and licensing details.

from . import models
from odoo import tools, api, SUPERUSER_ID
import csv

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    DiseaseModel = env['medical.disease']
    diseases_to_create = []
    with tools.file_open("icd_manager/data/icd10.csv") as file:
        reader = csv.DictReader(file)
        for row in reader:
            diseases_to_create.append({
                'code': row.get('code'),
                'name': row.get('name'),
                'long_name': row.get('long_name')})
    if diseases_to_create:
        DiseaseModel.create(diseases_to_create)
