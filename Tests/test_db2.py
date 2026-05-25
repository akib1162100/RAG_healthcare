import asyncio
import asyncpg
import sys

QUERIES = [
    ("medications", "SELECT med.id, prod.name AS medication_name, med.quantity, med.days, med.qty_per_day, med.short_comment as special_instruction FROM prescription_order_line_knk_new med LEFT JOIN product_product pp ON med.product_id = pp.id LEFT JOIN product_template prod ON pp.product_tmpl_id = prod.id LIMIT 1"),
    ("diagnoses", "SELECT d.id, disease.code AS disease_code, disease.name AS disease_name, disease.long_name AS disease_long_name FROM diagnosis_diagnosis d LEFT JOIN medical_disease disease ON d.disease_id = disease.id LIMIT 1"),
    ("complaints", "SELECT c.id, cl.name AS complaint, pr.name AS period, loc.name AS location FROM complaint_record_line c LEFT JOIN complaint_list cl ON c.complaint_list_id = cl.id LEFT JOIN period_record pr ON c.period = pr.id LEFT JOIN location_location loc ON c.location_id = loc.id LIMIT 1"),
    ("investigations", "SELECT i.id, il.name AS investigation_name FROM investigation_list_line i LEFT JOIN investigation_list il ON i.investigation_list_id = il.id LIMIT 1"),
    ("vitals", "SELECT v.id, v.name AS weight, v.w_unit AS weight_unit, v.height, v.h_unit AS height_unit, v.blood_presure AS bp_systolic, v.slash_tag, v.blood_presure_2 AS bp_diastolic, v.blood_unit AS bp_unit, v.pulse, v.pulse_unit, v.respiratory_rate, v.rr_unit FROM vital_list_line v LIMIT 1"),
    ("signs", "SELECT s.id, s.name AS sign_name, loc.name AS location, i.name AS intensity FROM sign_list_line s LEFT JOIN location_location loc ON s.location = loc.id LEFT JOIN intensity_intensity i ON s.intensity = i.id LIMIT 1"),
    ("past_medical_history", "SELECT p.id, sc.name AS symptom_name, rc.name AS result_name FROM past_medical_history p LEFT JOIN symptom_config sc ON p.symptom_id = sc.id LEFT JOIN result_config rc ON p.result_id = rc.id LIMIT 1"),
    ("medication_history", "SELECT m.id, prod.name AS medicine_name, mg.name AS medicine_group FROM medication_history m LEFT JOIN product_product pp ON m.medicine_id = pp.id LEFT JOIN product_template prod ON pp.product_tmpl_id = prod.id LEFT JOIN medicine_group mg ON m.medicine_group_id = mg.id LIMIT 1"),
    ("family_history", "SELECT f.id, fc.name AS history_name, fr.name AS result_name FROM family_history f LEFT JOIN family_history_config fc ON f.family_history_config_id = fc.id LEFT JOIN family_history_result fr ON f.family_history_result_id = fr.id LIMIT 1"),
    ("social_history", "SELECT s.id, sc.name AS history_name, sr.name AS result_name FROM social_history s LEFT JOIN social_history_config sc ON s.social_history_config_id = sc.id LEFT JOIN social_history_result sr ON s.social_history_result_id = sr.id LIMIT 1"),
    ("exercises", "SELECT e.id, e.name AS exercise_name, p.name AS part_location, e.move2 AS move, e.type_of_test2 AS repitition FROM excercise_ex_line e LEFT JOIN part_location p ON e.part_location = p.id LIMIT 1"),
    ("ortho", "SELECT o.id, o.name AS item_name, o.side AS side, loc.name AS location FROM ortho_list_line o LEFT JOIN location_location loc ON o.location = loc.id LIMIT 1"),
    ("physical_examinations", "SELECT pe.id, pe.general, pe.heent, pe.cvs, pe.respiratory, pe.abdomen, pe.msk, pe.cns, pe.sequence FROM physical_examination_line pe LIMIT 1"),
    ("procedures", "SELECT ph.id, pc.name AS procedure_name FROM procedure_history ph LEFT JOIN procedure_history_procedure_config_rel rel ON ph.id = rel.procedure_history_id LEFT JOIN procedure_config pc ON rel.procedure_config_id = pc.id LIMIT 1"),
    ("gcs_scores", "SELECT gcs.id, gcs.total_score, m.name AS motor_response, m.score AS motor_score, v.name AS verbal_response, v.score AS verbal_score, e.name AS eye_response, e.score AS eye_score FROM gcs_score_line gcs LEFT JOIN gsc_motor_response m ON gcs.motor_response_id = m.id LEFT JOIN gsc_verbal_response v ON gcs.verbal_response_id = v.id LEFT JOIN gsc_eye_response e ON gcs.eye_response_id = e.id LIMIT 1"),
    ("bmi_records", "SELECT bmi.id, bmi.v_weight AS weight, w_uom.name AS weight_unit, bmi.v_height AS height, h_uom.name AS height_unit, bmi.v_bmi AS bmi_value, bmi.bmi_unit FROM vital_bmi_line bmi LEFT JOIN uom_uom w_uom ON bmi.weight_uom_id = w_uom.id LEFT JOIN uom_uom h_uom ON bmi.height_uom_id = h_uom.id LIMIT 1"),
    ("old_history", "SELECT h.id, hl.name AS history_name, pr.name AS period_name, hc.name AS category_name, h.progression, h.severity, h.associated_symptoms FROM history_list_line h LEFT JOIN history_list hl ON h.name = hl.id LEFT JOIN period_record pr ON h.history_period = pr.id LEFT JOIN history_category hc ON h.history_category_id = hc.id LIMIT 1"),
    ("medical_history", "SELECT m.id, m.name AS history_text, m.date, m.medication, m.investigation FROM patient_history_line m LIMIT 1"),
]

async def check():
    conn = await asyncpg.connect('postgresql://odoo16:odoo16@host.docker.internal:5432/clidram_16')
    for name, q in QUERIES:
        try:
            await conn.execute(q)
            print(f"OK: {name}")
        except Exception as e:
            print(f"ERROR: {name} - {str(e)}")
            # In an asyncpg transaction, doing execute that fails might require a new connection if not rollback. Wait we are autocommit here? Yes, asyncpg single execute is autocommit unless in trans.
    await conn.close()

asyncio.run(check())
