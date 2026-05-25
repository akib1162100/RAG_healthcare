import copy
import datetime as dt
import json
import re
from typing import Any, Dict, List, Optional


DETAIL_SECTION_KEYS = (
    "allergy_alert",
    "patient_demographics",
    "vitals_at_visit",
    "chief_complaints",
    "red_flag_indicators",
    "diagnoses",
    "medications_prescribed",
    "investigations_ordered",
    "clinical_decision_mapping",
    "advise_care_plan",
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


def _clean_text(value: Any) -> str:
    text = _safe_text(value)
    if not text:
        return ""
    text = _normalize_odoo_relational_text(text)
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip(" -\n\t")


def _split_text_values(value: Any) -> List[str]:
    if isinstance(value, list):
        raw_values = value
    else:
        text = _clean_text(value)
        if not text:
            return []
        normalized = text.replace("|", "\n")
        raw_values = normalized.split("\n")

    seen = set()
    output = []
    for item in raw_values:
        text = _clean_text(item)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(text)
    return output


def _coerce_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value in (None, "", False):
        return []
    return [value]


def _first_non_empty(*values: Any) -> str:
    for value in values:
        text = _clean_text(value)
        if text:
            return text
    return ""


def _parse_dt(value: Any) -> Optional[dt.datetime]:
    text = _clean_text(value)
    if not text:
        return None
    for candidate in [text.replace("Z", ""), text.replace("T", " "), text.replace("T", " ").split(".")[0]]:
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
    return _clean_text(value)


def _dedupe_list(values: List[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        text = _clean_text(value)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _dedupe_dicts(rows: List[Dict[str, Any]], key_fields: List[str]) -> List[Dict[str, Any]]:
    seen = set()
    result = []
    for row in rows:
        key = tuple(_clean_text(row.get(field, "")).lower() for field in key_fields)
        if all(not item for item in key):
            continue
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def _exercise_label(row: Dict[str, Any]) -> str:
    return _first_non_empty(
        row.get("exercise_name"),
        row.get("display_name"),
        row.get("name"),
        row.get("exercise"),
    )


def _extract_named_block(text: str, label: str) -> List[str]:
    matches = list(re.finditer(r"(Diagnosis_Info|Complaint_Info|Medicine_info|Exercise_Info|Investigation_Info):", text))
    if not matches:
        return []
    for index, match in enumerate(matches):
        if match.group(1) != label:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        return _split_text_values(text[start:end])
    return []


def _parse_patient_details_blob(value: Any) -> Dict[str, List[str]]:
    text = _safe_text(value)
    if not text:
        return {}
    return {
        "Diagnosis_Info": _extract_named_block(text, "Diagnosis_Info"),
        "Complaint_Info": _extract_named_block(text, "Complaint_Info"),
        "Medicine_info": _extract_named_block(text, "Medicine_info"),
        "Exercise_Info": _extract_named_block(text, "Exercise_Info"),
        "Investigation_Info": _extract_named_block(text, "Investigation_Info"),
    }


def _parse_content(content: Any) -> Dict[str, str]:
    text = _safe_text(content)
    output: Dict[str, str] = {}

    patient_match = re.search(
        r"Patient:\s*(?P<name>.+?)\s*\(ID:\s*(?P<patient_id>[^)]+)\)\s*,\s*(?P<age>[^,]+?)\s+years old\s*,\s*(?P<gender>[^\n]+)",
        text,
        re.IGNORECASE,
    )
    if patient_match:
        output["patient_name"] = _clean_text(patient_match.group("name"))
        output["patient_id"] = _clean_text(patient_match.group("patient_id"))
        output["age"] = _clean_text(patient_match.group("age"))
        output["gender"] = _clean_text(patient_match.group("gender"))

    physician_match = re.search(r"Physician:\s*(.+)", text, re.IGNORECASE)
    if physician_match:
        physician = _clean_text(physician_match.group(1))
        reg_match = re.search(r"(Reg\s*no\.?\s*.*)$", physician, re.IGNORECASE)
        if reg_match:
            output["reg_no"] = _clean_text(reg_match.group(1))
            physician = _clean_text(physician[: reg_match.start()])
        output["physician"] = physician

    rx_match = re.search(r"Prescription\s+\S+\s+Date:\s*([^\n]+)", text, re.IGNORECASE)
    if rx_match:
        output["prescription_date"] = _clean_text(rx_match.group(1))

    diagnosis_match = re.search(r"Diagnosis:\s*(.+?)(?:\n[A-Z][^\n]*:|\Z)", text, re.IGNORECASE | re.DOTALL)
    if diagnosis_match:
        output["diagnosis"] = _clean_text(diagnosis_match.group(1))

    return output


def group_prescription_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[Any, Dict[str, Any]] = {}
    order: List[Any] = []

    for record in records:
        source_id = record.get("source_id") or record.get("metadata", {}).get("odoo_res_id") or record.get("id")
        if source_id not in grouped:
            grouped[source_id] = {
                "source_id": source_id,
                "source_model": record.get("source_model"),
                "records": [],
            }
            order.append(source_id)
        grouped[source_id]["records"].append(record)

    combined_groups = []
    for source_id in order:
        group = grouped[source_id]
        parts = sorted(group["records"], key=lambda row: (row.get("metadata", {}).get("chunk_index", 0), row.get("id", 0)))
        base = copy.deepcopy(parts[0])
        merged_metadata: Dict[str, Any] = {}
        for part in parts:
            meta = copy.deepcopy(part.get("metadata") or {})
            for key, value in meta.items():
                existing = merged_metadata.get(key)
                if isinstance(value, list):
                    current = existing if isinstance(existing, list) else []
                    current.extend(value)
                    merged_metadata[key] = current
                elif isinstance(value, dict):
                    current = existing if isinstance(existing, dict) else {}
                    current.update(value)
                    merged_metadata[key] = current
                elif not _is_blank(value):
                    merged_metadata[key] = value
                elif key not in merged_metadata:
                    merged_metadata[key] = value

        full_content = "\n".join(_safe_text(part.get("content")) for part in parts if _safe_text(part.get("content")))
        merged_metadata["chunk_index"] = 0
        merged_metadata["total_chunks"] = len(parts)
        base["content"] = full_content or base.get("content", "")
        base["metadata"] = merged_metadata
        base["group_record_ids"] = [part.get("id") for part in parts if part.get("id") is not None]
        combined_groups.append(base)

    return combined_groups


def has_meaningful_prescription_details(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    if not any(not _is_blank(data.get(key)) for key in DETAIL_SECTION_KEYS):
        return False
    meds = data.get("medications_prescribed", {})
    complaints = data.get("chief_complaints", {})
    return bool(
        _coerce_list(_clean_text(data.get("allergy_alert")))
        or _coerce_list((meds or {}).get("current_medications"))
        or _coerce_list((complaints or {}).get("primary_complaints"))
        or _coerce_list(data.get("diagnoses"))
    )


def needs_prescription_detail_refresh(data: Any) -> bool:
    if not has_meaningful_prescription_details(data):
        return True
    if not isinstance(data, dict):
        return True
    required = {
        "red_flag_indicators",
        "diagnoses",
        "investigations_ordered",
        "clinical_decision_mapping",
        "advise_care_plan",
        "follow_up_monitoring_plan",
    }
    return any(key not in data for key in required)


def _normal_range_for_vital(name: str) -> str:
    key = name.lower()
    if "blood pressure" in key:
        return "90/60 - 120/80 mmHg"
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
    if "weight" in key:
        return "-"
    return "-"


def _status_for_vital(name: str, value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "Noted" if _clean_text(value) else ""
    key = name.lower()
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
    return "Normal"


def build_deterministic_prescription_details(record: Dict[str, Any]) -> Dict[str, Any]:
    meta = copy.deepcopy(record.get("metadata") or {})
    content_info = _parse_content(record.get("content"))
    detail_blob = _parse_patient_details_blob(meta.get("patient_details"))

    patient_name = _first_non_empty(content_info.get("patient_name"), meta.get("patient_name"), "Patient")
    patient_id = _first_non_empty(meta.get("patient_seq"), content_info.get("patient_id"))
    patient_age = _first_non_empty(content_info.get("age"), meta.get("patient_age"))
    patient_gender = _first_non_empty(content_info.get("gender"), meta.get("patient_gender"))
    physician = _first_non_empty(content_info.get("physician"), meta.get("physician_name"))
    reg_no = _first_non_empty(content_info.get("reg_no"))
    rx_date = _first_non_empty(meta.get("prescription_date"), content_info.get("prescription_date"))

    complaint_lines: List[str] = []
    complaint_lines.extend(detail_blob.get("Complaint_Info", []))
    for row in _coerce_list(meta.get("complaints")):
        if not isinstance(row, dict):
            continue
        text = " - ".join(filter(None, [
            _clean_text(row.get("complaint")),
            _clean_text(row.get("location")),
            _clean_text(row.get("period")),
        ]))
        if text:
            complaint_lines.append(text)
    complaint_lines = _dedupe_list(complaint_lines)

    diagnosis_lines: List[str] = []
    diagnosis_lines.extend(detail_blob.get("Diagnosis_Info", []))
    diagnosis_lines.extend(_split_text_values(content_info.get("diagnosis")))
    for row in _coerce_list(meta.get("diagnoses")):
        if not isinstance(row, dict):
            continue
        text = _first_non_empty(row.get("disease_name"), row.get("name"), row.get("disease_code"))
        if text:
            diagnosis_lines.append(text)
    diagnosis_lines = _dedupe_list(diagnosis_lines)

    history_lines: List[str] = []
    for key in ("patient_history", "description"):
        history_lines.extend(_split_text_values(meta.get(key)))
    for row in _coerce_list(meta.get("medical_history")):
        if not isinstance(row, dict):
            continue
        text = _first_non_empty(row.get("history_text"), row.get("name"))
        if text:
            history_lines.append(text)
    history_lines = _dedupe_list(history_lines)

    old_history_lines: List[str] = []
    for row in _coerce_list(meta.get("old_history")):
        if not isinstance(row, dict):
            continue
        text = _first_non_empty(row.get("history_name"), row.get("name"), row.get("period_name"), row.get("period"))
        if text:
            old_history_lines.append(text)
    old_history_lines = _dedupe_list(old_history_lines)

    advice_lines: List[str] = []
    for key in ("advice_notes", "followup_notes", "extra_notes", "additional_comments"):
        advice_lines.extend(_split_text_values(meta.get(key)))
    advice_lines = _dedupe_list(advice_lines)

    exercise_lines: List[str] = []
    exercise_lines.extend(detail_blob.get("Exercise_Info", []))
    for row in _coerce_list(meta.get("exercises")):
        if not isinstance(row, dict):
            continue
        pieces = [
            _exercise_label(row),
            _clean_text(row.get("move")),
            _clean_text(row.get("repitition") or row.get("reps")),
        ]
        text = " - ".join(piece for piece in pieces if piece)
        if text:
            exercise_lines.append(text)
    exercise_lines = _dedupe_list(exercise_lines)

    vitals = meta.get("vitals") or {}
    vitals_rows = []
    vital_map = {
        "blood_pressure": "Blood Pressure",
        "pulse": "Pulse / Heart Rate",
        "temperature": "Body Temperature",
        "spo2": "SpO2",
        "respiratory_rate": "Respiratory Rate",
        "rbs": "Random Blood Sugar",
        "bmi": "BMI",
        "weight": "Weight",
    }
    for key, label in vital_map.items():
        value = vitals.get(key)
        if key == "blood_pressure":
            if not _clean_text(value):
                continue
        elif value in (None, "", False, 0, 0.0):
            continue
        vitals_rows.append({
            "parameter": label,
            "recorded_value": str(value),
            "status": _status_for_vital(label, value),
            "normal_range": _normal_range_for_vital(label),
        })
    if not vitals_rows:
        vitals_rows.append({
            "parameter": "Physical Board Result",
            "recorded_value": "-",
            "status": "Normal",
            "normal_range": "-",
        })

    red_flags_cardio: List[str] = []
    red_flags_routine: List[str] = []
    for vital in vitals_rows:
        status = _clean_text(vital.get("status"))
        if status in {"High", "Low", "Critical"}:
            target = red_flags_cardio if any(token in vital["parameter"].lower() for token in ("blood pressure", "pulse", "heart")) else red_flags_routine
            target.append(f"{vital['parameter']} {vital['recorded_value']} ({status})")
    if _clean_text(meta.get("investigation_result")):
        red_flags_routine.append("Abnormal investigation results noted")
    for row in _coerce_list(meta.get("signs")):
        if not isinstance(row, dict):
            continue
        sign_text = " at ".join(filter(None, [
            _first_non_empty(row.get("sign_name"), row.get("name")),
            _clean_text(row.get("location")),
        ]))
        if sign_text:
            red_flags_routine.append(sign_text)
    if meta.get("clinical_scores", {}).get("pain_score", 0) not in (0, None, False):
        pain_score = meta["clinical_scores"]["pain_score"]
        if isinstance(pain_score, (int, float)) and pain_score >= 7:
            red_flags_routine.append(f"Pain score {pain_score}/10")
    red_flags_cardio = _dedupe_list(red_flags_cardio)
    red_flags_routine = _dedupe_list(red_flags_routine)

    diagnoses = []
    for idx, text in enumerate(diagnosis_lines[:8], start=1):
        diagnoses.append({
            "diagnosis": text,
            "secondary_complication": "",
            "icd_10": "",
            "snomed": "",
            "type": "Primary" if idx == 1 else "Secondary",
            "specialty": "Medicine",
        })
    if not diagnoses and history_lines:
        diagnoses.append({
            "diagnosis": history_lines[0],
            "secondary_complication": "",
            "icd_10": "",
            "snomed": "",
            "type": "Primary",
            "specialty": "Medicine",
        })

    current_meds = []
    for med in _coerce_list(meta.get("medications")):
        if not isinstance(med, dict):
            continue
        med_name = _first_non_empty(med.get("medication_name"), med.get("name"))
        if not med_name:
            continue
        current_meds.append({
            "medication_drug_name": med_name,
            "dose": _first_non_empty(med.get("dose"), re.search(r"(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml))", med_name).group(1) if re.search(r"(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml))", med_name) else ""),
            "freq": _first_non_empty(med.get("frequency"), med.get("instruction"), "As directed"),
            "route": _first_non_empty(med.get("route"), "Oral"),
            "food": _first_non_empty(med.get("when_to_take"), med.get("instruction"), "As directed"),
            "duration": _first_non_empty(med.get("days"), med.get("duration_value")),
            "qty": _first_non_empty(med.get("quantity"), med.get("qty_per_day")),
            "margin": _first_non_empty(med.get("margin")),
        })
    if not current_meds:
        for line in detail_blob.get("Medicine_info", []):
            current_meds.append({
                "medication_drug_name": line,
                "dose": "",
                "freq": "As directed",
                "route": "Oral",
                "food": "As directed",
                "duration": "",
                "qty": "",
                "margin": "",
            })

    investigation_rows = []
    for row in _coerce_list(meta.get("investigations")):
        if not isinstance(row, dict):
            continue
        test_name = _first_non_empty(row.get("investigation_name"), row.get("name"))
        if test_name:
            investigation_rows.append({
                "category": "Clinical",
                "test_panel": test_name,
                "clinical_indication": _first_non_empty(meta.get("investigation_result"), "Ordered / Mentioned"),
            })
    for line in detail_blob.get("Investigation_Info", []):
        investigation_rows.append({
            "category": "Clinical",
            "test_panel": line,
            "clinical_indication": "From patient details",
        })
    if _clean_text(meta.get("investigation_result")) and not investigation_rows:
        investigation_rows.append({
            "category": "Clinical",
            "test_panel": "Investigation Result",
            "clinical_indication": _clean_text(meta.get("investigation_result")),
        })
    investigation_rows = _dedupe_dicts(investigation_rows, ["test_panel", "clinical_indication"])

    decision_rows = []
    likely_dx = diagnoses[0]["diagnosis"] if diagnoses else _first_non_empty(history_lines[0] if history_lines else "")
    next_action = advice_lines[0] if advice_lines else "Clinical review"
    for complaint in complaint_lines[:6]:
        decision_rows.append({
            "complaint": complaint,
            "time_course": _fmt_date(rx_date),
            "pattern": "Noted",
            "most_likely_dx": likely_dx,
            "next_action": next_action,
        })
    if not decision_rows:
        decision_rows.append({
            "complaint": "Prescription follow-up",
            "time_course": _fmt_date(rx_date),
            "pattern": "Noted",
            "most_likely_dx": likely_dx,
            "next_action": next_action,
        })

    care_plan = {
        "lifestyle_diet": _dedupe_list(exercise_lines + history_lines[:3])[:8] or ["Continue prescribed rehabilitation and general lifestyle advice"],
        "medication_instructions": _dedupe_list(advice_lines[:4] + [f"Take {med['medication_drug_name']} as directed" for med in current_meds[:3]])[:8] or ["Take medications exactly as prescribed"],
        "warning_signs_seek_care": _dedupe_list(red_flags_cardio + red_flags_routine)[:8] or ["Return for clinical review if symptoms worsen"],
    }

    next_visit = _first_non_empty(meta.get("date_of_next_visit"))
    if not next_visit and meta.get("next_visit_days") not in (None, "", False, 0):
        next_visit = f"In {meta.get('next_visit_days')} day(s)"
    if not next_visit and advice_lines:
        next_visit = advice_lines[0]

    follow_up = {
        "next_visit": next_visit or "-",
        "signature_status": _first_non_empty(meta.get("check_patient"), meta.get("status_updates", {}).get("counseling_behavioral_response"), "Awaiting review"),
        "investigations": " | ".join(_dedupe_list([row["test_panel"] for row in investigation_rows])) or "-",
        "referral": " | ".join(_dedupe_list(_split_text_values(meta.get("followup_notes")) + _split_text_values(meta.get("procedure_result")))) or "-",
    }

    details = {
        "allergy_alert": "",
        "patient_demographics": {
            "patient_name": patient_name,
            "date_of_birth_age": patient_age,
            "contact": "",
            "presenting_doctor": physician,
            "past_medical_history": " | ".join(_dedupe_list(history_lines + old_history_lines)[:6]),
            "gender": patient_gender,
            "hmo_hospital": "",
            "reg_no": reg_no,
            "patient_id": patient_id,
        },
        "vitals_at_visit": vitals_rows,
        "chief_complaints": {
            "primary_complaints": complaint_lines[:8] or ["No chief complaint captured"],
            "secondary_background_complaints": _dedupe_list(history_lines + old_history_lines)[:8],
        },
        "red_flag_indicators": {
            "alert_message": "MANDATORY: Active red flags identified" if (red_flags_cardio or red_flags_routine) else "No active red flags identified",
            "cardiology_red_flags": red_flags_cardio,
            "routine_red_flags": red_flags_routine,
        },
        "diagnoses": diagnoses,
        "medications_prescribed": {
            "date": _fmt_date(rx_date),
            "current_medications": current_meds,
            "other_historical_medications": _dedupe_list([_clean_text(item) for item in _coerce_list(meta.get("medication_history"))])[:10],
        },
        "investigations_ordered": investigation_rows,
        "clinical_decision_mapping": decision_rows,
        "advise_care_plan": care_plan,
        "follow_up_monitoring_plan": follow_up,
    }
    return details


def _merge_values(base: Any, override: Any) -> Any:
    if _is_blank(override):
        return base
    if isinstance(base, dict) and isinstance(override, dict):
        merged = copy.deepcopy(base)
        for key, value in override.items():
            merged[key] = _merge_values(merged.get(key), value)
        return merged
    if isinstance(base, list) and isinstance(override, list):
        return override if override else base
    return override


def merge_prescription_details(base: Dict[str, Any], enriched: Any) -> Dict[str, Any]:
    if not isinstance(enriched, dict):
        return base
    return _merge_values(base, enriched)
