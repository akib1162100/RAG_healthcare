from odoo import http
from odoo.http import request
import logging

logger = logging.getLogger(__name__)

class RagIntegrationController(http.Controller):

    @http.route('/api/rag/query_patient', type='json', auth='user', methods=['POST'])
    def api_query_patient(self, patient_seq, prompt, limit=5, **kwargs):
        """
        JSON-RPC endpoint wrapper for querying patient data from JS frontend.
        """
        try:
            rag_client = request.env['rag.api.client']
            result = rag_client.query_patient(patient_seq=patient_seq, prompt=prompt, limit=limit)
            return {'status': 'success', 'data': result}
        except Exception as e:
            logger.error(f"Error querying RAG system: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/rag/query_prescriptions', type='json', auth='user', methods=['POST'])
    def api_query_prescriptions(self, prompt, diagnosis_code=None, date_from=None, date_to=None, limit=10, **kwargs):
        """
        JSON-RPC endpoint wrapper for querying prescriptions from JS frontend.
        """
        try:
            rag_client = request.env['rag.api.client']
            result = rag_client.query_prescriptions(
                prompt=prompt, 
                diagnosis_code=diagnosis_code, 
                date_from=date_from, 
                date_to=date_to, 
                limit=limit
            )
            return {'status': 'success', 'data': result}
        except Exception as e:
            logger.error(f"Error querying prescriptions: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/rag/get_prescription', type='json', auth='user', methods=['POST'])
    def api_get_prescription(self, prescription_id, **kwargs):
        """
        JSON-RPC endpoint to fetch full nested prescription data by ID.
        """
        try:
            prescription = request.env['prescription.order.knk'].sudo().browse(int(prescription_id))
            if not prescription.exists():
                return {'status': 'error', 'message': 'Prescription not found'}
                
            result = {
                'id': prescription.id,
                'name': prescription.name,
                'patient': prescription.patient_id.name if prescription.patient_id else '',
                'physician': prescription.physician_id.name if prescription.physician_id else '',
                'date': prescription.date.isoformat() if prescription.date else '',
                'state': prescription.state,
                'disease': prescription.disease,
                'description': prescription.description,
                'vitals': {
                    'weight': prescription.v_weight,
                    'height': prescription.v_height,
                    'bmi': prescription.v_bmi,
                    'blood_pressure': f"{prescription.blood_presure}/{prescription.blood_presure_2}" if prescription.blood_presure else "",
                    'pulse': prescription.v_pulse,
                    'respiratory_rate': prescription.v_respiratory_rate,
                    'temperature': prescription.temperature,
                    'spo2': prescription.spo2,
                    'rbs': prescription.rbs,
                },
                'clinical_scores': {
                    'pain_score': prescription.pain_score,
                    'dyspnea': prescription.dyspnea,
                    'cardiac_rythm': prescription.cardiac_rythm,
                    'nihss': prescription.nihss,
                    'motor_power': prescription.motor_power,
                    'pupil_reaction': prescription.pupil_reaction,
                    'pupil_reaction_right': prescription.pupil_reaction_right,
                    'glassgow_coma_scale': prescription.glassgow_coma_scale,
                },
                'status_updates': {
                    'symptom_status': prescription.symptom_status,
                    'medication_adherence': prescription.medication_adherence,
                    'performance_status_update': prescription.performance_status_update,
                    'counseling_behavioral_response': prescription.counseling_behavioral_response,
                    'side_effects': prescription.side_effects,
                },
                'medications': [{'name': m.product_id.name, 'quantity': m.quantity, 'days': m.days, 'instruction': m.short_comment} for m in prescription.order_line_new_ids],
                'diagnoses': [{'name': d.disease_id.name if d.disease_id else ''} for d in prescription.diagnosis_ids],
                'complaints': [{'name': c.complaint_list_id.name if c.complaint_list_id else '', 'period': c.period.name if c.period else '', 'location': c.location_id.name if c.location_id else ''} for c in prescription.complaint_id],
                'signs': [{'name': s.sign_list_id.name if hasattr(s, 'sign_list_id') and s.sign_list_id else s.name, 'location': s.location.name if hasattr(s, 'location') and s.location else ''} for s in prescription.sign_ids],
                'investigations': [{'name': i.investigation_list_id.name if hasattr(i, 'investigation_list_id') and i.investigation_list_id else ''} for i in prescription.investigation_ids],
                'investigation_result': prescription.investigation_result,
                'procedures': [{'name': p.procedure_config_id.name if hasattr(p, 'procedure_config_id') and p.procedure_config_id else ''} for p in prescription.procedure_line_ids],
                'procedure_result': prescription.procedure_result,
                'physical_examinations': {
                    'general': prescription.general,
                    'heent': prescription.heent,
                    'cvs': prescription.cvs,
                    'respiratory': prescription.respiratory,
                    'abdomen': prescription.abdomen,
                    'msk': prescription.msk,
                    'cns': prescription.cns,
                    'boards': [{'general': pe.general, 'heent': pe.heent, 'cvs': pe.cvs, 'respiratory': pe.respiratory, 'abdomen': pe.abdomen, 'msk': pe.msk, 'cns': pe.cns} for pe in prescription.physical_examination_ids]
                },
                'gcs_scores': [{'total': g.total_score, 'motor': g.motor_response_id.name if hasattr(g, 'motor_response_id') and g.motor_response_id else '', 'verbal': g.verbal_response_id.name if hasattr(g, 'verbal_response_id') and g.verbal_response_id else '', 'eye': g.eye_response_id.name if hasattr(g, 'eye_response_id') and g.eye_response_id else ''} for g in prescription.gcs_score_line_ids],
                'bmi_records': [{'weight': b.v_weight, 'height': b.v_height, 'bmi': b.v_bmi} for b in prescription.bmi_line_ids],
                'exercises': [{'name': e.name, 'location': e.part_location.name if e.part_location else '', 'move': e.move2, 'reps': e.type_of_test2} for e in prescription.excercise_ids],
                'ortho_items': [{'name': o.name, 'side': o.side, 'location': o.location.name if o.location else ''} for o in prescription.ortho_ids],
                'old_history': [{'name': h.history_category_id.name if h.history_category_id else '', 'period': h.history_period.name if h.history_period else '', 'progression': h.progression} for h in prescription.history_id],
                'medical_history': [{'name': m.name, 'date': str(m.date) if m.date else '', 'medication': m.medication} for m in prescription.medical_history_ids],
                'past_medical_history': [{'symptom': p.symptom_id.name if p.symptom_id else '', 'result': p.result_id.name if p.result_id else ''} for p in prescription.past_medical_history_line_ids],
                'medication_history': [{'medicine': m.medicine_id.name if m.medicine_id else ''} for m in prescription.medication_history_line_ids],
                'family_history': [{'condition': f.family_history_config_id.name if f.family_history_config_id else '', 'result': f.family_history_result_id.name if f.family_history_result_id else ''} for f in prescription.family_history_line_ids],
                'social_history': [{'habit': s.social_history_config_id.name if s.social_history_config_id else '', 'result': s.social_history_result_id.name if s.social_history_result_id else ''} for s in prescription.social_history_line_ids],
                'patient_history': prescription.patient_history,
                'advice_notes': prescription.notes_line_id.name if prescription.notes_line_id else '',
                'patient_details': prescription.patient_details,
                'followup_notes': prescription.extra_notes,
                'additional_comments': prescription.additional_comments,
                'next_visit_days': prescription.next_visit_days,
            }
            return {'status': 'success', 'data': result}
        except Exception as e:
            logger.error(f"Error fetching prescription details: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/rag/trigger_indexing', type='json', auth='user', methods=['POST'])
    def api_trigger_index(self, models_list=None, incremental=False, limit=None, **kwargs):
        """
        JSON-RPC endpoint to trigger manual tracking
        """
        # Ensure user is admin to run this
        if not request.env.user.has_group('base.group_erp_manager'):
            return {'status': 'error', 'message': 'Access Denied: Only Administrator can trigger indexing'}
            
        try:
            rag_client = request.env['rag.api.client']
            result = rag_client.trigger_indexing(
                models_list=models_list, 
                incremental=incremental, 
                limit=limit
            )
            return {'status': 'success', 'data': result}
        except Exception as e:
            logger.error(f"Error triggering index: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/rag/status', type='json', auth='user', methods=['POST'])
    def api_get_status(self, **kwargs):
        """
        JSON-RPC endpoint to get RAG indexing status
        """
        try:
            rag_client = request.env['rag.api.client']
            result = rag_client.get_index_status()
            return {'status': 'success', 'data': result}
        except Exception as e:
            logger.error(f"Error fetching status: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/rag/chat', type='json', auth='user', methods=['POST'])
    def api_chat(self, prompt, session_id, patient_seq=None, reset=False, **kwargs):
        """
        JSON-RPC endpoint to handle Conversation RAG directly
        """
        try:
            rag_client = request.env['rag.api.client']
            result = rag_client.chat(
                prompt=prompt,
                session_id=session_id,
                patient_seq=patient_seq,
                reset=reset
            )
            return {'status': 'success', 'data': result}
        except Exception as e:
            logger.error(f"Error executing RAG chat: {str(e)}")
            return {'status': 'error', 'message': str(e)}
