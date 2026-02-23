"""
Data Extractor for Odoo Medical Models
Extracts data from Odoo PostgreSQL database with proper joins
"""
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
import logging

from .odoo_schema import ODOO_MODEL_MAPPING

logger = logging.getLogger(__name__)


class OdooDataExtractor:
    """Extract data from Odoo medical models"""
    
    def __init__(self, odoo_engine: AsyncEngine, vector_engine: AsyncEngine):
        self.engine = odoo_engine
        self.vector_engine = vector_engine
    
    async def extract_appointments(
        self, 
        limit: Optional[int] = None,
        since_date: Optional[datetime] = None,
        incremental: bool = True
    ) -> List[Dict]:
        """
        Extract appointment data with patient and doctor information
        
        Args:
            limit: Maximum number of records to extract
            since_date: Only extract records modified after this date
            incremental: If true, only fetches records marked as not synced
            
        Returns:
            List of appointment dictionaries
        """
        query = """
        SELECT 
            a.id,
            a.name AS appointment_number,
            a.appoint_date,
            a.appoint_state,
            a.description,
            a.app_dt_start,
            a.app_dt_stop,
            a.amount_total,
            a.write_date,
            -- Patient information
            p_patient.name AS patient_name,
            p_patient.seq AS patient_id,
            p_patient.age AS patient_age,
            p_patient.gender AS patient_gender,
            p_patient.phone AS patient_phone,
            p_patient.email AS patient_email,
            p_patient.id AS patient_res_id,
            -- Doctor information
            p_doctor.name AS doctor_name,
            p_doctor.designation AS doctor_designation,
            p_doctor.id AS doctor_res_id
        FROM wk_appointment a
        LEFT JOIN res_partner p_patient ON a.customer = p_patient.id
        LEFT JOIN res_partner p_doctor ON a.appoint_person_id = p_doctor.id
        WHERE a.appoint_state != 'rejected'
        """
        
        if incremental:
            query += " AND a.is_rag_synced = False"
        
        params = {}
        query += " ORDER BY a.write_date DESC"
        
        if limit:
            query += " LIMIT :limit"
            params['limit'] = limit
        
        async with self.engine.connect() as conn:
            result = await conn.execute(text(query), params)
            rows = result.fetchall()
            
            appointments = []
            for row in rows:
                appointments.append(dict(row._mapping))
                
            logger.info(f"Extracted {len(appointments)} appointments")
            return appointments
    
    async def extract_prescriptions(
        self,
        limit: Optional[int] = None,
        since_date: Optional[datetime] = None,
        incremental: bool = True
    ) -> List[Dict]:
        """
        Extract prescription data with patient, physician, and related information
        
        Returns:
            List of prescription dictionaries with nested related data
        """
        # Main prescription query
        query = """
        SELECT 
            p.id,
            p.name AS prescription_number,
            p.date AS prescription_date,
            p.state,
            p.description,
            p.patient_history,
            p.investigation_result,
            p.procedure_result,
            p.disease,
            p.short_code,
            p.symptom_status,
            p.medication_adherence,
            p.side_effects,
            p.additional_comments,
            p.write_date,
            p.notes_line_id,
            -- Enriched Scalars (adjusted to match actual DB schema)
            p.weight AS v_weight, 
            p.height AS v_height, 
            p.bmi AS v_bmi, 
            p.systolic AS blood_presure, 
            p.diastolic AS blood_presure_2,
            p.pulse AS v_pulse, 
            p.respiratory_rate AS v_respiratory_rate,
            p.performance_status_update,
            p.next_visit_days, p.date_of_next_visit, p.extra_notes, p.patient_details, p.check_patient,
            -- Patient information
            patient.name AS patient_name,
            patient.seq AS patient_id,
            patient.age AS patient_age,
            patient.gender AS patient_gender,
            p.patient_sex AS patient_sex,
            patient.id AS patient_res_id,
            -- Physician information
            physician.name AS physician_name,
            physician.designation AS physician_designation,
            physician.id AS physician_res_id
        FROM prescription_order_knk p
        LEFT JOIN res_partner patient ON p.patient_id = patient.id
        LEFT JOIN res_partner physician ON p.physician_id = physician.id
        WHERE p.state != 'cancelled'
        """
        
        if incremental:
            query += " AND p.is_rag_synced = False"
        
        params = {}
        
        query += " ORDER BY p.write_date DESC"
        
        if limit:
            query += " LIMIT :limit"
            params['limit'] = limit
        
        async with self.engine.connect() as conn:
            result = await conn.execute(text(query), params)
            rows = result.fetchall()
            
            prescriptions = []
            for row in rows:
                prescription = dict(row._mapping)
                prescription_id = prescription['id']
                
                # Fetch related data
                prescription['medications'] = await self._get_medications(conn, prescription_id)
                prescription['diagnoses'] = await self._get_diagnoses(conn, prescription_id)
                prescription['complaints'] = await self._get_complaints(conn, prescription_id)
                prescription['investigations'] = await self._get_investigations(conn, prescription_id)
                prescription['vitals'] = await self._get_vitals(conn, prescription_id)
                prescription['signs'] = await self._get_signs(conn, prescription_id)
                prescription['past_medical_history'] = await self._get_past_medical_history(conn, prescription_id)
                prescription['medication_history'] = await self._get_medication_history(conn, prescription_id)
                prescription['family_history'] = await self._get_family_history(conn, prescription_id)
                prescription['social_history'] = await self._get_social_history(conn, prescription_id)
                prescription['exercises'] = await self._get_exercises(conn, prescription_id)
                prescription['ortho'] = await self._get_ortho(conn, prescription_id)
                
                # New Extractions
                prescription['old_history'] = await self._get_old_history(conn, prescription_id)
                prescription['medical_history'] = await self._get_medical_history(conn, prescription_id)
                if prescription.get('notes_line_id'):
                    prescription['advice_notes'] = await self._get_advice_notes(conn, prescription['notes_line_id'])
                else:
                    prescription['advice_notes'] = []
                
                # Enriched Relationships
                prescription['physical_examinations'] = await self._get_physical_examinations(conn, prescription_id)
                prescription['procedures'] = await self._get_procedures(conn, prescription_id)
                prescription['gcs_scores'] = await self._get_gcs_scores(conn, prescription_id)
                prescription['bmi_records'] = await self._get_bmi_records(conn, prescription_id)
                
                prescriptions.append(prescription)
            
            logger.info(f"Extracted {len(prescriptions)} prescriptions")
            return prescriptions
    
    async def _get_medications(self, conn, prescription_id: int) -> List[Dict]:
        """Get medication lines for a prescription"""
        query = """
        SELECT 
            med.id,
            prod.name AS medication_name,
            med.quantity,
            med.days,
            med.qty_per_day,
            med.short_comment AS special_instruction
        FROM prescription_order_line_knk_new med
        LEFT JOIN product_product pp ON med.product_id = pp.id
        LEFT JOIN product_template prod ON pp.product_tmpl_id = prod.id
        WHERE med.prescription_id = :prescription_id
        """
        try:
            result = await conn.execute(text(query), {'prescription_id': prescription_id})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract medications: {e}")
            return []
    
    async def _get_diagnoses(self, conn, prescription_id: int) -> List[Dict]:
        """Get diagnoses for a prescription"""
        query = """
        SELECT 
            d.id,
            disease.code AS disease_code,
            disease.name AS disease_name,
            disease.long_name AS disease_long_name
        FROM diagnosis_diagnosis d
        LEFT JOIN medical_disease disease ON d.disease_id = disease.id
        WHERE d.diagnosis_res_id = :prescription_id
        """
        try:
            result = await conn.execute(text(query), {'prescription_id': prescription_id})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract diagnoses: {e}")
            return []
    
    async def _get_complaints(self, conn, prescription_id: int) -> List[Dict]:
        """Get complaints for a prescription"""
        query = """
        SELECT 
            c.id,
            cl.name AS complaint,
            pr.name AS period,
            loc.name AS location
        FROM complaint_record_line c
        LEFT JOIN complaint_list cl ON c.complaint_list_id = cl.id
        LEFT JOIN period_record pr ON c.period = pr.id
        LEFT JOIN location_location loc ON c.location_id = loc.id
        WHERE c.complain_res_id = :prescription_id
        """
        result = await conn.execute(text(query), {'prescription_id': prescription_id})
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def _get_investigations(self, conn, prescription_id: int) -> List[Dict]:
        """Get investigations for a prescription"""
        query = """
        SELECT 
            i.id,
            il.name AS investigation_name
        FROM investigation_list_line i
        LEFT JOIN investigation_list il ON i.investigation_list_id = il.id
        WHERE i.inves_res_id = :prescription_id
        """
        result = await conn.execute(text(query), {'prescription_id': prescription_id})
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def _get_vitals(self, conn, prescription_id: int) -> List[Dict]:
        """Get vital signs for a prescription"""
        query = """
        SELECT 
            v.id,
            v.name AS weight,
            v.w_unit AS weight_unit,
            v.height,
            v.h_unit AS height_unit,
            v.blood_presure AS bp_systolic,
            v.slash_tag,
            v.blood_presure_2 AS bp_diastolic,
            v.blood_unit AS bp_unit,
            v.pulse,
            v.pulse_unit,
            v.respiratory_rate,
            v.rr_unit
        FROM vital_list_line v
        WHERE v.vital_list_id = :prescription_id
        """
        try:
            result = await conn.execute(text(query), {'prescription_id': prescription_id})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract vitals: {e}")
            return []

    async def _get_signs(self, conn, prescription_id: int) -> List[Dict]:
        """Get examination signs for a prescription"""
        query = """
        SELECT 
            s.id,
            sl.name AS sign_name,
            loc.name AS location,
            i.name AS intensity
        FROM sign_list_line s
        LEFT JOIN sign_list sl ON s.name = sl.id
        LEFT JOIN location_location loc ON s.location = loc.id
        LEFT JOIN intensity_intensity i ON s.intensity = i.id
        WHERE s.sign_res_id = :prescription_id
        """
        try:
            result = await conn.execute(text(query), {'prescription_id': prescription_id})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract signs: {e}")
            return []
            
    async def _get_past_medical_history(self, conn, prescription_id: int) -> List[Dict]:
        """Get past medical history for a prescription"""
        query = """
        SELECT 
            p.id,
            sc.name AS symptom_name,
            rc.name AS result_name
        FROM past_medical_history p
        LEFT JOIN symptom_config sc ON p.symptom_id = sc.id
        LEFT JOIN result_config rc ON p.result_id = rc.id
        WHERE p.prescription_id = :prescription_id
        """
        try:
            result = await conn.execute(text(query), {'prescription_id': prescription_id})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract past medical history: {e}")
            return []
            
    async def _get_medication_history(self, conn, prescription_id: int) -> List[Dict]:
        """Get medication history for a prescription"""
        query = """
        SELECT 
            m.id,
            prod.name AS medicine_name,
            mg.name AS medicine_group
        FROM medication_history m
        LEFT JOIN product_product pp ON m.medicine_id = pp.id
        LEFT JOIN product_template prod ON pp.product_tmpl_id = prod.id
        LEFT JOIN medicine_group mg ON m.medicine_group_id = mg.id
        WHERE m.prescription_id = :prescription_id
        """
        try:
            result = await conn.execute(text(query), {'prescription_id': prescription_id})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract medication history: {e}")
            return []
            
    async def _get_family_history(self, conn, prescription_id: int) -> List[Dict]:
        """Get family history for a prescription"""
        query = """
        SELECT 
            f.id,
            fc.name AS history_name,
            fr.name AS result_name
        FROM family_history f
        LEFT JOIN family_history_config fc ON f.family_history_config_id = fc.id
        LEFT JOIN family_history_result fr ON f.family_history_result_id = fr.id
        WHERE f.prescription_id = :prescription_id
        """
        try:
            result = await conn.execute(text(query), {'prescription_id': prescription_id})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract family history: {e}")
            return []
            
    async def _get_social_history(self, conn, prescription_id: int) -> List[Dict]:
        """Get social history for a prescription"""
        query = """
        SELECT 
            s.id,
            sc.name AS history_name,
            sr.name AS result_name
        FROM social_history s
        LEFT JOIN social_history_config sc ON s.social_history_config_id = sc.id
        LEFT JOIN social_history_result sr ON s.social_history_result_id = sr.id
        WHERE s.prescription_id = :prescription_id
        """
        try:
            result = await conn.execute(text(query), {'prescription_id': prescription_id})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract social history: {e}")
            return []
            
    async def _get_exercises(self, conn, prescription_id: int) -> List[Dict]:
        """Get exercises for a prescription"""
        query = """
        SELECT 
            e.id,
            ex.name AS exercise_name,
            p.name AS part_location,
            e.move2 AS move,
            e.type_of_test2 AS repitition
        FROM excercise_ex_line e
        LEFT JOIN excercise_excercise ex ON e.name = ex.id
        LEFT JOIN part_location p ON e.part_location = p.id
        WHERE e.excer_res_id = :prescription_id
        """
        try:
            result = await conn.execute(text(query), {'prescription_id': prescription_id})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract exercises: {e}")
            return []
            
    async def _get_ortho(self, conn, prescription_id: int) -> List[Dict]:
        """Get ortho list for a prescription"""
        query = """
        SELECT 
            o.id,
            item.name AS item_name,
            o.side AS side,
            loc.name AS location
        FROM ortho_list_line o
        LEFT JOIN item_item item ON o.name = item.id
        LEFT JOIN location_location loc ON o.location = loc.id
        WHERE o.ortho_list_id = :prescription_id
        """
        try:
            result = await conn.execute(text(query), {'prescription_id': prescription_id})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract ortho: {e}")
            return []

    async def _get_physical_examinations(self, conn, prescription_id: int) -> List[Dict]:
        """Get physical examinations for a prescription (One2many records)"""
        return []
        # Table doesn't exist yet
        query = """
        SELECT 
            pe.id,
            pe.general,
            pe.heent,
            pe.cvs,
            pe.respiratory,
            pe.abdomen,
            pe.msk,
            pe.cns,
            pe.sequence
        FROM physical_examination_line pe
        WHERE pe.prescription_id = :prescription_id
        ORDER BY pe.sequence ASC
        """
        try:
            result = await conn.execute(text(query), {'prescription_id': prescription_id})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract physical examinations: {e}")
            return []

    async def _get_procedures(self, conn, prescription_id: int) -> List[Dict]:
        """Get surgical/medical procedures for a prescription"""
        return []
        # Relation table doesn't exist
        query = """
        SELECT 
            ph.id,
            pc.name AS procedure_name
        FROM procedure_history ph
        LEFT JOIN procedure_history_procedure_config_rel rel ON ph.id = rel.procedure_history_id
        LEFT JOIN procedure_config pc ON rel.procedure_config_id = pc.id
        WHERE ph.prescription_id = :prescription_id
        """
        try:
            result = await conn.execute(text(query), {'prescription_id': prescription_id})
            # This query might return duplicates if there are multiple configs per history record,
            # but usually for text generation, we just want the names anyway.
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract procedures: {e}")
            return []

    async def _get_gcs_scores(self, conn, prescription_id: int) -> List[Dict]:
        """Get Glasgow Coma Scale scores for a prescription"""
        return []
        query = """
        SELECT 
            gcs.id,
            gcs.total_score,
            m.name AS motor_response,
            m.score AS motor_score,
            v.name AS verbal_response,
            v.score AS verbal_score,
            e.name AS eye_response,
            e.score AS eye_score
        FROM gcs_score_line gcs
        LEFT JOIN gsc_motor_response m ON gcs.motor_response_id = m.id
        LEFT JOIN gsc_verbal_response v ON gcs.verbal_response_id = v.id
        LEFT JOIN gsc_eye_response e ON gcs.eye_response_id = e.id
        WHERE gcs.prescription_order_id = :prescription_id
        """
        try:
            result = await conn.execute(text(query), {'prescription_id': prescription_id})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract GCS scores: {e}")
            return []

    async def _get_bmi_records(self, conn, prescription_id: int) -> List[Dict]:
        """Get detailed BMI calculations for a prescription"""
        return []
        query = """
        SELECT 
            bmi.id,
            bmi.v_weight AS weight,
            w_uom.name AS weight_unit,
            bmi.v_height AS height,
            h_uom.name AS height_unit,
            bmi.v_bmi AS bmi_value,
            bmi.bmi_unit
        FROM vital_bmi_line bmi
        LEFT JOIN uom_uom w_uom ON bmi.weight_uom_id = w_uom.id
        LEFT JOIN uom_uom h_uom ON bmi.height_uom_id = h_uom.id
        WHERE bmi.prescription_id = :prescription_id
        """
        try:
            result = await conn.execute(text(query), {'prescription_id': prescription_id})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract BMI records: {e}")
            return []

    async def _get_old_history(self, conn, prescription_id: int) -> List[Dict]:
        """Get old patient history lines for a prescription"""
        query = """
        SELECT 
            h.id,
            hl.name AS history_name,
            pr.name AS period_name,
            hc.name AS category_name
        FROM history_list_line h
        LEFT JOIN history_list hl ON h.name = hl.id
        LEFT JOIN period_record pr ON h.history_period = pr.id
        LEFT JOIN history_category hc ON h.history_category_id = hc.id
        WHERE h.history_res_id = :prescription_id
        """
        try:
            result = await conn.execute(text(query), {'prescription_id': prescription_id})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract old history: {e}")
            return []

    async def _get_medical_history(self, conn, prescription_id: int) -> List[Dict]:
        """Get medical history lines for a prescription"""
        query = """
        SELECT 
            m.id,
            m.name AS history_text,
            m.date,
            m.medication,
            m.investigation
        FROM patient_history_line m
        WHERE m.pat_medical_his_id = :prescription_id
        """
        try:
            result = await conn.execute(text(query), {'prescription_id': prescription_id})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract medical history: {e}")
            return []

    async def _get_advice_notes(self, conn, notes_line_id: int) -> List[Dict]:
        """Get advice notes for a prescription"""
        query = """
        SELECT 
            n.id,
            n.name AS notes_text
        FROM note_note n
        WHERE n.id = :notes_line_id
        """
        try:
            result = await conn.execute(text(query), {'notes_line_id': notes_line_id})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not extract advice notes: {e}")
            return []

    
    async def get_last_indexed_date(self, model_name: str) -> Optional[datetime]:
        """Get the last indexed date for a model from etl_metadata"""
        query = """
        SELECT last_write_date 
        FROM etl_metadata 
        WHERE odoo_model = :model_name
        """
        async with self.vector_engine.connect() as conn:
            result = await conn.execute(text(query), {'model_name': model_name})
            row = result.fetchone()
            return row[0] if row and row[0] else None
    
    async def update_etl_metadata(
        self, 
        model_name: str, 
        last_write_date: datetime,
        total_records: int,
        total_chunks: int
    ):
        """Update ETL metadata after indexing"""
        query = """
        INSERT INTO etl_metadata (odoo_model, last_indexed_at, last_write_date, total_records, total_chunks)
        VALUES (:model_name, :indexed_at, :last_write_date, :total_records, :total_chunks)
        ON CONFLICT (odoo_model) 
        DO UPDATE SET 
            last_indexed_at = :indexed_at,
            last_write_date = :last_write_date,
            total_records = :total_records,
            total_chunks = :total_chunks
        """
        async with self.vector_engine.begin() as conn:
            await conn.execute(text(query), {
                'model_name': model_name,
                'indexed_at': datetime.now(),
                'last_write_date': last_write_date,
                'total_records': total_records,
                'total_chunks': total_chunks
            })

    async def get_existing_odoo_ids(self, odoo_model: str) -> set:
        """Fetch all unique odoo_res_id values currently in the vector DB for a given model"""
        query = "SELECT DISTINCT odoo_res_id FROM medical_rag_index WHERE odoo_model = :model_name"
        existing_ids = set()
        async with self.vector_engine.connect() as conn:
            result = await conn.execute(text(query), {'model_name': odoo_model})
            for row in result.fetchall():
                if row[0] is not None:
                    existing_ids.add(int(row[0]))
        return existing_ids

    async def mark_records_as_synced(self, odoo_model: str, record_ids: List[int]) -> int:
        """Mark records as synced in Odoo"""
        if not record_ids:
            return 0
            
        # Define table mapping for direct updates
        # e.g., 'wk.appointment' -> 'wk_appointment'
        # 'prescription.order.knk' -> 'prescription_order_knk'
        table_mapping = {
            'wk.appointment': 'wk_appointment',
            'prescription.order.knk': 'prescription_order_knk',
            'res.partner': 'res_partner',
            'medical.disease': 'medical_disease'
        }
        
        table_name = table_mapping.get(odoo_model)
        if not table_name:
            logger.error(f"Cannot mark synced: unknown table for model {odoo_model}")
            return 0
            
        # Update records where ID is in the list
        query = f"""
        UPDATE {table_name} 
        SET is_rag_synced = True 
        WHERE id = ANY(:record_ids)
        """
        
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text(query), {'record_ids': record_ids})
                updated_count = result.rowcount
                logger.info(f"Marked {updated_count} records as synced for {odoo_model}")
                return updated_count
        except Exception as e:
            logger.error(f"Failed to mark records as synced for {odoo_model}: {e}")
            return 0
