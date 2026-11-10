# MediAssist

MediAssist is an educational prototype for general health information. It combines a React/TypeScript client, FastAPI backend, consent-gated health records, LangChain-based Groq/Gemini model integration, FAISS retrieval, OCR/vision, and Prometheus-compatible operational monitoring.

> **Safety and deployment:** This is not a medical device or clinically validated triage system. Do not use it for emergencies or real patient data without appropriate clinical, privacy, security, provider, and jurisdiction-specific review. The attached archive had credential-like values in its environment example; this cleaned project has placeholders. Rotate any credentials that were present in the uploaded archive.

## What is included

- React client for registration/login, chat, health records, consent, and user-reviewed OCR text.
- FastAPI API with JWT auth, SQLAlchemy/Alembic, and current-consent checks.
- LangChain chat through Groq or Gemini, curated FAISS retrieval, optional SERP search (off by default), and emergency phrase routing.
- PDF/image extraction using text parsing, local OCR, or configured vision providers; file bytes are processed transiently.
- In-process request rate limiting and privacy-conscious Prometheus counters/histograms for HTTP, model calls/tokens, FAISS, OCR, SQL operations, and limiter rejections.
- Prometheus scrape configuration, starter alert rules, and an automatically provisioned Grafana dashboard under `monitoring/`.

See [architecture](docs/ARCHITECTURE.md), [API reference](docs/API.md), [safety/privacy](docs/SAFETY_PRIVACY.md), and [operational metrics guide](docs/OPERATIONS_METRICS.md).

## Requirements

Python 3.11 or 3.12, Node.js 20+ and npm. Tesseract and Poppler are recommended for local OCR/scanned PDF support. Docker Compose is optional for Prometheus/Grafana. Configure either a Groq or Gemini API key; Gemini is also used for the configured FAISS embeddings.

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
```

## Run the backend

```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell, copy the template with `Copy-Item .env.example .env`. Edit `backend/.env`: set a unique `JWT_SECRET` and the provider key you plan to use (`GROQ_API_KEY` or `GEMINI_API_KEY`). For Groq, keep `LLM_PROVIDER=groq` and set `GROQ_MODEL=openai/gpt-oss-120b` (or another model currently enabled for your account). Existing `.env` files are not overwritten by copying the template; if yours still says `llama-3.3-70b-versatile`, replace that line manually and restart the API. Keep actual provider secrets in this backend file only. The sample config defaults to SQLite. To use PostgreSQL, set `DATABASE_URL` to your own database connection string.

If Groq still returns `model_not_found`, check which models your API key can access and select one of the returned IDs:

```powershell
(Invoke-RestMethod -Headers @{ Authorization = "Bearer $env:GROQ_API_KEY" } -Uri "https://api.groq.com/openai/v1/models").data.id
```

Run migrations, optionally build the curated FAISS index (requires Gemini embeddings), then start FastAPI:

```bash
alembic upgrade head
python -m app.services.rag.ingest_documents
uvicorn app.main:app --reload
```

The API base is `http://localhost:8000/api/v1`; interactive API docs are at `http://localhost:8000/docs`. In local development, metrics are exposed at `http://localhost:8000/metrics` unless `METRICS_ENABLED=false`.

## Run the frontend

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open the local Vite URL (usually `http://localhost:5173`). The default API URL points at the local backend. To override it, copy `frontend/.env.example` to `.env.local` and set `VITE_API_BASE_URL`.

## Run Prometheus and Grafana

Start the API first with `METRICS_ENABLED=true`, then in a terminal with Docker Compose:

```bash
cd monitoring
cp .env.example .env
# Edit .env and set a strong GRAFANA_ADMIN_PASSWORD.
docker compose up -d
```

Grafana is bound to `127.0.0.1:3000` and Prometheus to `127.0.0.1:9090`. The compose setup provisions the Prometheus datasource and MediAssist dashboard. The sample Prometheus configuration scrapes `host.docker.internal:8000`; for this Docker setup, run the local API with `uvicorn app.main:app --host 0.0.0.0` and use a host firewall so the development service is reachable only where intended. See [metrics setup and PromQL examples](docs/OPERATIONS_METRICS.md) for calculations, alerts, privacy constraints, and troubleshooting. Restrict `/metrics` to trusted internal monitoring in any shared/deployed environment.

## Tests and build checks

From `backend/` with its virtual environment active:

```bash
pytest -q
```

From `frontend/`:

```bash
npm ci
npm run build
```

The backend tests are designed not to call live model/search providers. OCR engine presence and provider credentials need separate local verification.

## Data handling and limitations

The SQL database stores user accounts, consent, chat, and health records. The FAISS index is for curated sources only. Uploaded files are read in memory; extracted text is returned for user review and sent to a model only if the user chooses to attach it to a message. Provider data handling depends on the selected vendor and configuration.

The rate limiter and metrics registry are in process. They do not coordinate across multiple workers/replicas; deploy Redis-backed rate limiting and a suitable multi-process metrics collection strategy before scaling horizontally. Metrics intentionally do not include prompts, OCR text, filenames, emails, IP addresses, or user IDs. Provider-reported token metrics may be incomplete, and estimated cost must be calculated using current provider prices. Do not treat emergency phrase counts or telemetry as evidence of clinical performance.

The current implementation does not provide account deletion, automated data retention, production deployment hardening, or clinical quality validation. Sample medical knowledge and external model output require review; check source permissions before redistribution or deployment.
