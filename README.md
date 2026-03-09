# 🏥 Voice AI Patient Registration System

A voice-based AI agent accessible via a real US phone number that collects patient demographic information through natural conversation, persists data to a PostgreSQL database, and exposes it through a REST API with a web dashboard.

## 📞 Live Demo

| Item | Value |
|------|-------|
| **Phone Number** | +1 (530) 584-0276 |
| **API Base URL** | https://patientregistration-w1e2.onrender.com |
| **Dashboard** | https://patientregistration-w1e2.onrender.com/ |
| **API Patients** | https://patientregistration-w1e2.onrender.com/patients |

> **To test:** Call +1 (530) 584-0276 and speak naturally with Alison, the registration agent. Say "Hablo español" at any point to switch to Spanish.

---

## 🏗️ Architecture

```
Caller ──► Vapi.ai (STT + TTS + GPT-4.1)
                │
                │  Tool calls (HTTP POST)
                ▼
         Flask REST API  ◄──► PostgreSQL Database (Render)
                │
                ▼
         Dashboard (Tailwind CSS)
```

| Layer | Technology | Why |
|-------|-----------|-----|
| **Telephony + Voice** | [Vapi.ai](https://vapi.ai) | Abstracts phone number, STT, TTS, and LLM orchestration. Fastest path to a working voice agent. |
| **LLM** | OpenAI GPT-4.1 (via Vapi) | Best conversational quality for real-time phone calls. |
| **Backend API** | Python + Flask | Simple, readable, great ecosystem for rapid development. |
| **Database** | PostgreSQL (Render) | Persistent, production-grade. Data survives redeploys and restarts. |
| **Dashboard** | Tailwind CSS + Flask Templates | Served directly from Flask to avoid a separate frontend project. Intentional trade-off for this scope. |
| **Deployment** | Render | Git-push deploys, free tier available. Auto-deploys on every push to main. |

---

## 📁 Project Structure

```
patient-registration/
│
├── run.py                  # Entry point
├── requirements.txt        # Dependencies
├── Procfile                # Render: "web: gunicorn run:app"
├── .env.example            # Environment variables template
├── .gitignore              # Excludes .env, venv, instance/, *.db
│
├── vapi_prompt.md          # Voice agent system prompt
├── vapi_tools.json         # Vapi tool definitions (3 tools)
├── tests.py                # 19 automated API tests (isolated in-memory DB)
│
└── app/
    ├── __init__.py         # App factory — accepts test_config to isolate tests
    ├── database.py         # Patient + Appointment models + SQLAlchemy
    ├── routes.py           # REST API + Vapi webhooks + dashboard route
    ├── validators.py       # Field validation logic
    ├── seed.py             # 2 demo patients on startup (skipped during tests)
    └── templates/
        └── dashboard.html  # Responsive patient registry dashboard (Tailwind CSS)
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

> Locally uses SQLite (zero config). PostgreSQL is used in production via `DATABASE_URL` environment variable.

### 3. Run tests

Tests run against an isolated in-memory SQLite database — they never touch the real database.

```bash
pytest tests.py -v
```

Expected output: **19 passed**

### 4. Reset the database

```bash
# Delete the local SQLite file
del instance\patients.db   # Windows
rm instance/patients.db    # Mac/Linux

# Restart — seed data is recreated automatically
py run.py
```

---

## ☁️ Deployment (Render)

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New → Web Service → Connect GitHub repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn run:app`
5. Add environment variables:
   - `SECRET_KEY=your-random-string`
   - `DATABASE_URL=your-postgresql-url` (from Render PostgreSQL addon)
6. Create a PostgreSQL database in Render and link it via `DATABASE_URL`

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
| `GET` | `/appointments` | List appointments. Supports `?patient_id=` |
| `GET` | `/appointments/slots` | Get available mock appointment slots |
| `POST` | `/appointments` | Create appointment |
| `PUT` | `/appointments/:id` | Update appointment |
| `POST` | `/appointments/:id/cancel` | Cancel appointment |
| `POST` | `/vapi/save-patient` | Vapi webhook: saves confirmed patient |
| `POST` | `/vapi/lookup-patient` | Vapi webhook: checks for duplicate phone |
| `POST` | `/vapi/save-appointment` | Vapi webhook: saves scheduled appointment |

### HTTP Status Codes
- `200` OK, `201` Created
- `400` Bad request, `404` Not found, `422` Validation error, `500` Server error

---

## 📱 Vapi.ai Configuration

### Assistant
- **Name:** Patient Registration Agent
- **Voice:** Emily (ElevenLabs, eleven_multilingual_v2)
- **Model:** GPT-4.1
- **System Prompt:** See `vapi_prompt.md`
- **Transcriber:** Google Multilingual (supports English + Spanish)

### Tools (3)
| Tool | Endpoint |
|------|----------|
| `lookup_patient` | `POST /vapi/lookup-patient` |
| `save_patient` | `POST /vapi/save-patient` |
| `save_appointment` | `POST /vapi/save-appointment` |

### Phone Number
- **Provider:** Vapi (free tier)
- **Number:** +1 (530) 584-0276
- **Inbound:** Patient Registration Agent

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Random secret for Flask |
| `DATABASE_URL` | No | PostgreSQL URL (Render). Falls back to SQLite locally. |

---

## 🔒 Security
- No API keys hardcoded — all via environment variables
- Server-side validation on all inputs (never relying solely on the voice agent)
- Soft deletes only — no hard data destruction
- Phone numbers normalized to digits only, state uppercased automatically

---

## ⚠️ Known Trade-offs & Limitations

1. **SQLite locally, PostgreSQL in production** — Local dev uses SQLite for zero-config simplicity. Render uses PostgreSQL for true persistence. The switch is handled automatically via `DATABASE_URL`.

2. **Dashboard served from Flask** — In a production system the frontend would be a separate React app. Intentional trade-off to avoid unnecessary complexity within the time constraint.

3. **No API authentication** — The REST API has no auth layer. In production, add API key middleware or OAuth.

4. **Mock appointment slots** — Appointment availability is hardcoded mock data. In production this would connect to a real scheduling system.

5. **Render free tier cold starts** — The server sleeps after 15 min of inactivity. First request after sleep takes ~30 seconds. Open the dashboard before calling to wake the server.

6. **Test isolation** — Tests use an in-memory SQLite database via `test_config` passed to the app factory. This ensures tests never affect real data.

---

## 🎯 Bonus Features Implemented

| Bonus | Implementation |
|-------|---------------|
| ✅ Duplicate Detection | `lookup_patient` tool called at start of every call — recognizes returning callers by phone number |
| ✅ Appointment Scheduling | Full appointment flow after registration with mock slots and providers |
| ✅ Multi-language Support | Google Multilingual transcriber + prompt instruction — say "Hablo español" to switch |
| ✅ Call Summary | Vapi Summary + Structured Outputs (Call Summary, Success Evaluation, Appointment Booked) |
| ✅ Dashboard | Responsive Tailwind CSS dashboard with search, filters, patient modal and appointment history |
| ✅ Automated Tests | 19 pytest tests covering all endpoints with in-memory DB isolation |

---

## 🗺️ Next Steps

- [ ] Add JWT/API key authentication to REST endpoints
- [ ] Store full call transcripts linked to patient records in DB
- [ ] Separate the dashboard into a standalone React frontend
- [ ] Real appointment scheduling integration
- [ ] HIPAA-compliant hosting if used with real patient data
- [ ] Pagination for large patient lists

---

## 🧠 Prompt Engineering Notes

The system prompt (`vapi_prompt.md`) is designed around these principles:

1. **Structured 6-step flow** — prevents the agent from skipping confirmation or saving without consent
2. **Conversational language** — "your birthday" instead of "date_of_birth"
3. **Inline validation** — invalid data is handled naturally, not with error codes
4. **Confirmation before save** — agent always reads back all data before calling `save_patient`
5. **Duplicate detection** — phone number lookup at the start of every call
6. **Spanish support** — single trigger switches the agent's language for the entire call
7. **Appointment scheduling** — offered after successful registration as Step 6