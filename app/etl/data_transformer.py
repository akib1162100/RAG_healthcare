"""
Data Transformer for Medical Records
Converts structured Odoo data into natural language text suitable for embedding
"""
from typing import Dict, List, Tuple, Any
from datetime import datetime, date
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class MedicalDataTransformer:
    """Transform structured medical data into natural language"""
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def flatten_appointment(self, appointment: Dict) -> Tuple[str, Dict]:
        """
        Convert appointment data to natural language text
        
        Args:
            appointment: Appointment dictionary from extractor
            
        Returns:
            Tuple of (flattened_text, metadata)
        """
        parts = []
        
        # Appointment header
        parts.append(f"Appointment {appointment['appointment_number']}")
        parts.append(f"Date: {appointment['appoint_date']}")
        parts.append(f"Status: {appointment['appoint_state']}")
        
        # Patient information
        if appointment.get('patient_name'):
            parts.append(f"\nPatient: {appointment['patient_name']}")
            if appointment.get('patient_id'):
                parts.append(f"(ID: {appointment['patient_id']})")
            if appointment.get('patient_age'):
                parts.append(f", {appointment['patient_age']} years old")
            if appointment.get('patient_gender'):
                parts.append(f", {str(appointment['patient_gender']).capitalize()}")
        
        # Doctor information
        if appointment.get('doctor_name'):
            parts.append(f"\nDoctor: {appointment['doctor_name']}")
            if appointment.get('doctor_designation'):
                parts.append(f" ({appointment['doctor_designation']})")
        
        # Appointment details
        dt_start = appointment.get('app_dt_start')
        dt_stop = appointment.get('app_dt_stop')
        if dt_start and dt_stop:
            start_str = dt_start.strftime("%H:%M") if hasattr(dt_start, "strftime") else str(dt_start)[:16]
            stop_str = dt_stop.strftime("%H:%M") if hasattr(dt_stop, "strftime") else str(dt_stop)[:16]
            parts.append(f"\nTime: {start_str} - {stop_str}")
        elif appointment.get('time_from') and appointment.get('time_to'):
            parts.append(f"\nTime: {self._format_time(appointment['time_from'])} - {self._format_time(appointment['time_to'])}")
        
        if appointment.get('description'):
            parts.append(f"\nChief Complaint: {appointment['description']}")
        
        if appointment.get('amount_total'):
            parts.append(f"\nConsultation Fee: {appointment['amount_total']}")
        
        text = " ".join(parts)
        
        # Create metadata
        metadata = {
            'odoo_model': 'wk.appointment',
            'odoo_res_id': appointment['id'],
            'patient_id': appointment.get('patient_res_id'),
            'patient_seq': appointment.get('patient_id'),
            'doctor_id': appointment.get('doctor_res_id'),
            'appointment_date': str(appointment['appoint_date']),
            'appointment_state': appointment['appoint_state'],
            'indexed_at': datetime.now().isoformat()
        }
        
        return text, self._sanitize_for_json(metadata)
    
    def flatten_prescription(self, prescription: Dict) -> List[Tuple[str, Dict]]:
        """
        Convert prescription data to natural language text
        May return multiple chunks if content is long
        
        Args:
            prescription: Prescription dictionary from extractor
            
        Returns:
            List of (flattened_text, metadata) tuples
        """
        # Build comprehensive prescription text
        full_text = self._build_prescription_text(prescription)
        
        # Create base metadata
        base_metadata = {
            'odoo_model': 'prescription.order.knk',
            'odoo_res_id': prescription['id'],
            'patient_id': prescription.get('patient_res_id'),
            'patient_seq': prescription.get('patient_id'),
            'physician_id': prescription.get('physician_res_id'),
            'prescription_date': str(prescription['prescription_date']),
            'state': prescription.get('state'),
            'disease': prescription.get('disease'),
            'description': prescription.get('description'),
            'diagnosis_codes': [d.get('disease_code') for d in prescription.get('diagnoses', []) if d.get('disease_code')] + 
                               [d.get('secondary_diagnosis_name') for d in prescription.get('diagnoses', []) if d.get('secondary_diagnosis_name')],
            
            # Insert full related data lists directly into Metadata
            'medications': prescription.get('medications', []),
            'diagnoses': prescription.get('diagnoses', []),
            'complaints': prescription.get('complaints', []),
            'investigations': prescription.get('investigations', []),
            'vitals': prescription.get('vitals', []),
            'signs': prescription.get('signs', []),
            'past_medical_history': prescription.get('past_medical_history', []),
            'medication_history': prescription.get('medication_history', []),
            'family_history': prescription.get('family_history', []),
            'social_history': prescription.get('social_history', []),
            'exercises': prescription.get('exercises', []),
            'ortho': prescription.get('ortho', []),
            'old_history': prescription.get('old_history', []),
            'medical_history': prescription.get('medical_history', []),
            'advice_notes': prescription.get('advice_notes', []),
            
            # Newly added 
            'physical_examinations': prescription.get('physical_examinations', []),
            'procedures': prescription.get('procedures', []),
            'gcs_scores': prescription.get('gcs_scores', []),
            'bmi_records': prescription.get('bmi_records', []),
            
            # Clinical Scalars
            'clinical_scalars': {
                'v_weight': prescription.get('v_weight'),
                'v_height': prescription.get('v_height'),
                'v_bmi': prescription.get('v_bmi'),
                'blood_presure': prescription.get('blood_presure'),
                'blood_presure_2': prescription.get('blood_presure_2'),
                'pulse': prescription.get('v_pulse'),
                'respiratory_rate': prescription.get('v_respiratory_rate'),
                'temperature': prescription.get('temperature'),
                'spo2': prescription.get('spo2'),
                'rbs': prescription.get('rbs'),
                'pain_score': prescription.get('pain_score'),
                'dyspnea': prescription.get('dyspnea'),
                'cardiac_rythm': prescription.get('cardiac_rythm'),
                'nihss': prescription.get('nihss'),
                'motor_power': prescription.get('motor_power'),
                'pupil_reaction': prescription.get('pupil_reaction')
            },
            
            'status_updates': {
                'symptom_status': prescription.get('symptom_status'),
                'medication_adherence': prescription.get('medication_adherence'),
                'performance_status_update': prescription.get('performance_status_update'),
                'counseling_behavioral_response': prescription.get('counseling_behavioral_response'),
                'side_effects': prescription.get('side_effects')
            },
            
            'indexed_at': datetime.now().isoformat()
        }
        
        # Check if chunking is needed (ClinicalBERT has 512 token limit ~400 words)
        if len(full_text.split()) > 350:  # Conservative estimate
            chunks = self._chunk_text(full_text)
            results = []
            for idx, chunk in enumerate(chunks):
                metadata = base_metadata.copy()
                metadata['chunk_index'] = idx
                metadata['total_chunks'] = len(chunks)
                results.append((chunk, self._sanitize_for_json(metadata)))
            return results
        else:
            base_metadata['chunk_index'] = 0
            base_metadata['total_chunks'] = 1
            return [(full_text, self._sanitize_for_json(base_metadata))]
    
    def _build_prescription_text(self, prescription: Dict) -> str:
        """Build comprehensive prescription text"""
        parts = []
        
        # Header
        parts.append(f"Prescription {prescription.get('prescription_number') or 'Unknown'}")
        parts.append(f"Date: {prescription.get('prescription_date') or 'Unknown'}")
        
        # Patient information
        if prescription.get('patient_name'):
            parts.append(f"\nPatient: {prescription['patient_name']}")
            if prescription.get('patient_id'):
                parts.append(f"(ID: {prescription['patient_id']})")
            if prescription.get('patient_age'):
                parts.append(f", {prescription['patient_age']} years old")
            gender = prescription.get('patient_sex') or prescription.get('patient_gender')
            if gender:
                parts.append(f", {str(gender).capitalize()}")
        
        # Physician information
        if prescription.get('physician_name'):
            parts.append(f"\nPhysician: {prescription['physician_name']}")
            if prescription.get('physician_designation'):
                parts.append(f" ({prescription['physician_designation']})")
        
        # Diagnoses
        if prescription.get('diagnoses'):
            parts.append("\n\nDiagnosis:")
            for diag in prescription['diagnoses']:
                if diag.get('disease_name'):
                    diag_text = diag['disease_name']
                    if diag.get('disease_code'):
                        diag_text += f" (ICD: {diag['disease_code']})"
                    if diag.get('disease_long_name'):
                        diag_text += f" - {diag['disease_long_name']}"
                    parts.append(f"\n- Primary: {diag_text}")
                
                if diag.get('secondary_diagnosis_name'):
                    parts.append(f"\n- Secondary: {diag['secondary_diagnosis_name']}")
        
        # Chief Complaints
        if prescription.get('complaints'):
            parts.append("\n\nChief Complaints:")
            for complaint in prescription['complaints']:
                complaint_text = complaint.get('complaint') or ''
                if complaint.get('period'):
                    complaint_text += f" for {complaint['period']}"
                if complaint.get('location'):
                    complaint_text += f" at {complaint['location']}"
                if complaint_text.strip():
                    parts.append(f"\n- {complaint_text}")
        
        # Medications Prescribed
        if prescription.get('medications'):
            parts.append("\n\nMedications Prescribed:")
            for med in prescription['medications']:
                if med.get('medication_name'):
                    med_text = f"\n- {med['medication_name']}"
                    if med.get('dose'):
                        med_text += f" {med['dose']}"
                    if med.get('frequency'):
                        med_text += f", {med['frequency']}"
                    if med.get('route'):
                        med_text += f", {med['route']}"
                    if med.get('when_to_take'):
                        med_text += f", {med['when_to_take']}"
                    if med.get('days'):
                        parts.append(f" for {med['days']} days")
                    elif med.get('duration_unit') and med.get('duration_value'):
                        parts.append(f" for {med['duration_value']} {med['duration_unit']}")
                    
                    if med.get('qty_per_day'):
                        med_text += f" ({med['qty_per_day']}/day)"
                    
                    if med.get('allergy_status') == 'yes':
                        med_text += f" [ALLERGY WARNING TRIGGERED]"
                        
                    if med.get('special_instruction'):
                        med_text += f"\n  Special Instructions: {med['special_instruction']}"
                    parts.append(med_text)
        
        # Investigations
        if prescription.get('investigations'):
            parts.append("\n\nInvestigations Ordered:")
            for inv in prescription['investigations']:
                if inv.get('investigation_name'):
                    parts.append(f"\n- {inv['investigation_name']}")
        
        # Investigation Results
        if prescription.get('investigation_result'):
            parts.append(f"\n\nInvestigation Results:\n{prescription['investigation_result']}")
        
        # Vital Signs
        if prescription.get('vitals') or prescription.get('bmi_records') or any(['temperature' in prescription, 'spo2' in prescription, 'rbs' in prescription]):
            parts.append("\n\nVital Signs:")
            # Extract standard vitals if available
            for vital in prescription.get('vitals', []):
                if vital.get('weight'):
                    parts.append(f"\n- Weight: {vital['weight']} {vital.get('weight_unit', '')}")
                if vital.get('height'):
                    parts.append(f"\n- Height: {vital['height']} {vital.get('height_unit', '')}")
                if vital.get('bp_systolic'):
                    bp = f"{vital['bp_systolic']}"
                    if vital.get('bp_diastolic'):
                        bp += f"/{vital['bp_diastolic']}"
                    parts.append(f"\n- Blood Pressure: {bp} {vital.get('bp_unit', 'mmHg')}")
                if vital.get('pulse'):
                    parts.append(f"\n- Pulse: {vital['pulse']} {vital.get('pulse_unit', 'bpm')}")
                if vital.get('respiratory_rate'):
                    parts.append(f"\n- Respiratory Rate: {vital['respiratory_rate']} {vital.get('rr_unit', '/min')}")
            
            # Extract specific BMI records
            for bmi in prescription.get('bmi_records', []):
                if bmi.get('weight'):
                    parts.append(f"\n- Weight: {bmi['weight']} {bmi.get('weight_unit', '')}")
                if bmi.get('height'):
                    parts.append(f"\n- Height: {bmi['height']} {bmi.get('height_unit', '')}")
                if bmi.get('bmi_value'):
                    parts.append(f"\n- BMI: {bmi['bmi_value']} {bmi.get('bmi_unit', '')}")
                    
            # Extract standalone scalar vitals directly on prescription
            if prescription.get('temperature'):
                parts.append(f"\n- Temperature: {prescription['temperature']}")
            if prescription.get('spo2'):
                parts.append(f"\n- SpO2: {prescription['spo2']}%")
            if prescription.get('rbs'):
                parts.append(f"\n- Random Blood Sugar (RBS): {prescription['rbs']}")
            if prescription.get('v_weight'):
                parts.append(f"\n- Weight (Scalar): {prescription['v_weight']}")
            if prescription.get('v_height'):
                parts.append(f"\n- Height (Scalar): {prescription['v_height']}")
            if prescription.get('v_bmi'):
                parts.append(f"\n- BMI (Scalar): {prescription['v_bmi']}")
            if prescription.get('blood_presure'):
                bp = f"{prescription['blood_presure']}"
                if prescription.get('blood_presure_2'):
                    bp += f"/{prescription['blood_presure_2']}"
                parts.append(f"\n- Blood Pressure (Scalar): {bp}")
            if prescription.get('v_pulse'):
                parts.append(f"\n- Pulse (Scalar): {prescription['v_pulse']}")
            if prescription.get('v_respiratory_rate'):
                parts.append(f"\n- Respiratory Rate (Scalar): {prescription['v_respiratory_rate']}")
                
        # Clinical Scores & Classifications
        if any([prescription.get('gcs_scores'), prescription.get('nihss'), prescription.get('pain_score'), prescription.get('motor_power'), prescription.get('dyspnea'), prescription.get('cardiac_rythm')]):
            parts.append("\n\nClinical Scores & Classifications:")
            
            if prescription.get('pain_score') is not None:
                parts.append(f"\n- Pain Score: {prescription['pain_score']}")
            if prescription.get('motor_power') is not None:
                parts.append(f"\n- Motor Power: {prescription['motor_power']}")
            if prescription.get('nihss') is not None:
                parts.append(f"\n- NIHSS (Neuro Score): {prescription['nihss']}")
            if prescription.get('dyspnea'):
                parts.append(f"\n- Dyspnea (NYHA): Grade {str(prescription['dyspnea']).upper()}")
            if prescription.get('cardiac_rythm'):
                parts.append(f"\n- Cardiac Rhythm: {prescription['cardiac_rythm']} (Type: {prescription.get('cardiac_rythm_type', 'Unknown')})")
            
            pupil_l = prescription.get('pupil_reaction')
            pupil_r = prescription.get('pupil_reaction_right')
            if pupil_l or pupil_r:
                parts.append(f"\n- Pupil Reaction: Left [{pupil_l or 'N/A'}] / Right [{pupil_r or 'N/A'}]")
                
            # Glasgow Coma Scale
            if prescription.get('gcs_scores'):
                for idx, gcs in enumerate(prescription['gcs_scores']):
                    parts.append(f"\n- Glasgow Coma Scale (Record #{idx+1}): Total Score = {gcs.get('total_score', 'Unknown')}")
                    if gcs.get('motor_response'):
                        parts.append(f"\n  * Motor Response: {gcs['motor_response']} (Score: {gcs.get('motor_score', '')})")
                    if gcs.get('verbal_response'):
                        parts.append(f"\n  * Verbal Response: {gcs['verbal_response']} (Score: {gcs.get('verbal_score', '')})")
                    if gcs.get('eye_response'):
                        parts.append(f"\n  * Eye Response: {gcs['eye_response']} (Score: {gcs.get('eye_score', '')})")
            elif prescription.get('glassgow_coma_scale'):
                parts.append(f"\n- Glasgow Coma Scale (Scalar): {prescription['glassgow_coma_scale']}")

        # Physical Examinations
        if prescription.get('physical_examinations') or any([prescription.get('general'), prescription.get('abdomen'), prescription.get('respiratory')]):
            parts.append("\n\nPhysical Examinations:")
            
            # Array relations
            for exam in prescription.get('physical_examinations', []):
                parts.append(f"\n- Physical Board #{exam.get('sequence', 'N/A')}:")
                if exam.get('general'): parts.append(f"\n  * General: {exam['general']}")
                if exam.get('heent'): parts.append(f"\n  * HEENT: {exam['heent']}")
                if exam.get('cvs'): parts.append(f"\n  * CVS: {exam['cvs']}")
                if exam.get('respiratory'): parts.append(f"\n  * Respiratory: {exam['respiratory']}")
                if exam.get('abdomen'): parts.append(f"\n  * Abdomen: {exam['abdomen']}")
                if exam.get('msk'): parts.append(f"\n  * Musculoskeletal: {exam['msk']}")
                if exam.get('cns'): parts.append(f"\n  * CNS Screens: {exam['cns']}")
                
            # Scalar relations fallback
            if not prescription.get('physical_examinations'):
                if prescription.get('general'): parts.append(f"\n- General: {prescription['general']}")
                if prescription.get('heent'): parts.append(f"\n- HEENT: {prescription['heent']}")
                if prescription.get('cvs'): parts.append(f"\n- CVS: {prescription['cvs']}")
                if prescription.get('respiratory'): parts.append(f"\n- Respiratory: {prescription['respiratory']}")
                if prescription.get('abdomen'): parts.append(f"\n- Abdomen: {prescription['abdomen']}")
                if prescription.get('msk'): parts.append(f"\n- Musculoskeletal: {prescription['msk']}")
                if prescription.get('cns'): parts.append(f"\n- CNS Screens: {prescription['cns']}")
        
        # Patient History
        if prescription.get('patient_history'):
            parts.append(f"\n\nGeneral Patient History:\n{prescription['patient_history']}")
            
        # Old History
        if prescription.get('old_history'):
            parts.append("\n\nOld History:")
            for oh in prescription['old_history']:
                item = []
                if oh.get('history_name'): item.append(oh['history_name'])
                if oh.get('period_name'): item.append(f"Period: {oh['period_name']}")
                if oh.get('category_name'): item.append(f"Category: {oh['category_name']}")
                if oh.get('progression'): item.append(f"Progression: {oh['progression']}")
                if oh.get('severity'): item.append(f"Severity: {oh['severity']}")
                if oh.get('associated_symptoms'): item.append(f"Symptoms: {oh['associated_symptoms']}")
                if item: parts.append(f"\n- {' - '.join(item)}")

        # Medical History (Patient History Lines)
        if prescription.get('medical_history'):
            parts.append("\n\nMedical History:")
            for mh in prescription['medical_history']:
                item = []
                if mh.get('history_text'): item.append(mh['history_text'])
                if mh.get('date'): item.append(f"Date: {mh['date']}")
                if mh.get('medication'): item.append(f"Medication: {mh['medication']}")
                if mh.get('investigation'): item.append(f"Investigation: {mh['investigation']}")
                if item: parts.append(f"\n- {' - '.join(item)}")

        # Signs / Examinations
        if prescription.get('signs'):
            parts.append("\n\nExaminations / Signs:")
            for sign in prescription['signs']:
                if sign.get('sign_name'):
                    sign_text = f"\n- {sign['sign_name']}"
                    if sign.get('location'):
                        sign_text += f" at {sign['location']}"
                    if sign.get('intensity'):
                        sign_text += f" (Intensity: {sign['intensity']})"
                    parts.append(sign_text)



        # Exercises
        if prescription.get('exercises'):
            parts.append("\n\nPrescribed Exercises:")
            for ex in prescription['exercises']:
                if ex.get('exercise_name'):
                    ex_text = f"\n- {ex['exercise_name']}"
                    if ex.get('part_location'):
                        ex_text += f" for {ex['part_location']}"
                    if ex.get('move'):
                        ex_text += f" (Move: {ex['move']})"
                    if ex.get('repitition'):
                        ex_text += f" (Reps/Duration: {ex['repitition']})"
                    parts.append(ex_text)

        # Ortho Items
        if prescription.get('ortho'):
            parts.append("\n\nOrthopedic Items Prescribed:")
            for ortho in prescription['ortho']:
                if ortho.get('item_name'):
                    ortho_text = f"\n- {ortho['item_name']}"
                    if ortho.get('location'):
                        ortho_text += f" for {ortho['location']}"
                    if ortho.get('side'):
                        ortho_text += f" ({ortho['side']} side)"
                    parts.append(ortho_text)
        
        if prescription.get('procedures'):
            parts.append("\n\nProcedures Performed:")
            for proc in prescription['procedures']:
                if proc.get('procedure_name'):
                    parts.append(f"\n- {proc['procedure_name']}")
                    
        # Family History
        if prescription.get('family_history'):
            parts.append("\n\nFamily History:")
            for fh in prescription['family_history']:
                item = []
                if fh.get('condition_name'): item.append(fh['condition_name'])
                if fh.get('result_name'): item.append(f"Result: {fh['result_name']}")
                if item: parts.append(f"\n- {' - '.join(item)}")

        # Social History
        if prescription.get('social_history'):
            parts.append("\n\nSocial History:")
            for sh_item in prescription['social_history']:
                sh_parts = []
                if sh_item.get('habit_name'): sh_parts.append(sh_item['habit_name'])
                if sh_item.get('result_name'): sh_parts.append(f"Result: {sh_item['result_name']}")
                if sh_parts: parts.append(f"\n- {' - '.join(sh_parts)}")
                
        # Signs List
        if prescription.get('signs'):
            parts.append("\n\nExaminations (Signs):")
            for sign in prescription['signs']:
                sign_str = []
                if sign.get('examination_name'): sign_str.append(sign['examination_name'])
                if sign.get('location'): sign_str.append(f"(Location: {sign['location']})")
                if sign.get('intensity'): sign_str.append(f"- Intensity: {sign['intensity']}")
                if sign_str: parts.append(f"\n- {' '.join(sign_str)}")
                
        # Procedure Results
        if prescription.get('procedure_result'):
            parts.append(f"\n\nProcedure Results:\n{prescription['procedure_result']}")
        
        # Clinical Status & Recommendations
        if prescription.get('symptom_status'):
            parts.append(f"\n\nSymptom Status: {prescription['symptom_status']}")
        
        if prescription.get('medication_adherence'):
            parts.append(f"\nMedication Adherence: {prescription['medication_adherence']}")
            
        if prescription.get('performance_status_update'):
            parts.append(f"\nPerformance Status Update: {prescription['performance_status_update']}")
            
        if prescription.get('counseling_behavioral_response'):
            parts.append(f"\nCounseling & Behavioral Response: {prescription['counseling_behavioral_response']}")
        
        # Side Effects
        if prescription.get('side_effects'):
            parts.append(f"\n\nSide Effects/Toxicities:\n{prescription['side_effects']}")
            
        # Follow-up Schedule
        if prescription.get('date_of_next_visit') or prescription.get('next_visit_days'):
            parts.append("\n\nFollow-Up Schedule:")
            if prescription.get('date_of_next_visit'):
                parts.append(f"\n- Next Visit Date: {prescription['date_of_next_visit']}")
            if prescription.get('next_visit_days'):
                parts.append(f"\n- Recall Timeframe: {prescription['next_visit_days']} days")
        
        # Advice Notes
        if prescription.get('advice_notes'):
            parts.append("\n\nAdvice/Notes:")
            for note in prescription['advice_notes']:
                if note.get('notes_text'):
                    parts.append(f"\n- {note['notes_text']}")

        # Additional Comments & Details
        if prescription.get('additional_comments'):
            parts.append(f"\n\nAdditional Comments:\n{prescription['additional_comments']}")
        
        if prescription.get('patient_details'):
            parts.append(f"\nPatient Details (Internal Notes):\n{prescription['patient_details']}")
            
        if prescription.get('check_patient'):
            parts.append(f"\nCheck Patient Context:\n{prescription['check_patient']}")
            
        if prescription.get('extra_notes'):
            parts.append(f"\nExtra Notes:\n{prescription['extra_notes']}")
        
        # General Description
        if prescription.get('description'):
            parts.append(f"\n\nDescription/Summary:\n{prescription['description']}")
        
        return " ".join(parts)
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split long text into chunks with overlap
        Uses word-based chunking to preserve context
        """
        words = text.split()
        chunks = []
        
        # Calculate words per chunk (rough estimate: 1 token ≈ 0.75 words)
        words_per_chunk = int(self.chunk_size * 0.75)
        overlap_words = int(self.chunk_overlap * 0.75)
        
        start = 0
        while start < len(words):
            end = start + words_per_chunk
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))
            
            # Move start position with overlap
            start = end - overlap_words
            if start >= len(words):
                break
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def _format_time(self, time_float: float) -> str:
        """Convert Odoo time float to HH:MM format"""
        hours = int(time_float)
        minutes = int((time_float - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"

    def _sanitize_for_json(self, obj: Any) -> Any:
        """Recursively convert datetime/date/decimal into JSON serializable types"""
        if isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(item) for item in obj if item is not None]
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        else:
            return str(obj)
