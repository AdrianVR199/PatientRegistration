"""
API tests for the Patient Registration System.
Run with: pytest tests.py -v
"""

import pytest
import json
from app import create_app
from app.database import db as _db


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    test_app = create_app(test_config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with test_app.app_context():
        yield test_app


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture
def patient():
    return {
        "first_name": "John",
        "last_name": "Smith",
        "date_of_birth": "01/15/1980",
        "sex": "Male",
        "phone_number": "5550000100",
        "address_line_1": "123 Main Street",
        "city": "Chicago",
        "state": "IL",
        "zip_code": "60601"
    }


def post_patient(client, data):
    return client.post(
        "/patients",
        data=json.dumps(data),
        content_type="application/json"
    )


# ─────────────────────────────────────────────
# Create
# ─────────────────────────────────────────────

def test_create_patient_returns_201(client, patient):
    res = post_patient(client, patient)
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["first_name"] == "John"
    assert data["patient_id"] is not None


def test_response_has_data_and_error_keys(client, patient):
    patient["phone_number"] = "5550000001"
    res = post_patient(client, patient)
    body = res.get_json()
    assert "data" in body and "error" in body


def test_phone_stored_as_digits_only(client, patient):
    patient["phone_number"] = "(555) 000-0002"
    res = post_patient(client, patient)
    assert res.get_json()["data"]["phone_number"] == "5550000002"


def test_state_stored_uppercase(client, patient):
    patient["phone_number"] = "5550000003"
    patient["state"] = "il"
    res = post_patient(client, patient)
    assert res.get_json()["data"]["state"] == "IL"


def test_duplicate_phone_returns_duplicate_flag(client, patient):
    patient["phone_number"] = "5550000099"
    post_patient(client, patient)
    res = post_patient(client, patient)
    assert res.get_json().get("duplicate") is True


def test_missing_required_fields_returns_422(client):
    res = post_patient(client, {"first_name": "Only"})
    assert res.status_code == 422


# ─────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────

def test_future_date_of_birth_rejected(client, patient):
    patient["phone_number"] = "5550000010"
    patient["date_of_birth"] = "01/01/2099"
    assert post_patient(client, patient).status_code == 422


def test_short_phone_rejected(client, patient):
    patient["phone_number"] = "123"
    assert post_patient(client, patient).status_code == 422


def test_invalid_state_rejected(client, patient):
    patient["phone_number"] = "5550000011"
    patient["state"] = "XX"
    assert post_patient(client, patient).status_code == 422


def test_invalid_email_rejected(client, patient):
    patient["phone_number"] = "5550000012"
    patient["email"] = "not-an-email"
    assert post_patient(client, patient).status_code == 422


# ─────────────────────────────────────────────
# List & Get
# ─────────────────────────────────────────────

def test_list_patients_returns_200(client):
    res = client.get("/patients")
    assert res.status_code == 200
    assert isinstance(res.get_json()["data"], list)


def test_filter_by_last_name(client, patient):
    patient["phone_number"] = "5550000020"
    patient["last_name"] = "Unique"
    post_patient(client, patient)
    res = client.get("/patients?last_name=Unique")
    assert all("Unique" in p["last_name"] for p in res.get_json()["data"])


def test_get_patient_by_id(client, patient):
    patient["phone_number"] = "5550000021"
    pid = post_patient(client, patient).get_json()["data"]["patient_id"]
    res = client.get(f"/patients/{pid}")
    assert res.status_code == 200
    assert res.get_json()["data"]["patient_id"] == pid


def test_get_nonexistent_patient_returns_404(client):
    res = client.get("/patients/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404


# ─────────────────────────────────────────────
# Update
# ─────────────────────────────────────────────

def test_partial_update(client, patient):
    patient["phone_number"] = "5550000030"
    pid = post_patient(client, patient).get_json()["data"]["patient_id"]
    res = client.put(
        f"/patients/{pid}",
        data=json.dumps({"email": "updated@example.com"}),
        content_type="application/json"
    )
    assert res.status_code == 200
    assert res.get_json()["data"]["email"] == "updated@example.com"


def test_update_nonexistent_returns_404(client):
    res = client.put(
        "/patients/00000000-0000-0000-0000-000000000000",
        data=json.dumps({"city": "Nowhere"}),
        content_type="application/json"
    )
    assert res.status_code == 404


# ─────────────────────────────────────────────
# Delete
# ─────────────────────────────────────────────

def test_soft_delete_returns_200(client, patient):
    patient["phone_number"] = "5550000040"
    pid = post_patient(client, patient).get_json()["data"]["patient_id"]
    assert client.delete(f"/patients/{pid}").status_code == 200


def test_deleted_patient_not_in_list(client, patient):
    patient["phone_number"] = "5550000041"
    pid = post_patient(client, patient).get_json()["data"]["patient_id"]
    client.delete(f"/patients/{pid}")
    ids = [p["patient_id"] for p in client.get("/patients").get_json()["data"]]
    assert pid not in ids


def test_deleted_patient_returns_404_by_id(client, patient):
    patient["phone_number"] = "5550000042"
    pid = post_patient(client, patient).get_json()["data"]["patient_id"]
    client.delete(f"/patients/{pid}")
    assert client.get(f"/patients/{pid}").status_code == 404