# 🏥 Voice AI Patient Registration System

A voice-based AI agent accessible via a real US phone number that collects patient demographic information through natural conversation, persists data to a SQLite database, and exposes it through a REST API with a web dashboard.

## 📞 Live Demo

| Item | Value |
|------|-------|
| **Phone Number** | *(add your Vapi number here)* |
| **API Base URL** | https://patientregistration-w1e2.onrender.com |
| **Dashboard** | https://patientregistration-w1e2.onrender.com/ |
| **API Patients** | https://patientregistration-w1e2.onrender.com/patients |

---

## 🏗️ Architecture

```
Caller ──► Vapi.ai (STT + TTS + GPT-4o)
                │
                │  Tool calls (HTTP POST)
                ▼
         Flask REST API  ◄──► SQLite Database
                │
                ▼
         Dashboard (Tailwind CSS)
```

| Layer | Technology | Why |
|-------|-----------|-----|
| **Telephony + Voice** | [Vapi.ai](https://vapi.ai) | Abstracts phone number, STT, TTS, and LLM orchestration. Fastest path to a working voice agent. |
| **LLM** | OpenAI GPT-4o (via Vapi) | Best conversational quality for real-time phone calls. |
| **Backend API** | Python + Flask | Simple, readable, great ecosystem for rapid development. |
| **Database** | SQLite | Zero-config, file-based persistence. Smart trade-off under time pressure. |
| **Dashboard** | Tailwind CSS + Flask Templates | Served directly from Flask to avoid a separate frontend project. Intentional trade-off for this scope. |
| **Deployment** | Railway / Render | Git-push deploys, free tier available. |

---

## 📁 Project Structure

```
patient-registration/
│
├── run.py                  # Entry point
├── requirements.txt        # Dependencies
├── Procfile                # Railway/Render: "web: gunicorn run:app"
├── .env.example            # Environment variables template
├── .gitignore              # Excludes .env, venv, instance/, *.db
│
├── vapi_prompt.md          # Voice agent system prompt
├── vapi_tools.json         # Vapi tool definitions
├── tests.py                # 19 automated API tests (isolated in-memory DB)
│
└── app/
    ├── __init__.py         # App factory — accepts test_config to isolate tests
    ├── database.py         # Patient model + SQLAlchemy
    ├── routes.py           # REST API + Vapi webhooks + dashboard route
    ├── validators.py       # Field validation logic
    ├── seed.py             # 2 demo patients on startup (skipped during tests)
    └── templates/
        └── dashboard.html  # Patient registry dashboard (Tailwind CSS)
```

---

## 🚀 Setup Instructions

### 1. Clone and install

```bash
git clone <your-repo-url>
cd patient-registration

# Create virtual environment
py -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Run locally

```bash
py run.py
```

- **Dashboard:** http://localhost:5000
- **API:** http://localhost:5000/patients

### 3. Run tests

Tests run against an isolated in-memory SQLite database — they never touch the real `patients.db`.

```bash
pytest tests.py -v
```

Expected output: **19 passed**

### 4. Reset the database

If you need a clean slate, delete the database file and restart:

```bash
# Delete the file
del instance\patients.db   # Windows
rm instance/patients.db    # Mac/Linux

# Restart the server — seed data is recreated automatically
py run.py
```

---

## ☁️ Deployment (Railway)

1. Push code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo — Railway auto-detects the `Procfile`
4. Add environment variable: `SECRET_KEY=your-random-string`
5. Copy the public URL (e.g. `https://patient-api.up.railway.app`)
6. Update `vapi_tools.json` with your Railway URL

> **SQLite on Railway:** Data persists between restarts but not between redeploys. For production, swap to PostgreSQL (Railway offers a free addon). This is a known trade-off documented below.

---

## 📋 API Reference

All responses use envelope: `{ "data": {...}, "error": null }`

| Method | Endpoint | Description |
|--------|---------|-------------|
| `GET` | `/` | Web dashboard |
| `GET` | `/patients` | List all patients. Supports `?last_name=`, `?date_of_birth=`, `?phone_number=` |
| `GET` | `/patients/:id` | Get single patient by UUID |
| `POST` | `/patients` | Create new patient |
| `PUT` | `/patients/:id` | Partial update |
| `DELETE` | `/patients/:id` | Soft delete (sets `deleted_at`) |
| `POST` | `/vapi/save-patient` | Vapi webhook: saves confirmed patient |
| `POST` | `/vapi/lookup-patient` | Vapi webhook: checks for duplicate phone |

### HTTP Status Codes
- `200` OK, `201` Created
- `400` Bad request, `404` Not found, `422` Validation error, `500` Server error

---

## 📱 Vapi.ai Setup

### Step 1: Create account
Go to [vapi.ai](https://vapi.ai) and sign up (free tier available).

### Step 2: Create Assistant
1. Dashboard → **Assistants** → **Create Assistant**
2. Name: `Patient Registration Agent`
3. **System Prompt**: paste contents of `vapi_prompt.md`
4. **Model**: GPT-4o
5. **Voice**: Choose a natural-sounding voice

### Step 3: Add Tools
1. Go to **Tools** in the assistant settings
2. Add two tools from `vapi_tools.json`:
   - `lookup_patient` → `https://YOUR_BACKEND_URL/vapi/lookup-patient`
   - `save_patient` → `https://YOUR_BACKEND_URL/vapi/save-patient`

### Step 4: Get a Phone Number
1. Dashboard → **Phone Numbers** → **Buy Number** (~$2/month)
2. Assign it to your assistant

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FLASK_ENV` | No | `production` or `development` |
| `SECRET_KEY` | Yes | Random secret for Flask |

---

## 🔒 Security
- No API keys hardcoded — all via environment variables
- Server-side validation on all inputs (never relying solely on the voice agent)
- Soft deletes only — no hard data destruction
- Phone numbers normalized to digits only, state uppercased automatically

---

## ⚠️ Known Trade-offs & Limitations

1. **SQLite on Railway**: Data may not persist across redeploys. For production, swap to PostgreSQL.

2. **Dashboard served from Flask**: In a production system the frontend would be a separate React app. Intentional trade-off to avoid unnecessary complexity within the time constraint.

3. **No API authentication**: The REST API has no auth layer. In production, add API key middleware or OAuth.

4. **No call transcripts**: Vapi supports call recording as an add-on. Not implemented in this version.

5. **Test isolation**: Tests use an in-memory SQLite database via `test_config` passed to the app factory. This ensures tests never affect real data.

---

## 🗺️ Next Steps

- [ ] Swap SQLite for PostgreSQL for true persistence at scale
- [ ] Add JWT/API key authentication to REST endpoints
- [ ] Store call transcripts linked to patient records
- [ ] Separate the dashboard into a standalone React frontend
- [ ] Add appointment scheduling flow after registration
- [ ] HIPAA-compliant hosting if used with real patient data

---

## 🧠 Prompt Engineering Notes

The system prompt (`vapi_prompt.md`) is designed around these principles:

1. **Structured 5-step flow** — prevents the agent from skipping confirmation or saving without consent
2. **Conversational language** — "your birthday" instead of "date_of_birth"
3. **Inline validation** — invalid data is handled naturally, not with error codes
4. **Confirmation before save** — agent always reads back all data before calling `save_patient`
5. **Duplicate detection** — phone number lookup at the start of every call
6. **Spanish support** — single trigger switches the agent's language for the entire call
