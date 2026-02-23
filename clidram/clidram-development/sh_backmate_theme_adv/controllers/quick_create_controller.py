from odoo.http import request
from odoo import http
from datetime import datetime, date

#----------------------------------------------------------
# Odoo Web web Controllers
#----------------------------------------------------------
class QuickCreate(http.Controller):

    @http.route(['/create/quick/action'], type='json', auth='user', methods=['POST'])
    def create_quick_action_records(self,data):
        action_vals={
            'name': data.get('name'),
            'icon': data.get('icon'),
            'sequence': data.get('sequence'),
            'model_id': data.get('model_id'),
            'sh_user_id': request.env.user.id,
        }
        new_record=request.env['sh.quick.create'].sudo().create(action_vals)
        return True


        # return mentioned_dict
    
    @http.route(['/get/quick/action/data'], type='json', auth='user', methods=['POST'])
    def get_quick_action_data(self):
        final_data_list=[]
        total_data=request.env['sh.quick.create'].sudo().search([('sh_user_id','=',request.env.user.id)],order='sequence asc')
        for action in total_data:
            data_dict={
                'id':action.id,
                'name':action.name,
                'model_id':action.model_id.id,
                'icon':action.icon,
                'sequence':action.sequence,
                'model_name':action.model_name,
            }
            final_data_list.append(data_dict)

        allow_model_dict={}
        models=request.env['ir.model'].sudo().search([])

        for model in models:
            allow_model_dict[model.id]=model.display_name

        if not final_data_list:
            final_data_list= False
        return final_data_list,allow_model_dict

    
    @http.route(['/get/edit/quick/action/data'], type='json', auth='user', methods=['POST'])
    def get_edit_quick_action_data(self,action_id):
        data=request.env['sh.quick.create'].sudo().browse(action_id)

        final_data_list=[]
        data_dict={
            'id':data.id,
            'name':data.name,
            'model_id':data.model_id.id,
            'icon':data.icon,
            'sequence':data.sequence,
            'model_name':data.model_name,
        }
        final_data_list.append(data_dict)
        return final_data_list

    
    @http.route(['/unlink/quick/action/data'], type='json', auth='user', methods=['POST'])
    def unlink_quick_action_data(self,action_id):
        data=request.env['sh.quick.create'].sudo().browse(action_id)
        data.sudo().unlink()
       
        return True
    
    @http.route(['/update/quick/action'], type='json', auth='user', methods=['POST'])
    def update_quick_action_data(self,data,action_id):
        current_record=request.env['sh.quick.create'].sudo().browse(action_id)
        action_vals={
            'name': data.get('name'),
            'icon': data.get('icon'),
            'sequence': data.get('sequence'),
            'model_id': data.get('model_id'),
            'sh_user_id': request.env.user.id,
        }
        current_record.sudo().write(action_vals)
        return True

