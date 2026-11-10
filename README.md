# MediAssist

**MediAssist** is a multimodal, full-stack health-information assistant prototype. It combines a React and TypeScript client with a Python/FastAPI backend, LangChain-based model orchestration, retrieval-augmented generation (RAG) with FAISS, document text extraction, consent-gated health context, and operational telemetry.

> **Important:** MediAssist is an educational prototype—not a medical device, diagnostic system, or clinically validated triage service. It can produce incomplete or incorrect health information. Do not rely on it for emergencies, diagnosis, or treatment decisions. Do not enter real patient information into a development or unreviewed deployment.

![MediAssist system architecture](https://private-us-east-1.manuscdn.com/sessionFile/5ds5Y8nNX1LYYdt9l4YM91/sandbox/F74XPCWT0gufgKyPwYo8Nd-images_1794323893235_na1fn_L2hvbWUvdWJ1bnR1L21lZGlhc3Npc3QtY29tcGxldGUvbWVkaWFzc2lzdC9kb2NzL2FyY2hpdGVjdHVyZQ.png?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUvNWRzNVk4bk5YMUxZWWR0OWw0WU05MS9zYW5kYm94L0Y3NFhQQ1dUMGd1ZmdLeVB3WW84TmQtaW1hZ2VzXzE3OTQzMjM4OTMyMzVfbmExZm5fTDJodmJXVXZkV0oxYm5SMUwyMWxaR2xoYzNOcGMzUXRZMjl0Y0d4bGRHVXZiV1ZrYVdGemMybHpkQzlrYjJOekwyRnlZMmhwZEdWamRIVnlaUS5wbmciLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3OTYwODMyMDB9fX1dfQ__&Key-Pair-Id=K2QY5QTL8JSY6C&Signature=MEUCIQDRMfNYAsHqZrXqmc-iMjpVCUy4oroZT2rHCnBQkbuGgwIgSutkxi~QBQosa3jpb8qAfXbDiAM~IiW2Y9gK-D6tTWs_)

## Contents

- [Highlights](#highlights)
- [Architecture](#architecture)
- [Technology stack](#technology-stack)
- [Project structure](#project-structure)
- [Requirements](#requirements)
- [Setup and run](#setup-and-run)
- [Environment configuration](#environment-configuration)
- [Use the application](#use-the-application)
- [Retrieval evaluation](#retrieval-evaluation)
- [Operational metrics and rate limiting](#operational-metrics-and-rate-limiting)
- [Tests](#tests)
- [Safety, privacy, and known limitations](#safety-privacy-and-known-limitations)
- [Documentation](#documentation)

## Highlights

- **Multimodal input:** text chat, browser speech-to-text where supported, and PDF/image text extraction with a user review step.
- **RAG:** ingests curated PDF and JSON sources, splits them into 1,000-character chunks with 160-character overlap, creates Google embeddings, and stores/retrieves vectors with FAISS.
- **Two-stage retrieval experiment:** the latest local benchmark run used FAISS to retrieve 10 candidates and a cross-encoder to rerank them, passing the best four passages onward. Cross-encoder reranking is optional and requires its model package and implementation to be present in the local checkout.
- **LLM providers:** configurable Groq or Gemini chat models through LangChain. Gemini embeddings are used for FAISS indexing and query retrieval, including when Groq is selected for chat.
- **Consent-gated accounts and health context:** JWT authentication and a server-side check for current health-information consent protect chat, health-record, and document-extraction routes.
- **Transient document handling:** uploaded files are processed in memory. Extracted text is returned for user review and is sent to the chat model only if the user chooses to attach it to a question.
- **Optional web search:** a SERP API adapter can supplement generic health-information queries; it is disabled by default.
- **Operational visibility:** Prometheus-format metrics cover HTTP traffic and latency, model requests/tokens, FAISS retrieval, OCR, database operations, and rate-limit rejections.
- **Request limiting:** a basic in-process sliding-window limiter defaults to 10 requests per client per 60-second window.

## Architecture

The backend is a modular FastAPI application, not a microservice fleet. The high-level chat path is:

1. The client sends a question with its bearer token.
2. FastAPI authenticates the user and verifies current health-information consent.
3. The server saves the typed question and checks for emergency phrases before retrieval or model calls.
4. A context router determines whether curated medical sources or the user's saved health context are relevant.
5. FAISS retrieves passages from the curated knowledge base. When the optional reranker is enabled, a cross-encoder reorders a larger candidate pool and the best four are selected.
6. If enabled and eligible, generic non-personal queries may also receive supplemental web-search context.
7. LangChain assembles the prompt and invokes the configured Groq or Gemini model. The answer is stored and verified source metadata is returned separately.

See [the architecture overview](docs/ARCHITECTURE.md), [the API reference](docs/API.md), and the diagram source at [`docs/architecture.mmd`](docs/architecture.mmd).

## Technology stack

| Area | Technologies |
|---|---|
| Frontend | React 19, TypeScript, Vite, Axios, React Router, React Markdown |
| API | Python, FastAPI, Pydantic, Uvicorn |
| AI orchestration | LangChain, Groq and Google Gemini adapters |
| Retrieval | FAISS, Google Generative AI embeddings, recursive text splitting; optional cross-encoder reranking in the latest local build |
| Persistence | SQLAlchemy, Alembic, SQLite for local development, PostgreSQL supported |
| Documents | pypdf, Tesseract OCR, Pillow, Poppler for scanned PDFs; configured vision provider where applicable |
| Operations | Prometheus client, optional Prometheus/Grafana Compose stack |
| Tests | pytest, FastAPI TestClient, frontend TypeScript/Vite build and Oxlint |

## Project structure

```text
mediassist/
├── backend/
│   ├── app/
│   │   ├── routers/             # Authentication, consent, chat, health, documents
│   │   ├── services/            # LLM, safety, OCR, rate limiting, metrics
│   │   │   └── rag/              # Loading, chunking, embeddings, FAISS ingestion/retrieval
│   │   └── data/medical_knowledge/ # Curated starter PDF and JSON sources
│   ├── alembic/                 # Database migrations
│   ├── evaluation/              # Labeled retrieval questions/results (local outputs)
│   ├── scripts/                 # Retrieval evaluation and failure analysis
│   ├── tests/                   # Provider-independent backend tests
│   └── requirements.txt
├── frontend/                    # React/TypeScript application
├── docs/                        # Architecture, API, safety, and metrics guides
└── monitoring/                  # Optional Prometheus/Grafana configuration
```

## Requirements

- **Python 3.11 or 3.12** (Python 3.10 may produce Google-library support warnings)
- **Node.js 20 or newer** and npm
- A **Groq or Gemini API key** for chat generation
- A **Gemini API key** for FAISS embeddings and retrieval queries
- Tesseract OCR and Poppler for scanned-PDF/local OCR features
- Docker Compose only if you want the optional Prometheus/Grafana stack

On Ubuntu/Debian, install the common OCR utilities with:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
```

## Setup and run

The following commands are for local development. Open **two terminals**: one for the backend and one for the frontend.

### Windows PowerShell: backend

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks virtual-environment activation, allow it for the current window and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Edit `backend\.env` before starting the app. At minimum, set a unique `JWT_SECRET`, configure your chat provider, and add `GEMINI_API_KEY` for embeddings. Then run the database migrations, build the FAISS index, and start the API:

```powershell
alembic upgrade head
python -m app.services.rag.ingest_documents
uvicorn app.main:app --reload
```

Index ingestion may take time and makes embedding-provider requests. Run it again after replacing knowledge files or changing chunking settings.

### Windows PowerShell: frontend

In the second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open the Vite URL printed in the terminal, usually `http://localhost:5173`.

### macOS/Linux

Backend terminal:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env: set JWT_SECRET, the selected chat-provider key, and GEMINI_API_KEY.
alembic upgrade head
python -m app.services.rag.ingest_documents
uvicorn app.main:app --reload
```

Frontend terminal:

```bash
cd frontend
npm ci
npm run dev
```

### Local service URLs

- Frontend: usually `http://localhost:5173`
- API base: `http://localhost:8000/api/v1`
- FastAPI interactive docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`
- Prometheus metrics: `http://localhost:8000/metrics` when enabled

## Environment configuration

The complete templates are [`backend/.env.example`](backend/.env.example) and [`frontend/.env.example`](frontend/.env.example). Keep real secrets in local `.env` files only; never commit them.

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | Select `groq` or `gemini` for chat generation. |
| `GROQ_API_KEY`, `GROQ_MODEL` | Groq chat credentials and model ID. Select a model currently available to your account. |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Gemini chat credentials/model when Gemini is selected. `GEMINI_API_KEY` is also used for embeddings. |
| `GEMINI_EMBEDDING_MODEL` | Embedding model used to build and query the FAISS index. |
| `DATABASE_URL` | SQL database connection. The example defaults to local SQLite; PostgreSQL is supported. |
| `JWT_SECRET` | Signing secret for local access tokens. Use a unique random value of at least 32 characters; use a secret manager for deployment. |
| `ENABLE_WEB_SEARCH`, `SERP_API_KEY` | Optional external search. Search is disabled unless explicitly enabled. |
| `MAX_UPLOAD_BYTES`, `MAX_PDF_PAGES`, `MAX_IMAGE_PIXELS` | Document-extraction bounds; example defaults are 10 MB, 10 PDF pages, and 20 million image pixels. |
| `ENABLE_RATE_LIMIT`, `RATE_LIMIT_PER_MINUTE`, `RATE_LIMIT_WINDOW_SECONDS` | In-process request limit settings; example default is 10 requests per 60 seconds. |
| `METRICS_ENABLED` | Enable or disable the internal Prometheus scrape endpoint. Protect it from public access. |
| `VITE_API_BASE_URL` | Frontend API URL; defaults to `http://localhost:8000/api/v1`. |

Example local JWT secret generation in PowerShell:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Paste the generated value into `JWT_SECRET` in `backend\.env`. Do not put provider keys in the frontend environment file.

## Use the application

1. Register an account and sign in.
2. Review and accept the health-information consent to access protected features.
3. Start a conversation and ask a general health-information question.
4. Optionally upload a supported PDF or image. Review and edit the extracted text, then choose whether to attach it to a question.
5. Where supported, use browser speech recognition to place a transcript into the editable chat field; audio is not automatically submitted.
6. Review returned source references and treat the response as general information, not personal medical advice.

The API also provides account, consent, conversation, health-record, document-extraction, and health-check routes. See [`docs/API.md`](docs/API.md) or `http://localhost:8000/docs` for request schemas and details.

## Retrieval evaluation

MediAssist includes a JSONL-based evaluator for **retrieval quality**. It compares the returned FAISS chunk IDs against the relevant IDs in the labeled test set. It does not evaluate the correctness, safety, or clinical quality of generated answers.

The current 60-query test set is at [`backend/evaluation/questions.jsonl`](backend/evaluation/questions.jsonl). Its questions focus on a small set of topics from the exported encyclopedia passages (including caffeine, calcium-channel blockers, Campylobacter, and cancer), and each question currently has one labeled relevant chunk. Treat it as a development benchmark, not a representative clinical benchmark. Review and expand the labels/questions before publishing the metrics.

From `backend/` with the virtual environment active, run the ordinary FAISS baseline:

```powershell
python scripts/evaluate_retrieval.py --dataset evaluation/questions.jsonl --k 4 --output-csv evaluation/results.csv
```

Compare cutoffs with separate result files:

```powershell
python scripts/evaluate_retrieval.py --dataset evaluation/questions.jsonl --k 6 --output-csv evaluation/results_k6.csv
python scripts/evaluate_retrieval.py --dataset evaluation/questions.jsonl --k 10 --output-csv evaluation/results_k10.csv
```

For the **optional cross-encoder reranker** used in the latest local evaluation, install its dependency if it is not already included in your environment:

```powershell
python -m pip install sentence-transformers
```

Then use the supported local reranker integration to retrieve 10 FAISS candidates and score the reranked top four:

```powershell
python scripts/evaluate_retrieval.py --dataset evaluation/questions.jsonl --k 4 --candidate-k 10 --rerank --output-csv evaluation/results_rerank10_to4.csv
```

The first reranker model load may download model weights. Reranking can only promote candidates already in the initial FAISS pool; it cannot recover relevant chunks excluded from that pool. Benchmark consistently with the same index, labels, embedding model, and query set. Review the top-k results and label all genuinely answer-supporting passages, not merely the one initially selected as the target. See [`backend/scripts/README.md`](backend/scripts/README.md) and [`docs/OPERATIONS_METRICS.md`](docs/OPERATIONS_METRICS.md).

### Latest reported retrieval results

These are the results reported from the current 60-query local evaluation:

| Retrieval configuration | Precision | Recall | MRR |
|---|---:|---:|---:|
| FAISS top 4, no reranker | Precision@4 **15.8%** | Recall@4 **63.3%** | **0.5042** |
| FAISS top 6, no reranker | Precision@6 **12.2%** | Recall@6 **73.3%** | **0.5225** |
| FAISS top 10, no reranker | Precision@10 **7.8%** | Recall@10 **78.3%** | **0.5284** |
| FAISS top 10 → cross-encoder rerank → top 4 | Precision@4 **19.6%** | Recall@4 **78.3%** | **0.7472** |

The reranked top four retrieved the labeled target for 47 of 60 questions, compared with 38 of 60 for plain FAISS top four. Because each question has only one labeled relevant chunk, Precision@4 cannot exceed 25% under the current labels; the low precision partly reflects that label design. The dataset has not been clinically validated and the scores are **retrieval metrics only**. Do not present them as answer accuracy or evidence of medical safety.

To inspect missed queries, export the current chunk list and run the helper after copying it into your checkout:

```powershell
python scripts/evaluate_retrieval.py --export-chunks evaluation/chunks.csv
python scripts/analyze_retrieval_failures.py --results evaluation/results.csv --dataset evaluation/questions.jsonl --chunks evaluation/chunks.csv --output evaluation/failures_review.csv
```

The second command writes a review CSV with target and retrieved chunk previews. Read the actual passages before changing labels; a short preview may not include enough context to judge relevance.

## Operational metrics and rate limiting

With `METRICS_ENABLED=true`, the API exposes aggregate Prometheus text metrics at `GET /metrics`. The implemented instrumentation covers:

- HTTP request totals, status codes, latency, and in-progress requests
- Rate-limit rejections
- LLM attempts, latency, and provider-reported token counts when available
- FAISS search outcomes and latency
- OCR/document extraction outcomes and latency
- SQL statement outcomes and latency

The default limiter is **10 requests per 60 seconds per client identifier** (authenticated bearer-token hash or client IP). It is an in-process sliding window, so each application worker has its own state. It is not a shared, cluster-wide production limiter.

The metrics endpoint is unauthenticated by default. Do not expose it publicly; restrict access at the network, firewall, or reverse proxy. Prometheus and Grafana are optional; local Compose files and an example dashboard are in `monitoring/`. You can use `/metrics` directly for a basic check without Grafana. See [`docs/OPERATIONS_METRICS.md`](docs/OPERATIONS_METRICS.md) for metric names, calculations, alert examples, and scaling caveats.

## Tests

From `backend/` with the virtual environment active:

```powershell
python -m pytest -q
```

The latest checked backend suite in this project copy passed **37 tests**. Tests are designed not to call live model or search providers. To build the frontend:

```powershell
cd frontend
npm ci
npm run build
```

To lint the frontend source:

```powershell
npx oxlint src
```

OCR engines, provider credentials, FAISS index generation, and external API access require separate local verification.

## Safety, privacy, and known limitations

- MediAssist does not diagnose, prescribe, or determine whether a person is safe to wait. Its emergency phrase detector is a basic pattern-based safeguard, not validated triage; it may miss urgent language or over-trigger.
- The included medical sources are starter/sample material. One is an encyclopedia PDF; check its currentness, completeness, and redistribution rights. Replace it with permitted, reviewed, dated sources before sharing or deployment.
- The SQL database persists accounts, consent events, conversations, messages, and user-entered health context. Conversation deletion exists, but full account deletion and automated retention schedules are not implemented.
- Document uploads are not persisted by the extraction endpoint. However, if the user elects to send extracted text with a chat question, that text may be sent to the configured model provider. Review provider data handling before using sensitive information.
- The browser currently stores the access token in `localStorage`; this is suitable only as a prototype trade-off and is more exposed to successful script injection than an appropriately configured secure cookie design.
- The rate limiter and metrics registry are process-local. Use a shared limiter such as Redis and an appropriate multi-process metrics strategy before scaling to multiple workers/replicas.
- Web search is off by default. If enabled, query filters are not a guarantee of de-identification.
- No compliance certification, production security hardening, or clinical validation is claimed.

Read [`docs/SAFETY_PRIVACY.md`](docs/SAFETY_PRIVACY.md) before changing data flows or testing with sensitive information.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API reference](docs/API.md)
- [Safety and privacy notes](docs/SAFETY_PRIVACY.md)
- [Operational metrics guide](docs/OPERATIONS_METRICS.md)
- [Retrieval evaluation guide](backend/scripts/README.md)
- [Architecture diagram source](docs/architecture.mmd)
