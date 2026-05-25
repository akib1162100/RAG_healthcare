import datetime as dt
import re
from typing import Any, Dict, List, Optional


ROLLING_SUMMARY_KEYS = (
    "allergy_alert",
    "patient_demographics",
    "vitals_at_visit",
    "chief_complaints",
    "vitals_indicators",
    "lab_report_mandatory",
    "medications_prescribed",
    "medical_history_findings",
    "clinical_record_mapping",
    "suspect_and_care_plan",
    "follow_up_monitoring_plan",
)


def _is_blank(value: Any) -> bool:
    if value is None or value is False:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"", "-", "null", "none", "false", "n/a"}
    if isinstance(value, (int, float)):
        return value == 0
    if isinstance(value, dict):
        return not value or all(_is_blank(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return not value or all(_is_blank(v) for v in value)
    return False


def has_meaningful_rolling_summary(summary: Any) -> bool:
    if not isinstance(summary, dict):
        return False
    return any(not _is_blank(summary.get(key)) for key in ROLLING_SUMMARY_KEYS)


def _safe_text(value: Any) -> str:
    if value in (None, False):
        return ""
    if isinstance(value, (list, tuple)):
        if len(value) >= 2 and isinstance(value[1], str):
            return value[1].replace("\r", "\n").strip()
    return str(value).replace("\r", "\n").strip()


def _normalize_odoo_relational_text(text: str) -> str:
    if not text:
        return ""
    tuple_match = re.match(r"^[\[(]?\s*\d+\s*,\s*['\"]([^'\"]+)['\"]\s*[\])]?$", text)
    if tuple_match:
        return tuple_match.group(1).strip()
    text = re.sub(r"\b[a-zA-Z_][\w.]*\(\d+,?\)\s*-\s*", "", text)
    text = re.sub(r"\b[a-zA-Z_][\w.]*\(\d+,?\)", "", text)
    return text.strip()


def _clean_line(value: Any) -> str:
    text = _safe_text(value)
    if not text:
        return ""
    text = _normalize_odoo_relational_text(text)
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip(" -\n\t")


def _split_lines(value: Any) -> List[str]:
    text = _clean_line(value)
    if not text:
        return []
    lines = []
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        line = line.lstrip("-").strip()
        if line:
            lines.append(line)
    return lines


def _unique_strings(values: List[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        clean = _clean_line(value)
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(clean)
    return result


def _unique_dicts(rows: List[Dict[str, Any]], key_fields: List[str]) -> List[Dict[str, Any]]:
    seen = set()
    result = []
    for row in rows:
        key = tuple(_clean_line(row.get(field, "")).lower() for field in key_fields)
        if all(not part for part in key):
            continue
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def _first_non_empty(*values: Any) -> str:
    for value in values:
        text = _clean_line(value)
        if text:
            return text
    return ""


def _parse_dt(value: Any) -> Optional[dt.datetime]:
    text = _clean_line(value)
    if not text:
        return None
    candidates = [
        text.replace("Z", ""),
        text.replace("T", " "),
        text.replace("T", " ").split(".")[0],
    ]
    for candidate in candidates:
        try:
            return dt.datetime.fromisoformat(candidate)
        except ValueError:
            continue
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _fmt_date(value: Any) -> str:
    parsed = _parse_dt(value)
    if parsed:
        return parsed.strftime("%Y-%m-%d")
    return _clean_line(value)


def _parse_prescription_content(content: Any) -> Dict[str, str]:
    text = _safe_text(content)
    out: Dict[str, str] = {}

    patient_match = re.search(
        r"Patient:\s*(?P<name>.+?)\s*\(ID:\s*(?P<patient_id>[^)]+)\)\s*,\s*(?P<age>[^,]+?)\s+years old\s*,\s*(?P<gender>[^\n]+)",
        text,
        re.IGNORECASE,
    )
    if patient_match:
        out["patient_name"] = _clean_line(patient_match.group("name"))
        out["patient_id"] = _clean_line(patient_match.group("patient_id"))
        out["age"] = _clean_line(patient_match.group("age"))
        out["gender"] = _clean_line(patient_match.group("gender"))

    physician_match = re.search(r"Physician:\s*(.+)", text, re.IGNORECASE)
    if physician_match:
        physician = _clean_line(physician_match.group(1))
        reg_match = re.search(r"(Reg\s*no\.?\s*.*)$", physician, re.IGNORECASE)
        if reg_match:
            out["reg_no"] = _clean_line(reg_match.group(1))
            physician = _clean_line(physician[: reg_match.start()])
        out["physician"] = physician

    rx_match = re.search(r"Prescription\s+\S+\s+Date:\s*([^\n]+)", text, re.IGNORECASE)
    if rx_match:
        out["prescription_date"] = _clean_line(rx_match.group(1))

    diagnosis_match = re.search(r"Diagnosis:\s*(.+?)(?:\n[A-Z][^\n]*:|\Z)", text, re.IGNORECASE | re.DOTALL)
    if diagnosis_match:
        out["diagnosis"] = _clean_line(diagnosis_match.group(1))

    return out


def _parse_patient_details_blob(value: Any) -> Dict[str, List[str]]:
    text = _safe_text(value)
    if not text:
        return {}

    labels = [
        "Diagnosis_Info",
        "Complaint_Info",
        "Medicine_info",
        "Exercise_Info",
        "Investigation_Info",
    ]
    matches = list(re.finditer(r"(Diagnosis_Info|Complaint_Info|Medicine_info|Exercise_Info|Investigation_Info):", text))
    if not matches:
        return {}

    parsed: Dict[str, List[str]] = {}
    for index, match in enumerate(matches):
        label = match.group(1)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end]
        lines = _split_lines(block)
        if lines:
            parsed[label] = lines

    for label in labels:
        parsed.setdefault(label, [])
    return parsed


def _coerce_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value in (None, "", False):
        return []
    return [value]


def _exercise_label(row: Dict[str, Any]) -> str:
    return _first_non_empty(
        row.get("exercise_name"),
        row.get("display_name"),
        row.get("name"),
        row.get("exercise"),
    )


def _status_for_vital(name: str, value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "Noted" if _clean_line(value) else ""

    key = name.lower()
    if "systolic" in key:
        if numeric >= 180 or numeric <= 80:
            return "Critical"
        if numeric > 140 or numeric < 90:
            return "High" if numeric > 140 else "Low"
        return "Normal"
    if "diastolic" in key:
        if numeric >= 120 or numeric <= 50:
            return "Critical"
        if numeric > 90 or numeric < 60:
            return "High" if numeric > 90 else "Low"
        return "Normal"
    if "pulse" in key or "heart rate" in key:
        if numeric > 120 or numeric < 40:
            return "Critical"
        if numeric > 100 or numeric < 60:
            return "High" if numeric > 100 else "Low"
        return "Normal"
    if "temperature" in key:
        if numeric >= 103:
            return "Critical"
        if numeric > 99.5:
            return "High"
        if numeric < 96:
            return "Low"
        return "Normal"
    if "spo2" in key:
        if numeric < 90:
            return "Critical"
        if numeric < 94:
            return "Low"
        return "Normal"
    if "respiratory" in key:
        if numeric > 30 or numeric < 8:
            return "Critical"
        if numeric > 20 or numeric < 12:
            return "High" if numeric > 20 else "Low"
        return "Normal"
    if "rbs" in key:
        if numeric > 250 or numeric < 50:
            return "Critical"
        if numeric > 140 or numeric < 70:
            return "High" if numeric > 140 else "Low"
        return "Normal"
    if "bmi" in key:
        if numeric >= 30:
            return "High"
        if numeric < 18.5:
            return "Low"
        return "Normal"
    return "Noted"


def _normal_range_for_vital(name: str) -> str:
    key = name.lower()
    if "blood pressure" in key:
        return "90/60 - 120/80 mmHg"
    if "systolic" in key:
        return "90 - 120 mmHg"
    if "diastolic" in key:
        return "60 - 80 mmHg"
    if "pulse" in key or "heart rate" in key:
        return "60 - 100 bpm"
    if "temperature" in key:
        return "97 - 99.5 F"
    if "spo2" in key:
        return "94 - 100 %"
    if "respiratory" in key:
        return "12 - 20 /min"
    if "rbs" in key:
        return "70 - 140 mg/dL"
    if "bmi" in key:
        return "18.5 - 24.9"
    return "-"


def _derive_vitals(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    latest_values: Dict[str, Any] = {}
    latest_label = {
        "blood_pressure": "Blood Pressure",
        "bp_systolic": "BP Systolic",
        "bp_diastolic": "BP Diastolic",
        "pulse": "Pulse / Heart Rate",
        "temperature": "Body Temperature",
        "spo2": "SpO2",
        "respiratory_rate": "Respiratory Rate",
        "rbs": "Random Blood Sugar",
        "bmi": "BMI",
        "weight": "Weight",
        "height": "Height",
    }

    for record in sorted(records, key=lambda row: row.get("_sort_dt") or dt.datetime.min, reverse=True):
        vitals = record.get("metadata", {}).get("vitals") or {}
        for key in latest_label:
            value = vitals.get(key)
            if key in latest_values:
                continue
            if key == "blood_pressure":
                if _clean_line(value):
                    latest_values[key] = value
            elif value not in (None, "", False, 0, 0.0):
                latest_values[key] = value

    result = []
    for key, label in latest_label.items():
        if key not in latest_values:
            continue
        value = latest_values[key]
        if key in {"weight", "height"}:
            rendered = str(value)
            status = "Noted"
        else:
            rendered = str(value)
            status = _status_for_vital(label, value)
        result.append(
            {
                "parameter": label,
                "recorded_value": rendered,
                "status": status,
                "normal_range": _normal_range_for_vital(label),
            }
        )
    return result


def build_deterministic_rolling_summary(records: List[Dict[str, Any]], patient_seq: str) -> Dict[str, Any]:
    normalized_records: List[Dict[str, Any]] = []
    for record in records:
        meta = record.get("metadata") or {}
        content_info = _parse_prescription_content(record.get("content"))
        details_info = _parse_patient_details_blob(meta.get("patient_details"))
        sort_dt = _parse_dt(meta.get("prescription_date")) or _parse_dt(content_info.get("prescription_date")) or dt.datetime.min
        normalized_records.append(
            {
                **record,
                "_content_info": content_info,
                "_details_info": details_info,
                "_sort_dt": sort_dt,
            }
        )

    prescriptions = [r for r in normalized_records if r.get("source_model") == "prescription.order.knk"]
    prescriptions.sort(key=lambda row: (row.get("_sort_dt") or dt.datetime.min, row.get("id", 0)))
    latest_prescription = prescriptions[-1] if prescriptions else {}

    partner_records = [r for r in normalized_records if r.get("source_model") == "res.partner"]
    partner_content = _safe_text(partner_records[0].get("content")) if partner_records else ""
    partner_name = ""
    partner_gender = ""
    partner_age = ""
    partner_location = ""
    if partner_content:
        match = re.search(
            r"Patient Profile:\s*(?P<name>.*?)\s+Seq ID:\s*(?P<seq>\S+)\s+Gender:\s*(?P<gender>\S+)\s+Age:\s*(?P<age>\S+)\s+Location:\s*(?P<location>.+)",
            partner_content,
            re.IGNORECASE,
        )
        if match:
            partner_name = _clean_line(match.group("name"))
            partner_gender = _clean_line(match.group("gender"))
            partner_age = _clean_line(match.group("age"))
            partner_location = _clean_line(match.group("location"))

    latest_content = latest_prescription.get("_content_info", {})
    latest_meta = latest_prescription.get("metadata", {})
    latest_details = latest_prescription.get("_details_info", {})

    patient_name = _first_non_empty(latest_content.get("patient_name"), partner_name, "Patient")
    gender = _first_non_empty(latest_content.get("gender"), partner_gender)
    age = _first_non_empty(latest_content.get("age"), partner_age)
    physician = _first_non_empty(latest_content.get("physician"))
    reg_no = _first_non_empty(latest_content.get("reg_no"))

    diagnosis_lines: List[str] = []
    complaint_lines: List[str] = []
    medication_lines: List[str] = []
    exercise_lines: List[str] = []
    investigation_lines: List[str] = []
    advice_lines: List[str] = []
    general_history_lines: List[str] = []
    old_history_lines: List[str] = []
    medical_history_rows: List[Dict[str, str]] = []
    sign_rows: List[Dict[str, str]] = []
    lab_rows: List[Dict[str, str]] = []
    complaint_timeline: List[Dict[str, str]] = []
    medications_current: List[Dict[str, Any]] = []

    for record in prescriptions:
        meta = record.get("metadata", {})
        details = record.get("_details_info", {})
        content_info = record.get("_content_info", {})
        record_date = _fmt_date(meta.get("prescription_date") or content_info.get("prescription_date"))

        diagnosis_lines.extend(details.get("Diagnosis_Info", []))
        complaint_lines.extend(details.get("Complaint_Info", []))
        medication_lines.extend(details.get("Medicine_info", []))
        exercise_lines.extend(details.get("Exercise_Info", []))
        investigation_lines.extend(details.get("Investigation_Info", []))
        advice_lines.extend(_split_lines(meta.get("advice_notes")))
        advice_lines.extend(_split_lines(meta.get("followup_notes")))
        advice_lines.extend(_split_lines(meta.get("additional_comments")))
        advice_lines.extend(_split_lines(meta.get("extra_notes")))
        general_history_lines.extend(_split_lines(meta.get("patient_history")))
        general_history_lines.extend(_split_lines(meta.get("description")))

        for row in _coerce_list(meta.get("old_history")):
            if not isinstance(row, dict):
                continue
            text = _first_non_empty(row.get("history_name"), row.get("name"), row.get("period_name"), row.get("period"))
            if text:
                old_history_lines.append(text)
                medical_history_rows.append(
                    {
                        "category": "Old History",
                        "past_plant": "Past",
                        "description": text,
                    }
                )

        for row in _coerce_list(meta.get("medical_history")):
            if not isinstance(row, dict):
                continue
            text = _first_non_empty(row.get("history_text"), row.get("name"))
            if text:
                history_date = _fmt_date(row.get("date")) or record_date or "Past"
                medical_history_rows.append(
                    {
                        "category": "Medical History",
                        "past_plant": history_date,
                        "description": text,
                    }
                )

        for row in _coerce_list(meta.get("diagnoses")):
            if not isinstance(row, dict):
                continue
            text = _first_non_empty(row.get("disease_name"), row.get("name"), row.get("disease_code"))
            if text:
                diagnosis_lines.append(text)

        for row in _coerce_list(meta.get("complaints")):
            if not isinstance(row, dict):
                continue
            parts = [
                _clean_line(row.get("complaint")),
                _clean_line(row.get("location")),
                _clean_line(row.get("period")),
            ]
            text = " - ".join(part for part in parts if part)
            if text:
                complaint_lines.append(text)
                complaint_timeline.append(
                    {
                        "complaint": text,
                        "trend_note": "Noted",
                        "start_date": record_date,
                        "end_date": record_date,
                    }
                )

        for row in _coerce_list(meta.get("signs")):
            if not isinstance(row, dict):
                continue
            sign_text = _first_non_empty(row.get("sign_name"), row.get("name"))
            location = _clean_line(row.get("location"))
            if sign_text or location:
                sign_rows.append(
                    {
                        "symptom_test": " at ".join(part for part in [sign_text, location] if part),
                        "finding_flag": "Noted",
                    }
                )

        for row in _coerce_list(meta.get("investigations")):
            if not isinstance(row, dict):
                continue
            test_name = _first_non_empty(row.get("investigation_name"), row.get("name"))
            if not test_name:
                continue
            result_text = _first_non_empty(meta.get("investigation_result"))
            lab_rows.append(
                {
                    "investigation": test_name,
                    "result": result_text or "Ordered / Mentioned",
                    "normal_range": "-",
                    "unit": "-",
                    "status": "Noted",
                }
            )

        for row in _coerce_list(meta.get("exercises")):
            if not isinstance(row, dict):
                continue
            parts = [
                _exercise_label(row),
                _clean_line(row.get("move")),
                _clean_line(row.get("repitition") or row.get("reps")),
            ]
            text = " - ".join(part for part in parts if part)
            if text:
                exercise_lines.append(text)

        if _clean_line(meta.get("investigation_result")) and not _coerce_list(meta.get("investigations")):
            lab_rows.append(
                {
                    "investigation": "Investigation Result",
                    "result": _clean_line(meta.get("investigation_result")),
                    "normal_range": "-",
                    "unit": "-",
                    "status": "Noted",
                }
            )

        if record is latest_prescription:
            medications_current = []
            for row in _coerce_list(meta.get("medications")):
                if not isinstance(row, dict):
                    continue
                med_name = _first_non_empty(row.get("medication_name"), row.get("name"))
                if not med_name:
                    continue
                medications_current.append(
                    {
                        "medication_drug_name": med_name,
                        "dose": _first_non_empty(row.get("dose")),
                        "freq": _first_non_empty(row.get("frequency"), row.get("freq")),
                        "route": _first_non_empty(row.get("route")),
                        "food": _first_non_empty(row.get("food"), row.get("when_to_take"), row.get("instruction")),
                        "duration": _first_non_empty(row.get("duration"), row.get("days")),
                        "qty": _first_non_empty(row.get("qty"), row.get("quantity")),
                        "amount": _first_non_empty(row.get("amount")),
                        "margin": _first_non_empty(row.get("margin")),
                    }
                )

    diagnosis_lines = _unique_strings(diagnosis_lines)
    complaint_lines = _unique_strings(complaint_lines)
    medication_lines = _unique_strings(medication_lines)
    exercise_lines = _unique_strings(exercise_lines)
    investigation_lines = _unique_strings(investigation_lines)
    advice_lines = _unique_strings(advice_lines)
    general_history_lines = _unique_strings(general_history_lines)
    old_history_lines = _unique_strings(old_history_lines)
    medical_history_rows = _unique_dicts(medical_history_rows, ["category", "past_plant", "description"])
    sign_rows = _unique_dicts(sign_rows, ["symptom_test", "finding_flag"])
    lab_rows = _unique_dicts(lab_rows, ["investigation", "result"])
    complaint_timeline = _unique_dicts(complaint_timeline, ["complaint", "start_date", "end_date"])

    if not medications_current and latest_details.get("Medicine_info"):
        for line in _unique_strings(latest_details.get("Medicine_info", [])):
            medications_current.append(
                {
                    "medication_drug_name": line,
                    "dose": "",
                    "freq": "",
                    "route": "",
                    "food": "",
                    "duration": "",
                    "qty": "",
                    "amount": "",
                    "margin": "",
                }
            )

    latest_next_visit_days = latest_meta.get("next_visit_days")
    next_time = ""
    if latest_next_visit_days not in (None, "", False, 0):
        next_time = f"Review in {latest_next_visit_days} day(s)"
    elif advice_lines:
        next_time = advice_lines[0]

    primary_complaints = complaint_lines[:8]
    secondary_complaints = []
    secondary_complaints.extend(general_history_lines[:6])
    secondary_complaints.extend(old_history_lines[:6])
    secondary_complaints = _unique_strings(secondary_complaints)[:8]

    past_medical_history = _unique_strings(diagnosis_lines + old_history_lines + general_history_lines)[:10]

    vitals_indicators = sign_rows[:]
    clinical_scores = latest_meta.get("clinical_scores") or {}
    pain_score = clinical_scores.get("pain_score")
    if pain_score not in (None, "", False, 0):
        vitals_indicators.append(
            {
                "symptom_test": f"Pain Score {pain_score}",
                "finding_flag": "High" if float(pain_score) >= 7 else ("Medium" if float(pain_score) >= 4 else "Noted"),
            }
        )
    for key, value in (latest_meta.get("status_updates") or {}).items():
        if value in (None, "", False, 0):
            continue
        vitals_indicators.append(
            {
                "symptom_test": key.replace("_", " ").title(),
                "finding_flag": "Noted",
            }
        )
    vitals_indicators = _unique_dicts(vitals_indicators, ["symptom_test", "finding_flag"])

    suspect_and_care_plan = []
    if diagnosis_lines:
        suspect_and_care_plan.append(
            {
                "clinical_action": f"Continue evaluation and treatment for {diagnosis_lines[0]}",
                "additional_considerations": "Built from complete indexed prescription history and patient notes",
                "priority_level": "Medium",
                "next_time": next_time,
            }
        )
    if advice_lines:
        suspect_and_care_plan.append(
            {
                "clinical_action": advice_lines[0],
                "additional_considerations": advice_lines[1] if len(advice_lines) > 1 else "",
                "priority_level": "Medium",
                "next_time": next_time,
            }
        )
    if exercise_lines:
        suspect_and_care_plan.append(
            {
                "clinical_action": "Continue prescribed exercise and rehabilitation plan",
                "additional_considerations": "; ".join(exercise_lines[:3]),
                "priority_level": "Low",
                "next_time": next_time,
            }
        )
    suspect_and_care_plan = _unique_dicts(suspect_and_care_plan, ["clinical_action", "additional_considerations"])

    follow_up_monitoring_plan = []
    for line in investigation_lines[:8]:
        follow_up_monitoring_plan.append(
            {
                "test_name": line,
                "frequency": "At next review",
                "monitoring_points": "Review investigation findings with clinical progress",
                "scheduling_date": next_time,
            }
        )
    if not follow_up_monitoring_plan:
        follow_up_monitoring_plan.append(
            {
                "test_name": "Clinical follow-up review",
                "frequency": "As advised",
                "monitoring_points": "Symptoms, medication response, and longitudinal history",
                "scheduling_date": next_time,
            }
        )

    summary = {
        "allergy_alert": "",
        "patient_demographics": {
            "patient_name": patient_name,
            "date_of_birth_age": age,
            "gender": gender,
            "contact": "",
            "presenting_doctor": physician,
            "hmo_hospital": partner_location,
            "reg_no": reg_no,
            "past_medical_history": " | ".join(past_medical_history[:6]),
            "patient_id": patient_seq,
        },
        "vitals_at_visit": _derive_vitals(prescriptions),
        "chief_complaints": {
            "primary_complaints": primary_complaints,
            "secondary_background_complaints": secondary_complaints,
            "clinical_impression": " | ".join(diagnosis_lines[:4]),
        },
        "vitals_indicators": vitals_indicators[:12],
        "lab_report_mandatory": lab_rows[:12],
        "medications_prescribed": {
            "prescription_date": _fmt_date(latest_meta.get("prescription_date") or latest_content.get("prescription_date")),
            "physician": physician,
            "diagnosis": " | ".join(diagnosis_lines[:4]),
            "current_medications": medications_current[:20],
        },
        "medical_history_findings": medical_history_rows[:20],
        "clinical_record_mapping": complaint_timeline[:12],
        "suspect_and_care_plan": suspect_and_care_plan[:8],
        "follow_up_monitoring_plan": follow_up_monitoring_plan[:10],
    }

    if not summary["medical_history_findings"] and general_history_lines:
        summary["medical_history_findings"] = [
            {
                "category": "Clinical History",
                "past_plant": "Past",
                "description": line,
            }
            for line in general_history_lines[:12]
        ]

    if not summary["clinical_record_mapping"] and primary_complaints:
        summary["clinical_record_mapping"] = [
            {
                "complaint": complaint,
                "trend_note": "Noted",
                "start_date": _fmt_date(latest_meta.get("prescription_date") or latest_content.get("prescription_date")),
                "end_date": _fmt_date(latest_meta.get("prescription_date") or latest_content.get("prescription_date")),
            }
            for complaint in primary_complaints[:8]
        ]

    return summary
