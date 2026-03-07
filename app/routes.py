import logging
import re
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, render_template
from .database import db, Patient
from .validators import validate_patient_data

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Helper: standard JSON envelope
# ─────────────────────────────────────────────
def ok(data, status=200):
    return jsonify({"data": data, "error": None}), status


def err(message, status=400):
    return jsonify({"data": None, "error": message}), status


# ─────────────────────────────────────────────
# Blueprint: /patients
# ─────────────────────────────────────────────
patients_bp = Blueprint("patients", __name__)


@patients_bp.route("/", methods=["GET"])
def dashboard():
    return render_template("dashboard.html")


@patients_bp.route("/patients", methods=["GET"])
def list_patients():
    q = Patient.query.filter(Patient.deleted_at.is_(None))

    if ln := request.args.get("last_name"):
        q = q.filter(Patient.last_name.ilike(f"%{ln}%"))
    if dob := request.args.get("date_of_birth"):
        q = q.filter(Patient.date_of_birth == dob)
    if ph := request.args.get("phone_number"):
        digits = re.sub(r"\D", "", ph)
        q = q.filter(Patient.phone_number.contains(digits))

    patients = q.order_by(Patient.created_at.desc()).all()
    return ok([p.to_dict() for p in patients])


@patients_bp.route("/patients/<patient_id>", methods=["GET"])
def get_patient(patient_id):
    p = Patient.query.filter_by(patient_id=patient_id).filter(Patient.deleted_at.is_(None)).first()
    if not p:
        return err("Patient not found.", 404)
    return ok(p.to_dict())


@patients_bp.route("/patients", methods=["POST"])
def create_patient():
    data = request.get_json(silent=True)
    if not data:
        return err("Request body must be JSON.", 400)

    errors = validate_patient_data(data)
    if errors:
        return err(errors, 422)

    # Normalize phone digits only
    phone_digits = re.sub(r"\D", "", data["phone_number"])

    # Duplicate detection
    existing = Patient.query.filter_by(phone_number=phone_digits).filter(Patient.deleted_at.is_(None)).first()
    if existing:
        return jsonify({
            "data": existing.to_dict(),
            "error": None,
            "duplicate": True,
            "message": f"A patient named {existing.first_name} {existing.last_name} already exists with this phone number."
        }), 200

    p = Patient(
        first_name      = data["first_name"].strip(),
        last_name       = data["last_name"].strip(),
        date_of_birth   = data["date_of_birth"],
        sex             = data["sex"],
        phone_number    = phone_digits,
        email           = data.get("email"),
        address_line_1  = data["address_line_1"].strip(),
        address_line_2  = data.get("address_line_2"),
        city            = data["city"].strip(),
        state           = data["state"].upper(),
        zip_code        = data["zip_code"],
        insurance_provider   = data.get("insurance_provider"),
        insurance_member_id  = data.get("insurance_member_id"),
        preferred_language   = data.get("preferred_language", "English"),
        emergency_contact_name  = data.get("emergency_contact_name"),
        emergency_contact_phone = re.sub(r"\D", "", data["emergency_contact_phone"])
                                  if data.get("emergency_contact_phone") else None,
    )
    db.session.add(p)
    db.session.commit()

    logger.info("NEW PATIENT REGISTERED: %s", p.to_dict())
    return ok(p.to_dict(), 201)


@patients_bp.route("/patients/<patient_id>", methods=["PUT"])
def update_patient(patient_id):
    p = Patient.query.filter_by(patient_id=patient_id).filter(Patient.deleted_at.is_(None)).first()
    if not p:
        return err("Patient not found.", 404)

    data = request.get_json(silent=True)
    if not data:
        return err("Request body must be JSON.", 400)

    errors = validate_patient_data(data, partial=True)
    if errors:
        return err(errors, 422)

    ALLOWED = [
        "first_name","last_name","date_of_birth","sex","phone_number",
        "email","address_line_1","address_line_2","city","state","zip_code",
        "insurance_provider","insurance_member_id","preferred_language",
        "emergency_contact_name","emergency_contact_phone",
    ]
    for field in ALLOWED:
        if field in data:
            value = data[field]
            if field == "phone_number" or field == "emergency_contact_phone":
                value = re.sub(r"\D", "", value) if value else value
            if field == "state" and value:
                value = value.upper()
            setattr(p, field, value)

    p.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    logger.info("PATIENT UPDATED: %s", p.to_dict())
    return ok(p.to_dict())


@patients_bp.route("/patients/<patient_id>", methods=["DELETE"])
def delete_patient(patient_id):
    p = Patient.query.filter_by(patient_id=patient_id).filter(Patient.deleted_at.is_(None)).first()
    if not p:
        return err("Patient not found.", 404)
    p.deleted_at = datetime.now(timezone.utc)
    db.session.commit()
    return ok({"message": f"Patient {patient_id} soft-deleted."})


# ─────────────────────────────────────────────
# Blueprint: /vapi  (webhook from Vapi.ai)
# ─────────────────────────────────────────────
vapi_bp = Blueprint("vapi", __name__)


@vapi_bp.route("/vapi/save-patient", methods=["POST"])
def vapi_save_patient():
    """
    Called by Vapi tool-call when the agent has confirmed all data with caller.
    Vapi sends:  { "message": { "toolCallList": [{ "function": { "arguments": {...} } }] } }
    We extract the arguments dict and save to DB.
    """
    body = request.get_json(silent=True) or {}
    logger.info("VAPI WEBHOOK RECEIVED: %s", body)

    # Extract arguments from Vapi tool-call structure
    try:
        tool_calls = body["message"]["toolCallList"]
        data = tool_calls[0]["function"]["arguments"]
        tool_call_id = tool_calls[0]["id"]
    except (KeyError, IndexError, TypeError):
        return jsonify({"error": "Invalid Vapi payload."}), 400

    errors = validate_patient_data(data)
    if errors:
        return jsonify({
            "results": [{
                "toolCallId": tool_call_id,
                "result": f"Validation failed: {'; '.join(errors)}"
            }]
        }), 200  # Always 200 to Vapi; error is in the result

    # Duplicate check
    phone_digits = re.sub(r"\D", "", data.get("phone_number", ""))
    existing = Patient.query.filter_by(phone_number=phone_digits).filter(Patient.deleted_at.is_(None)).first()
    if existing:
        return jsonify({
            "results": [{
                "toolCallId": tool_call_id,
                "result": f"DUPLICATE:{existing.first_name}:{existing.last_name}:{existing.patient_id}"
            }]
        }), 200

    p = Patient(
        first_name      = data["first_name"].strip(),
        last_name       = data["last_name"].strip(),
        date_of_birth   = data["date_of_birth"],
        sex             = data["sex"],
        phone_number    = phone_digits,
        email           = data.get("email"),
        address_line_1  = data["address_line_1"].strip(),
        address_line_2  = data.get("address_line_2"),
        city            = data["city"].strip(),
        state           = data["state"].upper(),
        zip_code        = data["zip_code"],
        insurance_provider   = data.get("insurance_provider"),
        insurance_member_id  = data.get("insurance_member_id"),
        preferred_language   = data.get("preferred_language", "English"),
        emergency_contact_name  = data.get("emergency_contact_name"),
        emergency_contact_phone = re.sub(r"\D", "", data["emergency_contact_phone"])
                                  if data.get("emergency_contact_phone") else None,
    )
    db.session.add(p)
    db.session.commit()

    logger.info("PATIENT SAVED VIA VAPI: %s", p.to_dict())

    return jsonify({
        "results": [{
            "toolCallId": tool_call_id,
            "result": f"SUCCESS:{p.patient_id}"
        }]
    }), 200


@vapi_bp.route("/vapi/lookup-patient", methods=["POST"])
def vapi_lookup_patient():
    """
    Called by Vapi to check if a phone number already exists in the DB.
    """
    body = request.get_json(silent=True) or {}
    try:
        tool_calls = body["message"]["toolCallList"]
        args = tool_calls[0]["function"]["arguments"]
        tool_call_id = tool_calls[0]["id"]
    except (KeyError, IndexError, TypeError):
        return jsonify({"error": "Invalid payload."}), 400

    phone_digits = re.sub(r"\D", "", args.get("phone_number", ""))
    existing = Patient.query.filter_by(phone_number=phone_digits).filter(Patient.deleted_at.is_(None)).first()

    if existing:
        result = f"FOUND:{existing.first_name}:{existing.last_name}:{existing.patient_id}"
    else:
        result = "NOT_FOUND"

    return jsonify({
        "results": [{"toolCallId": tool_call_id, "result": result}]
    }), 200


# ─────────────────────────────────────────────
# Blueprint: /appointments
# ─────────────────────────────────────────────
from .database import Appointment

appointments_bp = Blueprint("appointments", __name__)

VALID_APPOINTMENT_TYPES = [
    "General Checkup",
    "Follow-up Visit",
    "Specialist Consultation",
    "Vaccination",
    "Lab Work",
    "Physical Therapy",
    "Mental Health",
    "Dental",
    "Vision",
    "Other"
]

MOCK_PROVIDERS = [
    "Dr. Sarah Johnson",
    "Dr. Michael Chen",
    "Dr. Emily Rodriguez",
    "Dr. James Williams",
    "Dr. Amanda Foster"
]

MOCK_AVAILABLE_SLOTS = [
    {"date": "04/07/2026", "time": "09:00 AM"},
    {"date": "04/07/2026", "time": "10:30 AM"},
    {"date": "04/08/2026", "time": "02:00 PM"},
    {"date": "04/09/2026", "time": "11:00 AM"},
    {"date": "04/10/2026", "time": "03:30 PM"},
    {"date": "04/11/2026", "time": "09:30 AM"},
]


@appointments_bp.route("/appointments", methods=["GET"])
def list_appointments():
    patient_id = request.args.get("patient_id")
    q = Appointment.query
    if patient_id:
        q = q.filter_by(patient_id=patient_id)
    appointments = q.order_by(Appointment.appointment_date).all()
    return ok([a.to_dict() for a in appointments])


@appointments_bp.route("/appointments/slots", methods=["GET"])
def get_available_slots():
    """Return mock available appointment slots."""
    return ok({
        "slots": MOCK_AVAILABLE_SLOTS,
        "providers": MOCK_PROVIDERS,
        "appointment_types": VALID_APPOINTMENT_TYPES
    })


@appointments_bp.route("/appointments/<appointment_id>", methods=["GET"])
def get_appointment(appointment_id):
    a = Appointment.query.filter_by(appointment_id=appointment_id).first()
    if not a:
        return err("Appointment not found.", 404)
    return ok(a.to_dict())


@appointments_bp.route("/appointments", methods=["POST"])
def create_appointment():
    data = request.get_json(silent=True)
    if not data:
        return err("Request body must be JSON.", 400)

    required = ["patient_id", "appointment_date", "appointment_time", "appointment_type"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return err(f"Missing required fields: {', '.join(missing)}", 422)

    # Verify patient exists
    patient = Patient.query.filter_by(patient_id=data["patient_id"]).filter(
        Patient.deleted_at.is_(None)
    ).first()
    if not patient:
        return err("Patient not found.", 404)

    a = Appointment(
        patient_id       = data["patient_id"],
        appointment_date = data["appointment_date"],
        appointment_time = data["appointment_time"],
        appointment_type = data["appointment_type"],
        provider_name    = data.get("provider_name", MOCK_PROVIDERS[0]),
        notes            = data.get("notes"),
        status           = "scheduled"
    )
    db.session.add(a)
    db.session.commit()

    logger.info("APPOINTMENT SCHEDULED: %s", a.to_dict())
    return ok(a.to_dict(), 201)


@appointments_bp.route("/appointments/<appointment_id>", methods=["PUT"])
def update_appointment(appointment_id):
    a = Appointment.query.filter_by(appointment_id=appointment_id).first()
    if not a:
        return err("Appointment not found.", 404)

    data = request.get_json(silent=True) or {}
    for field in ["appointment_date", "appointment_time", "appointment_type", "provider_name", "notes", "status"]:
        if field in data:
            setattr(a, field, data[field])

    a.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return ok(a.to_dict())


@appointments_bp.route("/appointments/<appointment_id>/cancel", methods=["POST"])
def cancel_appointment(appointment_id):
    a = Appointment.query.filter_by(appointment_id=appointment_id).first()
    if not a:
        return err("Appointment not found.", 404)
    a.status = "cancelled"
    a.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return ok({"message": "Appointment cancelled.", "appointment": a.to_dict()})


# ── Vapi webhook for saving appointments ──────
@vapi_bp.route("/vapi/save-appointment", methods=["POST"])
def vapi_save_appointment():
    """
    Called by Vapi tool when the agent schedules an appointment after registration.
    """
    body = request.get_json(silent=True) or {}
    logger.info("VAPI APPOINTMENT WEBHOOK: %s", body)

    try:
        tool_calls  = body["message"]["toolCallList"]
        data        = tool_calls[0]["function"]["arguments"]
        tool_call_id = tool_calls[0]["id"]
    except (KeyError, IndexError, TypeError):
        return jsonify({"error": "Invalid Vapi payload."}), 400

    # Verify patient
    patient = Patient.query.filter_by(patient_id=data.get("patient_id")).filter(
        Patient.deleted_at.is_(None)
    ).first()
    if not patient:
        return jsonify({"results": [{"toolCallId": tool_call_id, "result": "ERROR: Patient not found."}]}), 200

    a = Appointment(
        patient_id       = data["patient_id"],
        appointment_date = data.get("appointment_date", MOCK_AVAILABLE_SLOTS[0]["date"]),
        appointment_time = data.get("appointment_time", MOCK_AVAILABLE_SLOTS[0]["time"]),
        appointment_type = data.get("appointment_type", "General Checkup"),
        provider_name    = data.get("provider_name", MOCK_PROVIDERS[0]),
        notes            = data.get("notes"),
        status           = "scheduled"
    )
    db.session.add(a)
    db.session.commit()

    logger.info("APPOINTMENT SAVED VIA VAPI: %s", a.to_dict())

    return jsonify({"results": [{
        "toolCallId": tool_call_id,
        "result": f"SUCCESS:{a.appointment_id}:{a.appointment_date}:{a.appointment_time}:{a.provider_name}"
    }]}), 200