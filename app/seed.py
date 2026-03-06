from .database import db, Patient


def seed_data():
    if Patient.query.count() > 0:
        return  

    patients = [
        Patient(
            first_name="Jane",
            last_name="Doe",
            date_of_birth="03/15/1985",
            sex="Female",
            phone_number="5551234567",
            email="jane.doe@example.com",
            address_line_1="123 Main Street",
            address_line_2="Apt 4B",
            city="New York",
            state="NY",
            zip_code="10001",
            insurance_provider="Blue Cross Blue Shield",
            insurance_member_id="BCBS-987654",
            preferred_language="English",
            emergency_contact_name="John Doe",
            emergency_contact_phone="5559876543",
        ),
        Patient(
            first_name="Carlos",
            last_name="Rivera",
            date_of_birth="07/22/1990",
            sex="Male",
            phone_number="5557654321",
            email="carlos.rivera@example.com",
            address_line_1="456 Oak Avenue",
            city="Los Angeles",
            state="CA",
            zip_code="90001",
            preferred_language="Spanish",
        ),
    ]

    for p in patients:
        db.session.add(p)
    db.session.commit()
    print("✅ Seed data inserted.")
