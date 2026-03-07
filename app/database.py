from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import uuid

db = SQLAlchemy()


def generate_uuid():
    return str(uuid.uuid4())


def now_utc():
    return datetime.now(timezone.utc)


class Patient(db.Model):
    __tablename__ = "patients"

    patient_id   = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    first_name   = db.Column(db.String(50),  nullable=False)
    last_name    = db.Column(db.String(50),  nullable=False)
    date_of_birth= db.Column(db.String(10),  nullable=False)   
    sex          = db.Column(db.String(20),  nullable=False)   
    phone_number = db.Column(db.String(20),  nullable=False)
    email        = db.Column(db.String(120), nullable=True)
    address_line_1 = db.Column(db.String(200), nullable=False)
    address_line_2 = db.Column(db.String(200), nullable=True)
    city         = db.Column(db.String(100), nullable=False)
    state        = db.Column(db.String(2),   nullable=False)
    zip_code     = db.Column(db.String(10),  nullable=False)
    insurance_provider  = db.Column(db.String(100), nullable=True)
    insurance_member_id = db.Column(db.String(100), nullable=True)
    preferred_language  = db.Column(db.String(50),  nullable=True, default="English")
    emergency_contact_name  = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(20),  nullable=True)
    created_at   = db.Column(db.DateTime(timezone=True), default=now_utc)
    updated_at   = db.Column(db.DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    deleted_at   = db.Column(db.DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "patient_id":   self.patient_id,
            "first_name":   self.first_name,
            "last_name":    self.last_name,
            "date_of_birth":self.date_of_birth,
            "sex":          self.sex,
            "phone_number": self.phone_number,
            "email":        self.email,
            "address_line_1": self.address_line_1,
            "address_line_2": self.address_line_2,
            "city":         self.city,
            "state":        self.state,
            "zip_code":     self.zip_code,
            "insurance_provider":   self.insurance_provider,
            "insurance_member_id":  self.insurance_member_id,
            "preferred_language":   self.preferred_language,
            "emergency_contact_name":  self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "created_at":   self.created_at.isoformat() if self.created_at else None,
            "updated_at":   self.updated_at.isoformat() if self.updated_at else None,
        }


class Appointment(db.Model):
    __tablename__ = "appointments"

    appointment_id   = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id       = db.Column(db.String(36), db.ForeignKey("patients.patient_id"), nullable=False)
    appointment_date = db.Column(db.String(10),  nullable=False)   # MM/DD/YYYY
    appointment_time = db.Column(db.String(8),   nullable=False)   # HH:MM AM/PM
    appointment_type = db.Column(db.String(100), nullable=False)   # e.g. "General Checkup"
    provider_name    = db.Column(db.String(100), nullable=True)    # e.g. "Dr. Smith"
    notes            = db.Column(db.String(500), nullable=True)
    status           = db.Column(db.String(20),  nullable=False, default="scheduled")  # scheduled/cancelled/completed
    created_at       = db.Column(db.DateTime(timezone=True), default=now_utc)
    updated_at       = db.Column(db.DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    patient = db.relationship("Patient", backref="appointments")

    def to_dict(self):
        return {
            "appointment_id":   self.appointment_id,
            "patient_id":       self.patient_id,
            "appointment_date": self.appointment_date,
            "appointment_time": self.appointment_time,
            "appointment_type": self.appointment_type,
            "provider_name":    self.provider_name,
            "notes":            self.notes,
            "status":           self.status,
            "created_at":       self.created_at.isoformat() if self.created_at else None,
            "updated_at":       self.updated_at.isoformat() if self.updated_at else None,
        }