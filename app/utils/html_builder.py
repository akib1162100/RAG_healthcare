import datetime
import json
import re


class HTMLBuilder:
    """Clinical HTML builder — two renderers:
    1. build_10_section_html  : legacy /summary endpoint (old schema)
    2. build_rolling_summary_html : rolling Map-Reduce summary (HMS-exact schema)
    """

    @staticmethod
    def _v(val):
        cleaned = HTMLBuilder._clean_text(val)
        return cleaned if cleaned else "-"

    @staticmethod
    def _as_dict(val):
        return val if isinstance(val, dict) else {}

    @staticmethod
    def _as_list(val):
        if isinstance(val, list):
            return val
        if val in (None, "", "null"):
            return []
        return [val]

    @staticmethod
    def _as_list_of_dicts(val):
        return [item for item in HTMLBuilder._as_list(val) if isinstance(item, dict)]

    @staticmethod
    def _clean_text(val):
        if val in (None, "", "null", "None", False):
            return ""
        if isinstance(val, (list, tuple)) and len(val) >= 2 and isinstance(val[1], str):
            text = val[1]
        else:
            text = str(val)
        text = text.replace("\r", "\n").strip()
        tuple_match = re.match(r"^[\[(]?\s*\d+\s*,\s*['\"]([^'\"]+)['\"]\s*[\])]?$", text)
        if tuple_match:
            text = tuple_match.group(1).strip()
        text = re.sub(r"\b[a-zA-Z_][\w.]*\(\d+,?\)\s*-\s*", "", text)
        text = re.sub(r"\b[a-zA-Z_][\w.]*\(\d+,?\)", "", text)
        return text.strip()

    @staticmethod
    def _split_text_values(val):
        if isinstance(val, list):
            raw_values = val
        else:
            text = HTMLBuilder._clean_text(val)
            if not text:
                return []
            normalized = text.replace("|", "\n")
            raw_values = normalized.split("\n")

        seen = set()
        output = []
        for item in raw_values:
            text = HTMLBuilder._clean_text(item).strip(" -")
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            output.append(text)
        return output

    @staticmethod
    def _medication_label(item):
        if isinstance(item, dict):
            name = (
                HTMLBuilder._clean_text(item.get("medication_drug_name"))
                or HTMLBuilder._clean_text(item.get("medication_name"))
                or HTMLBuilder._clean_text(item.get("name"))
            )
            details = []
            for key in ("dose", "freq", "route", "food", "duration"):
                value = HTMLBuilder._clean_text(item.get(key))
                if value and value != "-":
                    details.append(value)
            if name and details:
                return f"{name} ({', '.join(details)})"
            return name or "-"
        return HTMLBuilder._v(item)

    @staticmethod
    def adapt_rolling_to_clinical_schema(data):
        B = HTMLBuilder
        data = B._as_dict(data)

        demo = B._as_dict(data.get("patient_demographics", {}))
        vitals = B._as_list_of_dicts(data.get("vitals_at_visit", []))
        complaints = B._as_dict(data.get("chief_complaints", {}))
        indicators = B._as_list_of_dicts(data.get("vitals_indicators", []))
        labs = B._as_list_of_dicts(data.get("lab_report_mandatory", []))
        meds = B._as_dict(data.get("medications_prescribed", {}))
        history = B._as_list_of_dicts(data.get("medical_history_findings", []))
        mapping = B._as_list_of_dicts(data.get("clinical_record_mapping", []))
        care = B._as_list_of_dicts(data.get("suspect_and_care_plan", []))
        follow = B._as_list_of_dicts(data.get("follow_up_monitoring_plan", []))

        diagnosis_parts = []
        diagnosis_parts.extend(B._split_text_values(complaints.get("clinical_impression")))
        diagnosis_parts.extend(B._split_text_values(meds.get("diagnosis")))
        diagnosis_parts.extend(B._split_text_values(demo.get("past_medical_history")))
        diagnoses = []
        for idx, text in enumerate(diagnosis_parts[:10], start=1):
            diagnoses.append({
                "diagnosis": text,
                "secondary_complication": "",
                "icd_10": "",
                "snomed": "",
                "type": "Primary" if idx == 1 else "Secondary",
                "specialty": "Medicine",
            })
        if not diagnoses:
            diagnoses = [{
                "diagnosis": "No diagnosis captured",
                "secondary_complication": "",
                "icd_10": "",
                "snomed": "",
                "type": "Noted",
                "specialty": "-",
            }]

        cardiology_red_flags = []
        routine_red_flags = []
        for item in indicators:
            symptom = B._clean_text(item.get("symptom_test"))
            finding = B._clean_text(item.get("finding_flag"))
            if not symptom and not finding:
                continue
            entry = symptom if not finding else f"{symptom} - {finding}"
            target = cardiology_red_flags if any(
                token in symptom.lower() for token in ("card", "heart", "chest", "bp", "pulse", "ecg")
            ) else routine_red_flags
            target.append(entry)
        alert_message = "MANDATORY: Active findings identified - clinical review advised" if (cardiology_red_flags or routine_red_flags) else "No red flags captured in current summary"

        current_meds = []
        for med in B._as_list_of_dicts(meds.get("current_medications", [])):
            current_meds.append({
                "medication_drug_name": med.get("medication_drug_name") or med.get("name") or "-",
                "dose": med.get("dose") or "Not specified",
                "freq": med.get("freq") or "As directed",
                "route": med.get("route") or "Oral",
                "food": med.get("food") or "As directed",
                "duration": med.get("duration") or "-",
                "qty": med.get("qty") or "-",
                "margin": med.get("margin") or "-",
            })
        if not current_meds:
            current_meds = [{
                "medication_drug_name": "No medications captured",
                "dose": "-",
                "freq": "-",
                "route": "-",
                "food": "-",
                "duration": "-",
                "qty": "-",
                "margin": "-",
            }]

        historical_meds = []
        for row in history:
            if B._clean_text(row.get("category")).lower().startswith("old"):
                historical_meds.append(row.get("description"))
        historical_meds = B._split_text_values(historical_meds)[:10]

        investigations = []
        for lab in labs:
            test_panel = B._clean_text(lab.get("investigation"))
            result = B._clean_text(lab.get("result"))
            investigations.append({
                "category": "Clinical",
                "test_panel": test_panel or "Investigation",
                "clinical_indication": result or lab.get("status") or "-",
            })
        if not investigations:
            investigations = [{
                "category": "Clinical",
                "test_panel": "No investigations captured",
                "clinical_indication": "-",
            }]

        first_dx = diagnoses[0].get("diagnosis", "-")
        first_next_action = B._clean_text(care[0].get("clinical_action")) if care else "-"
        decision_map = []
        for row in mapping:
            decision_map.append({
                "complaint": row.get("complaint") or "-",
                "time_course": " to ".join(filter(None, [B._clean_text(row.get("start_date")), B._clean_text(row.get("end_date"))])) or "-",
                "pattern": row.get("trend_note") or "-",
                "most_likely_dx": first_dx,
                "next_action": first_next_action,
            })
        if not decision_map:
            primary = B._as_list(complaints.get("primary_complaints", []))
            decision_map = [{
                "complaint": primary[0] if primary else "No complaint timeline captured",
                "time_course": "-",
                "pattern": "Noted",
                "most_likely_dx": first_dx,
                "next_action": first_next_action,
            }]

        lifestyle = []
        medication_instructions = []
        warning_signs = []
        secondary_complaints = B._as_list(complaints.get("secondary_background_complaints", []))
        for entry in secondary_complaints[:6]:
            lifestyle.append(entry)
        for row in care:
            action = B._clean_text(row.get("clinical_action"))
            consideration = B._clean_text(row.get("additional_considerations"))
            priority = B._clean_text(row.get("priority_level")).lower()
            if priority in ("high", "critical"):
                warning_signs.extend([action, consideration])
            else:
                medication_instructions.extend([action])
                lifestyle.extend([consideration])
        lifestyle = B._split_text_values(lifestyle)[:8] or ["Continue advised lifestyle and rehabilitation plan"]
        medication_instructions = B._split_text_values(medication_instructions)[:8] or ["Take medications exactly as prescribed"]
        warning_signs = B._split_text_values(warning_signs)[:8] or ["Return for urgent review if symptoms worsen"]

        next_visit = "-"
        monitoring_points = []
        investigation_names = []
        if follow:
            first_follow = follow[0]
            next_visit = B._clean_text(first_follow.get("scheduling_date")) or B._clean_text(first_follow.get("frequency")) or "-"
            for row in follow:
                investigation_names.append(row.get("test_name"))
                monitoring_points.append(row.get("monitoring_points"))
        follow_up_plan = {
            "next_visit": next_visit,
            "signature_status": "Awaiting review",
            "investigations": " | ".join(B._split_text_values(investigation_names)) or "-",
            "referral": " | ".join(B._split_text_values(monitoring_points)) or "-",
        }

        return {
            "allergy_alert": data.get("allergy_alert", ""),
            "patient_demographics": {
                "patient_name": demo.get("patient_name"),
                "date_of_birth_age": demo.get("date_of_birth_age"),
                "gender": demo.get("gender"),
                "contact": demo.get("contact"),
                "presenting_doctor": demo.get("presenting_doctor"),
                "hmo_hospital": demo.get("hmo_hospital"),
                "reg_no": demo.get("reg_no"),
                "past_medical_history": demo.get("past_medical_history"),
                "patient_id": demo.get("patient_id"),
            },
            "vitals_at_visit": vitals or [{
                "parameter": "Physical Board Result",
                "recorded_value": "-",
                "status": "Normal",
                "normal_range": "-",
            }],
            "chief_complaints": {
                "primary_complaints": B._as_list(complaints.get("primary_complaints", [])) or ["No chief complaint captured"],
                "secondary_background_complaints": B._as_list(complaints.get("secondary_background_complaints", [])),
            },
            "red_flag_indicators": {
                "alert_message": alert_message,
                "cardiology_red_flags": cardiology_red_flags or ["No cardiology red flags captured"],
                "routine_red_flags": routine_red_flags or ["No routine red flags captured"],
            },
            "diagnoses": diagnoses,
            "medications_prescribed": {
                "date": meds.get("prescription_date") or meds.get("date") or "-",
                "current_medications": current_meds,
                "other_historical_medications": historical_meds,
            },
            "investigations_ordered": investigations,
            "clinical_decision_mapping": decision_map,
            "advise_care_plan": {
                "lifestyle_diet": lifestyle,
                "medication_instructions": medication_instructions,
                "warning_signs_seek_care": warning_signs,
            },
            "follow_up_monitoring_plan": follow_up_plan,
        }

    @staticmethod
    def materialize_report_sections(data):
        """Build the full 10-section report schema from a rolling summary payload."""
        B = HTMLBuilder
        data = B._as_dict(data)
        derived = B.adapt_rolling_to_clinical_schema(data)
        stored = B._as_dict(data.get("report_sections", {}))

        if not stored:
            return derived

        merged = dict(derived)
        for key, value in stored.items():
            if value not in (None, "", [], {}):
                merged[key] = value
        return merged

    @staticmethod
    def enrich_summary_for_storage(data):
        """
        Persist report-style sections inside the rolling summary JSON so they are
        saved in DB and refreshed on every new iteration.
        """
        B = HTMLBuilder
        base = B._as_dict(data).copy()
        base["report_sections"] = B.materialize_report_sections(base)
        base["report_sections_version"] = 1
        return base

    @staticmethod
    def status_badge(status):
        colours = {
            "Improving": "#28a745", "Worsening": "#dc3545", "Stationary": "#fd7e14",
            "Resolved": "#28a745", "New": "#0d6efd",
            "Normal": "#28a745", "High": "#dc3545", "Low": "#fd7e14", "Critical": "#dc3545",
            "Primary": "#0d6efd", "Secondary": "#17a2b8", "Rule Out": "#ffc107",
            "Positive": "#dc3545", "Negative": "#28a745", "Noted": "#fd7e14", "Absent": "#6c757d",
            "High": "#dc3545", "Medium": "#fd7e14", "Low": "#28a745",
        }
        bg = colours.get(status, "#6c757d")
        return (f"<span style='background:{bg};color:#fff;padding:2px 8px;"
                f"border-radius:4px;font-size:11px;font-weight:600;white-space:nowrap'>"
                f"{status}</span>")

    @staticmethod
    def section_header(num, title, colour="#1a3c5e"):
        return (f"<tr><td colspan='10' style='background:{colour};color:#fff;"
                f"padding:7px 10px;font-weight:700;font-size:12px;"
                f"letter-spacing:.5px;border-bottom:2px solid #fff'>"
                f"{num}. {title.upper()}</td></tr>")

    @staticmethod
    def th(*cols, bg="#2c5f8a"):
        cells = "".join(
            f"<th style='background:{bg};color:#fff;padding:5px 8px;"
            f"font-size:11px;white-space:nowrap;text-align:left;"
            f"border:1px solid #1a3c5e'>{c}</th>"
            for c in cols
        )
        return f"<tr>{cells}</tr>"

    @staticmethod
    def td_row(cols, stripe=False, colspans=None):
        bg = "#f4f8fb" if stripe else "#fff"
        cells = []
        for i, c in enumerate(cols):
            cs = f" colspan='{colspans[i]}'" if colspans and i < len(colspans) and colspans[i] else ""
            val = HTMLBuilder._v(c)
            content = c if isinstance(c, str) and c.startswith("<") else val
            cells.append(
                f"<td{cs} style='padding:5px 8px;font-size:11px;"
                f"border:1px solid #dee2e6;background:{bg};vertical-align:top'>"
                f"{content}</td>"
            )
        return f"<tr>{''.join(cells)}</tr>"

    # ─── Legacy renderer (used by /summary endpoint) ──────────────────────────

    @staticmethod
    def build_10_section_html(data, patient_seq, patient_name, page_label_html=""):
        def _v(val):
            cleaned = HTMLBuilder._clean_text(val)
            return cleaned if cleaned else "-"

        def _dict(val):
            return val if isinstance(val, dict) else {}

        def _list(val):
            if isinstance(val, list):
                return val
            if val in (None, "", "null"):
                return []
            return [val]

        def _dict_list(val):
            return [item for item in _list(val) if isinstance(item, dict)]

        def status_badge(status):
            colours = {
                "Improving": "#28a745", "Worsening": "#dc3545", "Stationary": "#fd7e14",
                "Normal": "#28a745", "High": "#dc3545", "Low": "#fd7e14", "Critical": "#dc3545",
                "Primary": "#0d6efd", "Secondary": "#17a2b8", "Rule Out": "#ffc107",
                "Positive": "#dc3545", "Negative": "#28a745", "Noted": "#fd7e14", "Absent": "#6c757d"
            }
            bg = colours.get(status, "#6c757d")
            return f"<span style='background:{bg};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;white-space:nowrap'>{status}</span>"

        def section_header(num, title, colour="#1a3c5e"):
            return f"<tr><td colspan='10' style='background:{colour};color:#fff;padding:7px 10px;font-weight:700;font-size:12px;letter-spacing:.5px;border-bottom:2px solid #fff'>{num}. {title.upper()}</td></tr>"

        def th(*cols, bg="#2c5f8a"):
            cells = "".join(f"<th style='background:{bg};color:#fff;padding:5px 8px;font-size:11px;white-space:nowrap;text-align:left;border:1px solid #1a3c5e'>{c}</th>" for c in cols)
            return f"<tr>{cells}</tr>"

        def td_row(*cols, stripe=False, colspans=None):
            bg = "#f4f8fb" if stripe else "#fff"
            cells = []
            for i, c in enumerate(cols):
                cs = f" colspan='{colspans[i]}'" if colspans and i < len(colspans) and colspans[i] else ""
                cells.append(f"<td{cs} style='padding:5px 8px;font-size:11px;border:1px solid #dee2e6;background:{bg};vertical-align:top'>{_v(c) if not isinstance(c, str) or not c.startswith('<') else c}</td>")
            return f"<tr>{''.join(cells)}</tr>"

        TS = "width:100%;border-collapse:collapse;margin-bottom:15px;font-family:Arial,sans-serif"
        data = _dict(data)
        h = []

        if page_label_html:
            h.append(page_label_html)
        else:
            h.append(
                f"<div style='background:#1a3c5e;color:#fff;padding:10px 14px;font-family:Arial,sans-serif;border-radius:4px 4px 0 0;margin-bottom:15px'>"
                f"<table width='100%'><tr>"
                f"<td><span style='font-size:17px;font-weight:700;letter-spacing:.5px'>MEDICAL SUMMARY</span></td>"
                f"<td style='text-align:right;font-size:11px;opacity:.9'>"
                f"<b>Patient:</b> {patient_name} &nbsp;|&nbsp; <b>ID:</b> {patient_seq} &nbsp;|&nbsp; "
                f"<b>Generated:</b> " + datetime.datetime.now().strftime("%d %b %Y %H:%M") +
                f"</td></tr></table></div>"
            )

        allergy = data.get("allergy_alert")
        if allergy and str(allergy).upper() not in ("-", "NULL", ""):
            h.append(f"<div style='background:#f8d7da;color:#721c24;padding:8px 14px;border:1px solid #f5c6cb;border-radius:4px;margin-bottom:15px;font-size:13px;font-weight:bold;font-family:Arial,sans-serif'>ALLERGY ALERT: {allergy}</div>")

        demo = _dict(data.get("patient_demographics", {}))
        h.append(f"<table style='{TS}'><tbody>")
        h.append(section_header(1, "Patient Demographics"))
        h.append(th("Field", "Details", "Field", "Details"))
        h.append(td_row("Patient Name", demo.get("patient_name") or patient_name, "Patient ID", demo.get("patient_id") or patient_seq))
        h.append(td_row("Date of Birth / Age", demo.get("date_of_birth_age"), "Gender", demo.get("gender"), stripe=True))
        h.append(td_row("Contact", demo.get("contact"), "HMO / Hospital", demo.get("hmo_hospital")))
        h.append(td_row("Presenting Doctor", demo.get("presenting_doctor"), "Reg. No.", demo.get("reg_no"), stripe=True))
        h.append(td_row("Past Medical History", demo.get("past_medical_history") or "No prior history captured for this prescription", "", "", colspans=[1, 3]))
        h.append("</tbody></table>")

        vitals = _dict_list(data.get("vitals_at_visit", []))
        if not vitals:
            vitals = [{"parameter": "Physical Board Result", "recorded_value": "-", "status": "Noted", "normal_range": "-"}]
        h.append(f"<table style='{TS}'><tbody>")
        h.append(section_header(2, "Vitals At Visit", colour="#2e7d32"))
        h.append(th("Parameter", "Recorded Value", "Status", "Normal Range", bg="#388e3c"))
        for i, v in enumerate(vitals):
            row_bg = "#f8d7da" if v.get("status") == "Critical" else ("#f4f8fb" if i % 2 == 1 else "#fff")
            val = f"<b>{v.get('recorded_value')}</b>" if v.get("status") in ("High", "Low", "Critical") else _v(v.get("recorded_value"))
            h.append(f"<tr style='background:{row_bg}'>"
                     f"<td style='padding:5px 8px;font-size:11px;border:1px solid #dee2e6'>{_v(v.get('parameter'))}</td>"
                     f"<td style='padding:5px 8px;font-size:11px;border:1px solid #dee2e6;color:{'#dc3545' if v.get('status') in ('High','Critical') else '#000'}'>{val}</td>"
                     f"<td style='padding:5px 8px;font-size:11px;border:1px solid #dee2e6'>{status_badge(v.get('status', ''))}</td>"
                     f"<td style='padding:5px 8px;font-size:11px;border:1px solid #dee2e6'>{_v(v.get('normal_range'))}</td></tr>")
        h.append("</tbody></table>")

        cc = _dict(data.get("chief_complaints", {}))
        prim = _list(cc.get("primary_complaints", [])) or ["No chief complaint captured for this prescription"]
        sec = _list(cc.get("secondary_background_complaints", [])) or ["No secondary/background complaint recorded"]
        h.append(f"<table style='{TS};border:1px solid #dee2e6'><tbody>")
        h.append(section_header(3, "Chief Complaints", colour="#0277bd"))
        h.append("<tr><td style='padding:8px 14px;background:#f9fafb;font-size:11px'>")
        h.append("<b style='color:#0277bd'>Primary Complaints:</b><ul style='margin:4px 0 10px 0;padding-left:20px'>")
        for p in prim:
            h.append(f"<li>{_v(p)}</li>")
        h.append("</ul>")
        h.append("<b style='color:#0277bd'>Secondary / Background Complaints:</b><ul style='margin:4px 0 4px 0;padding-left:20px'>")
        for s in sec:
            h.append(f"<li>{_v(s)}</li>")
        h.append("</ul>")
        h.append("</td></tr></tbody></table>")

        rfi = _dict(data.get("red_flag_indicators", {}))
        h.append(f"<table style='{TS}'><tbody>")
        h.append(section_header(4, "Red Flag Indicators", colour="#c62828"))
        alert = rfi.get("alert_message")
        if alert and alert.upper() not in ("-", "NULL", ""):
            h.append(f"<tr><td colspan='2' style='background:#f8d7da;color:#721c24;padding:6px 10px;font-size:12px;font-weight:bold;text-align:center;border:1px solid #f5c6cb'>{alert}</td></tr>")
        h.append(th("Cardiology Red Flags", "Routine Red Flags", bg="#c62828"))
        cardio = rfi.get("cardiology_red_flags", [])
        routine = rfi.get("routine_red_flags", [])
        if not isinstance(cardio, list):
            cardio = []
        if not isinstance(routine, list):
            routine = []
        if not cardio:
            cardio = ["No cardiology red flag noted from this prescription"]
        if not routine:
            routine = ["No routine red flag noted from this prescription"]
        max_len = max(len(cardio), len(routine), 1)
        for i in range(max_len):
            c_val = f"<li>{cardio[i]}</li>" if i < len(cardio) and cardio[i] else ""
            r_val = f"<li>{routine[i]}</li>" if i < len(routine) and routine[i] else ""
            c_html = f"<ul style='margin:0;padding-left:15px'>{c_val}</ul>" if c_val else "-"
            r_html = f"<ul style='margin:0;padding-left:15px'>{r_val}</ul>" if r_val else "-"
            h.append(td_row(c_html, r_html, stripe=i % 2 == 1))
        h.append("</tbody></table>")

        diag = _dict_list(data.get("diagnoses", []))
        if not diag:
            diag = [{"diagnosis": "No diagnosis explicitly recorded for this prescription", "secondary_complication": "", "icd_10": "", "snomed": "", "type": "Noted", "specialty": "General"}]
        h.append(f"<table style='{TS}'><tbody>")
        h.append(section_header(5, "Diagnoses", colour="#00838f"))
        h.append(th("Sl.", "Diagnosis", "Secondary Complication", "ICD-10", "SNOMED", "Type", "Specialty", bg="#00ACC1"))
        for i, d in enumerate(diag):
            type_b = status_badge(d.get("type", "")) if d.get("type") else "-"
            h.append(td_row(str(i+1), d.get("diagnosis"), d.get("secondary_complication"), d.get("icd_10"), d.get("snomed"), type_b, d.get("specialty"), stripe=i % 2 == 1))
        h.append("</tbody></table>")

        meds_obj = _dict(data.get("medications_prescribed", {}))
        curr = _dict_list(meds_obj.get("current_medications", []))
        hist = _list(meds_obj.get("other_historical_medications", []))
        if not curr:
            curr = [{"medication_drug_name": "No medication explicitly captured", "dose": "-", "freq": "-", "route": "-", "food": "-", "duration": "-", "qty": "-", "margin": "-"}]
        h.append(f"<table style='{TS}'><tbody>")
        h.append(section_header(6, "Medications Prescribed", colour="#4a148c"))
        rx_d = meds_obj.get("date")
        if rx_d and rx_d.upper() not in ("-", "NULL", ""):
            h.append(f"<tr><td colspan='9' style='background:#f3e5f5;padding:5px 10px;font-size:11px;font-weight:600;color:#4a148c'>Recent Prescription Date: {rx_d}</td></tr>")
        h.append(th("Sl.", "Medication (Drug Name)", "Dose", "Freq", "Route", "Food", "Duration", "Qty", "Margin", bg="#6a1b9a"))
        for i, c in enumerate(curr):
            h.append(td_row(str(i+1), f"<b>{_v(c.get('medication_drug_name'))}</b>", c.get("dose"), c.get("freq"), c.get("route"), c.get("food"), c.get("duration"), c.get("qty"), c.get("margin"), stripe=i % 2 == 1))
        if hist:
            h.append(f"<tr><td colspan='9' style='background:#f9fafb;padding:8px 10px;font-size:11px'>")
            h.append("<b style='color:#4a148c'>Other / Historical Medications:</b><ul style='margin:4px 0 0 0;padding-left:20px'>")
            for hs in hist:
                h.append(f"<li>{HTMLBuilder._medication_label(hs)}</li>")
            h.append("</ul></td></tr>")
        h.append("</tbody></table>")

        inv = _dict_list(data.get("investigations_ordered", []))
        if not inv:
            inv = [{"category": "Clinical", "test_panel": "No investigation explicitly recorded", "clinical_indication": "No investigation/order note found in this prescription"}]
        h.append(f"<table style='{TS}'><tbody>")
        h.append(section_header(7, "Investigations Ordered", colour="#1565c0"))
        h.append(th("Sl.", "Category", "Test / Panel", "Clinical Indication", bg="#1976D2"))
        for i, v in enumerate(inv):
            h.append(td_row(str(i+1), v.get("category"), v.get("test_panel"), v.get("clinical_indication"), stripe=i % 2 == 1))
        h.append("</tbody></table>")

        cdm = _dict_list(data.get("clinical_decision_mapping", []))
        if not cdm:
            cdm = [{"complaint": "Prescription review", "time_course": "-", "pattern": "Noted", "most_likely_dx": "-", "next_action": "Clinical review as needed"}]
        h.append(f"<table style='{TS}'><tbody>")
        h.append(section_header(8, "Clinical Decision Mapping", colour="#2e4053"))
        h.append(th("Complaint", "Time Course", "Pattern", "Most Likely Dx", "Next Action", bg="#34495e"))
        for i, c in enumerate(cdm):
            h.append(td_row(c.get("complaint"), c.get("time_course"), c.get("pattern"), c.get("most_likely_dx"), c.get("next_action"), stripe=i % 2 == 1))
        h.append("</tbody></table>")

        acp = _dict(data.get("advise_care_plan", {}))
        h.append(f"<table style='{TS}'><tbody>")
        h.append(section_header(9, "Advise & Care Plan", colour="#ef6c00"))
        h.append(th("Lifestyle & Diet", "Medication Instructions", "Warning Signs - Seek Care", bg="#fb8c00"))
        life = _list(acp.get("lifestyle_diet", [])) or ["No lifestyle or diet note recorded"]
        med_inst = _list(acp.get("medication_instructions", [])) or ["Follow the prescribed medication plan"]
        warn = _list(acp.get("warning_signs_seek_care", [])) or ["Seek care if symptoms worsen or new symptoms appear"]
        l_html = "<ul style='margin:0;padding-left:15px'>" + "".join(f"<li>{_v(x)}</li>" for x in life) + "</ul>"
        m_html = "<ul style='margin:0;padding-left:15px'>" + "".join(f"<li>{_v(x)}</li>" for x in med_inst) + "</ul>"
        w_html = "<ul style='margin:0;padding-left:15px;color:#dc3545'>" + "".join(f"<li>{_v(x)}</li>" for x in warn) + "</ul>"
        h.append(td_row(l_html, m_html, w_html))
        h.append("</tbody></table>")

        fum = _dict(data.get("follow_up_monitoring_plan", {}))
        h.append(f"<table style='{TS}'><tbody>")
        h.append(section_header(10, "Follow-Up & Monitoring Plan", colour="#0277bd"))
        h.append(th("Next Visit", "Signature Status", "Investigations", "Referral", bg="#0288D1"))
        h.append(td_row(
            fum.get("next_visit") or "Review as advised",
            fum.get("signature_status") or "Awaiting review",
            fum.get("investigations") or "No follow-up investigation specified",
            fum.get("referral") or "No referral specified",
        ))
        h.append("</tbody></table>")

        if not any([demo, vitals, cc, rfi, diag, meds_obj, inv, cdm, acp, fum]):
            h.append(f"<pre style='font-size:12px;padding:10px'>{json.dumps(data, indent=2)}</pre>")

        return "".join(h)

    @staticmethod
    def render_clinical_doc(data, patient_seq, patient_name, page_num=1, total_pages=1):
        page_label = f"Prescription {page_num} of {total_pages}"
        data = HTMLBuilder._as_dict(data)
        lp = HTMLBuilder._as_dict(data.get("medications_prescribed", {}))
        rx_date = lp.get("date", "") if isinstance(lp, dict) else ""
        if rx_date:
            page_label += f" &nbsp;|&nbsp; Date: {rx_date}"
        header_html = (
            f"<div style='background:#1a3c5e;color:#fff;padding:10px 14px;margin-bottom:10px;"
            f"font-family:Arial,sans-serif;border-radius:4px'>"
            f"<table width='100%'><tr>"
            f"<td style='font-size:15px;font-weight:700'>PRESCRIPTION DETAIL</td>"
            f"<td style='text-align:right;font-size:11px'>{page_label}</td>"
            f"</tr></table></div>"
        )
        return HTMLBuilder.build_10_section_html(data, patient_seq, patient_name, header_html)

    # ─── Rolling Summary renderer — HMS reference format (10 sections) ────────

    @staticmethod
    def build_rolling_summary_html(data: dict, patient_seq: str, patient_name: str) -> str:
        """
        Renders the 10-section clinical HTML matching the HMS reference design exactly.

        REDUCE schema (field names are FIXED — must match LLM output exactly):
          allergy_alert
          patient_demographics: {patient_name, date_of_birth_age, gender, contact,
                                  presenting_doctor, hmo_hospital, reg_no,
                                  past_medical_history, patient_id}
          vitals_at_visit:       [{parameter, recorded_value, status, normal_range}]
          chief_complaints:      {primary_complaints[], secondary_background_complaints[],
                                  clinical_impression}
          vitals_indicators:     [{symptom_test, finding_flag}]
          lab_report_mandatory:  [{investigation, result, normal_range, unit, status}]
          medications_prescribed:{prescription_date, physician, diagnosis,
                                  current_medications: [{medication_drug_name, dose, freq,
                                  route, food, duration, qty, amount, margin}]}
          medical_history_findings: [{category, past_plant, description}]
          clinical_record_mapping:  [{complaint, trend_note, start_date, end_date}]
          suspect_and_care_plan:    [{clinical_action, additional_considerations,
                                     priority_level, next_time}]
          follow_up_monitoring_plan:[{test_name, frequency, monitoring_points, scheduling_date}]
        """
        clinical_data = HTMLBuilder.materialize_report_sections(data)
        return HTMLBuilder.build_10_section_html(clinical_data, patient_seq, patient_name)
        import datetime as _dt
        TS = "width:100%;border-collapse:collapse;margin-bottom:15px;font-family:Arial,sans-serif"
        B = HTMLBuilder
        data = B._as_dict(data)
        h = []

        # ── Header ──────────────────────────────────────────────────────────
        h.append(
            f"<div style='background:#1a3c5e;color:#fff;padding:10px 14px;"
            f"font-family:Arial,sans-serif;border-radius:4px 4px 0 0;margin-bottom:15px'>"
            f"<table width='100%'><tr>"
            f"<td><span style='font-size:17px;font-weight:700;letter-spacing:.5px'>"
            f"MEDICAL SUMMARY</span></td>"
            f"<td style='text-align:right;font-size:11px;opacity:.9'>"
            f"<b>Patient:</b> {patient_name} &nbsp;|&nbsp; <b>ID:</b> {patient_seq}"
            f" &nbsp;|&nbsp; <b>Generated:</b> {_dt.datetime.now().strftime('%d %b %Y %H:%M')}"
            f"</td></tr></table></div>"
        )

        # ── Allergy Alert ────────────────────────────────────────────────────
        allergy = data.get("allergy_alert", "")
        if allergy and str(allergy).upper() not in ("-", "NULL", "NONE", ""):
            h.append(
                f"<div style='background:#f8d7da;color:#721c24;padding:8px 14px;"
                f"border:1px solid #f5c6cb;border-radius:4px;margin-bottom:15px;"
                f"font-size:13px;font-weight:bold;font-family:Arial,sans-serif'>"
                f"&#9888; ALLERGY ALERT: {allergy}</div>"
            )

        # ── 1. Patient Demographics ──────────────────────────────────────────
        demo = B._as_dict(data.get("patient_demographics", {}))
        if demo:
            h.append(f"<table style='{TS}'><tbody>")
            h.append(B.section_header(1, "Patient Demographics"))
            h.append(B.th("Field", "Details", "Field", "Details"))
            h.append(B.td_row([
                "Patient Name", demo.get("patient_name") or patient_name,
                "Patient ID",   demo.get("patient_id") or demo.get("reg_no") or patient_seq,
            ]))
            h.append(B.td_row([
                "Date of Birth / Age", demo.get("date_of_birth_age"),
                "Gender",              demo.get("gender"),
            ], stripe=True))
            h.append(B.td_row([
                "Contact",        demo.get("contact"),
                "HMO / Hospital", demo.get("hmo_hospital"),
            ]))
            h.append(B.td_row([
                "Presenting Doctor", demo.get("presenting_doctor"),
                "Reg. No.",          demo.get("reg_no"),
            ], stripe=True))
            pmh = demo.get("past_medical_history", "")
            if pmh:
                h.append(B.td_row(["Past Medical History", pmh, "", ""], colspans=[1, 3]))
            h.append("</tbody></table>")

        # ── 2. Vitals At Visit ───────────────────────────────────────────────
        vitals = B._as_list_of_dicts(data.get("vitals_at_visit", []))
        h.append(f"<table style='{TS}'><tbody>")
        h.append(B.section_header(2, "Vitals At Visit", colour="#2e7d32"))
        h.append(B.th("Parameter", "Recorded Value", "Status", "Normal Range", bg="#388e3c"))
        if vitals:
            for i, v in enumerate(vitals):
                st = v.get("status", "")
                row_bg = "#f8d7da" if st == "Critical" else ("#f4f8fb" if i % 2 else "#fff")
                rv = v.get("recorded_value", "")
                val_html = (f"<b style='color:#dc3545'>{B._v(rv)}</b>"
                            if st in ("High", "Low", "Critical") else B._v(rv))
                h.append(
                    f"<tr style='background:{row_bg}'>"
                    f"<td style='padding:5px 8px;font-size:11px;border:1px solid #dee2e6'>{B._v(v.get('parameter'))}</td>"
                    f"<td style='padding:5px 8px;font-size:11px;border:1px solid #dee2e6'>{val_html}</td>"
                    f"<td style='padding:5px 8px;font-size:11px;border:1px solid #dee2e6'>{B.status_badge(st) if st else '-'}</td>"
                    f"<td style='padding:5px 8px;font-size:11px;border:1px solid #dee2e6'>{B._v(v.get('normal_range'))}</td></tr>"
                )
        else:
            h.append(B.td_row(["No vitals captured in indexed records"], colspans=[4]))
        h.append("</tbody></table>")

        # ── 3. Chief Complaints ──────────────────────────────────────────────
        cc = B._as_dict(data.get("chief_complaints", {}))
        prim = B._as_list(cc.get("primary_complaints", []))
        sec  = B._as_list(cc.get("secondary_background_complaints", []))
        imp  = cc.get("clinical_impression", "")
        h.append(f"<table style='{TS};border:1px solid #dee2e6'><tbody>")
        h.append(B.section_header(3, "Chief Complaints", colour="#0277bd"))
        h.append("<tr><td style='padding:8px 14px;background:#f9fafb;font-size:11px'>")
        if prim:
            h.append("<b style='color:#0277bd'>Primary Complaints:</b>"
                     "<ul style='margin:4px 0 10px 0;padding-left:20px'>")
            for p in prim: h.append(f"<li>{B._v(p)}</li>")
            h.append("</ul>")
        if sec:
            h.append("<b style='color:#0277bd'>Secondary / Background Complaints:</b>"
                     "<ul style='margin:4px 0 10px 0;padding-left:20px'>")
            for s in sec: h.append(f"<li>{B._v(s)}</li>")
            h.append("</ul>")
        if imp:
            h.append(f"<b style='color:#0277bd'>Clinical Impression:</b> {B._v(imp)}")
        if not any([prim, sec, imp]):
            h.append("No complaints captured in indexed records.")
        h.append("</td></tr></tbody></table>")

        # ── 4. Vitals Indicators ─────────────────────────────────────────────
        vi = B._as_list_of_dicts(data.get("vitals_indicators", []))
        h.append(f"<table style='{TS}'><tbody>")
        h.append(B.section_header(4, "Vitals Indicators", colour="#00838f"))
        h.append(B.th("Symptom / Test", "Finding / Flag", bg="#00ACC1"))
        if vi:
            for i, v in enumerate(vi):
                flag = v.get("finding_flag", "")
                h.append(B.td_row(
                    [v.get("symptom_test"), B.status_badge(flag) if flag else "-"],
                    stripe=i % 2 == 1,
                ))
        else:
            h.append(B.td_row(["No clinical indicators captured"], colspans=[2]))
        h.append("</tbody></table>")

        # ── 5. Lab Report (Mandatory) ────────────────────────────────────────
        labs = B._as_list_of_dicts(data.get("lab_report_mandatory", []))
        h.append(f"<table style='{TS}'><tbody>")
        h.append(B.section_header(5, "Lab Report (Mandatory)", colour="#1565c0"))
        h.append(B.th("Investigation", "Result", "Normal Range", "Unit", "Status", bg="#1976D2"))
        if labs:
            for i, lab in enumerate(labs):
                st = lab.get("status", "")
                row_bg = "#f8d7da" if st in ("Critical", "High") else ("#f4f8fb" if i % 2 else "#fff")
                bold = "font-weight:700;" if st in ("Critical", "High", "Low") else ""
                h.append(
                    f"<tr style='background:{row_bg}'>"
                    f"<td style='padding:5px 8px;font-size:11px;border:1px solid #dee2e6'>{B._v(lab.get('investigation'))}</td>"
                    f"<td style='padding:5px 8px;font-size:11px;border:1px solid #dee2e6;{bold}'>{B._v(lab.get('result'))}</td>"
                    f"<td style='padding:5px 8px;font-size:11px;border:1px solid #dee2e6'>{B._v(lab.get('normal_range'))}</td>"
                    f"<td style='padding:5px 8px;font-size:11px;border:1px solid #dee2e6'>{B._v(lab.get('unit'))}</td>"
                    f"<td style='padding:5px 8px;font-size:11px;border:1px solid #dee2e6'>{B.status_badge(st) if st else '-'}</td></tr>"
                )
        else:
            h.append(B.td_row(["No investigation results captured"], colspans=[5]))
        h.append("</tbody></table>")

        # ── 6. Medications Prescribed ────────────────────────────────────────
        mp = B._as_dict(data.get("medications_prescribed", {}))
        curr = B._as_list_of_dicts(mp.get("current_medications", []))
        h.append(f"<table style='{TS}'><tbody>")
        h.append(B.section_header(6, "Medications Prescribed", colour="#4a148c"))
        meta_parts = []
        rx_date   = mp.get("prescription_date", "")
        physician  = mp.get("physician", "")
        diagnosis  = mp.get("diagnosis", "")
        if rx_date:   meta_parts.append(f"<b>Prescription Date:</b> {rx_date}")
        if physician: meta_parts.append(f"<b>Physician:</b> {physician}")
        if diagnosis: meta_parts.append(f"<b>Diagnosis:</b> {diagnosis}")
        if meta_parts:
            h.append(
                f"<tr><td colspan='10' style='background:#f3e5f5;padding:5px 10px;"
                f"font-size:11px;font-weight:600;color:#4a148c'>"
                + " &nbsp;|&nbsp; ".join(meta_parts) + "</td></tr>"
            )
        h.append(B.th(
            "Sl.", "Medication (Drug Name)", "Dose", "Freq", "Route",
            "Food", "Duration", "Qty", "Amount", "Margin", bg="#6a1b9a",
        ))
        if curr:
            for i, m in enumerate(curr):
                h.append(B.td_row([
                    str(i + 1),
                    f"<b>{B._v(m.get('medication_drug_name'))}</b>",
                    m.get("dose"),     m.get("freq"),
                    m.get("route"),    m.get("food"),
                    m.get("duration"), m.get("qty"),
                    m.get("amount"),   m.get("margin"),
                ], stripe=i % 2 == 1))
        else:
            h.append(B.td_row(["", "No medications captured", "", "", "", "", "", "", "", ""], colspans=[1, 9]))
        h.append("</tbody></table>")

        # ── 7. Medical History Findings ──────────────────────────────────────
        mhf = B._as_list_of_dicts(data.get("medical_history_findings", []))
        h.append(f"<table style='{TS}'><tbody>")
        h.append(B.section_header(7, "Medical History Findings", colour="#6a1b9a"))
        h.append(B.th("Category", "Past / Plan", "Description", bg="#8e24aa"))
        if mhf:
            for i, m in enumerate(mhf):
                h.append(B.td_row(
                    [m.get("category"), m.get("past_plant"), m.get("description")],
                    stripe=i % 2 == 1,
                ))
        else:
            h.append(B.td_row(["No medical history captured"], colspans=[3]))
        h.append("</tbody></table>")

        # ── 8. Clinical Record Mapping ───────────────────────────────────────
        crm = B._as_list_of_dicts(data.get("clinical_record_mapping", []))
        h.append(f"<table style='{TS}'><tbody>")
        h.append(B.section_header(8, "Clinical Record Mapping", colour="#2e4053"))
        h.append(B.th("Complaint", "Trend Note", "Start Date", "End Date", bg="#34495e"))
        if crm:
            for i, c in enumerate(crm):
                trend = c.get("trend_note", "")
                h.append(B.td_row([
                    c.get("complaint"),
                    B.status_badge(trend) if trend else "-",
                    c.get("start_date"), c.get("end_date"),
                ], stripe=i % 2 == 1))
        else:
            h.append(B.td_row(["No complaint timeline captured"], colspans=[4]))
        h.append("</tbody></table>")

        # ── 9. Suspect & Care Plan ───────────────────────────────────────────
        scp = B._as_list_of_dicts(data.get("suspect_and_care_plan", []))
        h.append(f"<table style='{TS}'><tbody>")
        h.append(B.section_header(9, "Suspect & Care Plan", colour="#ef6c00"))
        h.append(B.th("Clinical Action", "Additional Considerations",
                      "Priority Level", "Next Time", bg="#fb8c00"))
        if scp:
            for i, s in enumerate(scp):
                priority = s.get("priority_level", "")
                h.append(B.td_row([
                    s.get("clinical_action"),
                    s.get("additional_considerations"),
                    B.status_badge(priority) if priority else "-",
                    s.get("next_time"),
                ], stripe=i % 2 == 1))
        else:
            h.append(B.td_row(["No care plan captured"], colspans=[4]))
        h.append("</tbody></table>")

        # ── 10. Follow-Up & Monitoring Plan ─────────────────────────────────
        fum = B._as_list_of_dicts(data.get("follow_up_monitoring_plan", []))
        h.append(f"<table style='{TS}'><tbody>")
        h.append(B.section_header(10, "Follow-Up & Monitoring Plan", colour="#0277bd"))
        h.append(B.th("Test / Monitoring", "Frequency",
                      "Monitoring Points", "Scheduled Date", bg="#0288D1"))
        if fum:
            for i, f_ in enumerate(fum):
                h.append(B.td_row([
                    f_.get("test_name"),          f_.get("frequency"),
                    f_.get("monitoring_points"),   f_.get("scheduling_date"),
                ], stripe=i % 2 == 1))
        else:
            h.append(B.td_row(["No follow-up items captured"], colspans=[4]))
        h.append("</tbody></table>")

        # Fallback — raw JSON if all sections empty
        if not any([demo, vitals, cc, vi, labs, mp, mhf, crm, scp, fum]):
            h.append(f"<pre style='font-size:12px;padding:10px;background:#f8f9fa'>"
                     f"{json.dumps(data, indent=2)}</pre>")

        return "".join(h)
