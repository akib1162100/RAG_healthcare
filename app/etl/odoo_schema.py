"""
Odoo Medical Data Model Schema Mapping
Maps Odoo models to PostgreSQL tables and defines key fields for extraction
"""

# Odoo model to PostgreSQL table mapping
ODOO_MODEL_MAPPING = {
    'wk.appointment': {
        'table': 'wk_appointment',
        'description': 'Patient appointments with doctors',
        'key_fields': [
            'id', 'name', 'appoint_date', 'appoint_state',
            'customer', 'appoint_person_id', 'description',
            'app_phone', 'app_email', 'time_from', 'time_to',
            'amount_total', 'write_date', 'create_date'
        ],
        'relations': {
            'customer': ('res_partner', 'id', 'patient'),  # Patient
            'appoint_person_id': ('res_partner', 'id', 'doctor'),  # Doctor
        },
        'filter': "appoint_state != 'rejected'",  # Only non-rejected appointments
    },
    
    'prescription.order.knk': {
        'table': 'prescription_order_knk',
        'description': 'Prescription orders with medications and diagnoses',
        'key_fields': [
            'id', 'name', 'date', 'state', 'patient_id', 'physician_id',
            'description', 'patient_history', 'investigation_result',
            'procedure_result', 'disease', 'short_code', 
            'symptom_status', 'medication_adherence', 'side_effects',
            'additional_comments', 'write_date', 'create_date',
            'v_weight', 'v_height', 'v_bmi', 'blood_presure', 'blood_presure_2',
            'v_pulse', 'v_respiratory_rate', 'temperature', 'spo2', 'rbs',
            'motor_power', 'pupil_reaction', 'pupil_reaction_right', 'nihss',
            'pain_score', 'dyspnea', 'cardiac_rythm_type', 'cardiac_rythm', 'glassgow_coma_scale',
            'general', 'heent', 'cvs', 'respiratory', 'abdomen', 'msk', 'cns',
            'performance_status_update', 'counseling_behavioral_response',
            'next_visit_days', 'date_of_next_visit', 'extra_notes', 'patient_details', 'check_patient'
        ],
        'relations': {
            'patient_id': ('res_partner', 'id', 'patient'),
            'physician_id': ('res_partner', 'id', 'physician'),
            'notes_line_id': ('note_note', 'id', 'notes'),
        },
        'one2many': {
            'medications': ('prescription_order_line_knk_new', 'prescription_id'),
            'diagnoses': ('diagnosis_diagnosis', 'diagnosis_res_id'),
            'complaints': ('complaint_record_line', 'complain_res_id'),
            'investigations': ('investigation_list_line', 'inves_res_id'),
            'vitals': ('vital_list_line', 'vital_list_id'),
            'history': ('history_list_line', 'history_res_id'),
            'physical_examinations': ('physical_examination_line', 'prescription_id'),
            'procedures': ('procedure_history', 'prescription_id'),
            'gcs_scores': ('gcs_score_line', 'prescription_order_id'),
            'bmi_records': ('vital_bmi_line', 'prescription_id'),
            'exercises': ('excercise_ex_line', 'excer_res_id'),
            'ortho_items': ('ortho_list_line', 'ortho_list_id'),
            'past_medical_history': ('past_medical_history', 'prescription_id'),
            'medication_history': ('medication_history', 'prescription_id'),
            'family_history': ('family_history', 'prescription_id'),
            'social_history': ('social_history', 'prescription_id'),
            'signs': ('sign_list_line', 'sign_res_id'),
            'old_history': ('history_list_line', 'history_res_id'),
            'medical_history': ('patient_history_line', 'pat_medical_his_id'),
        },
        'relations': {
            'patient_id': ('res_partner', 'id', 'patient'),
            'physician_id': ('res_partner', 'id', 'physician'),
            'notes_line_id': ('note_note', 'id', 'notes'),
        },
        'filter': "state = 'prescribed'",  # Only confirmed prescriptions
    },
    
    'res.partner': {
        'table': 'res_partner',
        'description': 'Patients and physicians',
        'key_fields': [
            'id', 'name', 'seq', 'date_of_birth', 'age', 'gender',
            'partner_type', 'patient_medical_history', 'phone', 'email',
            'city', 'state_id', 'country_id', 'designation',
            'write_date', 'create_date'
        ],
        'filter': "partner_type IN ('patient', 'physician')",
    },
    
    'medical.disease': {
        'table': 'medical_disease',
        'description': 'ICD disease codes and names',
        'key_fields': ['id', 'code', 'name', 'long_name'],
    },
}

# Medication line fields
MEDICATION_LINE_FIELDS = [
    'id', 'prescription_id', 'product_id', 'quantity', 'duration',
    'dose', 'frequency', 'route', 'when_to_take', 'special_instruction'
]

# Diagnosis fields
DIAGNOSIS_FIELDS = [
    'id', 'diagnosis_res_id', 'disease_id', 'disease_short_code_id'
]

# Complaint fields
COMPLAINT_FIELDS = [
    'id', 'complain_res_id', 'complaint_list_id', 'period', 'location_id'
]

# Investigation fields
INVESTIGATION_FIELDS = [
    'id', 'inves_res_id', 'test_type', 'investigation_list_id'
]

# Vital signs fields
VITAL_FIELDS = [
    'id', 'vital_list_id', 'vital_name', 'vital_value', 'vital_uom'
]
