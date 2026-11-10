# MediAssist Architecture

## Status and scope

This document describes the code in this repository after the current implementation. It is not a production deployment diagram. The backend is a modular FastAPI application rather than a set of microservices. SQLite is used by default in local development; PostgreSQL is supported through `DATABASE_URL`.

## Components

- **React + TypeScript client:** login/registration, consent, chat, health records, attachment review, and optional browser speech recognition.
- **FastAPI API:** validates requests, checks JWT identity, applies consent requirements, and routes chat, health-record, consent, authentication, and document-extraction operations.
- **SQLAlchemy/PostgreSQL or SQLite:** accounts, consent events, conversations, messages, and user-entered health context.
- **Safety/context services:** basic emergency phrase detection runs before model generation; a context router selects whether curated medical retrieval and personal health data are relevant.
- **LangChain LCEL:** formats a safety-constrained prompt with up to ten prior messages, the question, optional user-reviewed extracted text, narrowly selected health context, and retrieved passages.
- **Model adapters:** invoke configured Groq (`ChatGroq`) or Gemini (`ChatGoogleGenerativeAI`) providers. Provider API keys are configured server-side; the selected provider's response usage metadata is collected when available.
- **Knowledge ingestion:** reads local PDF and JSON knowledge files, uses LangChain recursive text splitting and Google embeddings, then creates a persistent FAISS index.
- **Optional SerpAPI adapter:** disabled by default. It only runs for eligible generic medical questions, rejects several obvious personal/identifier patterns, and labels results as supplemental web material.
- **Document extraction:** reads one PDF or raster image in memory, validates type and size, and uses text extraction, local OCR, or configured vision adapters. It returns extracted content for review, then discards the upload bytes.
- **Browser voice input:** uses SpeechRecognition/webkitSpeechRecognition when available and places the transcript in the editable text box; it does not auto-submit or send audio to the backend.
- **Operational telemetry:** a Prometheus client registry tracks API counters/histograms, in-flight requests, limiter rejections, model calls/tokens, FAISS, OCR, and SQL timings. Prometheus/Grafana example deployment files live under `monitoring/`.

## System diagram

See [`architecture.png`](architecture.png) and source [`architecture.mmd`](architecture.mmd).

## Text-chat flow

1. The client submits a question using a bearer token.
2. The API validates the token and checks the latest `health_information` consent record and configured consent version.
3. The chat handler verifies that the requested conversation belongs to the authenticated user and saves the question text.
4. Emergency phrase detection runs before RAG, external search, or model calls. A detected phrase returns the fixed emergency message.
5. For other questions, the context router decides whether medical knowledge or the user's saved health profile is relevant.
6. The FAISS retriever embeds the query using the configured Gemini embedding model and returns up to four source passages.
7. If enabled, SerpAPI is called only for questions that pass conservative non-personal query checks. Search snippets are treated as untrusted context.
8. LangChain combines the question, selected context, and conversation history into a prompt, then invokes the configured Groq or Gemini model.
9. The assistant response is stored as a conversation message. Verified passage or web references are returned with the response.

## Document flow

1. The client uploads a PDF, JPG, PNG, or WebP file to `/api/v1/documents/extract`.
2. The API requires current health-information consent, enforces a 10 MB default maximum, validates file signatures, and limits PDF pages and image dimensions.
3. Text is extracted with `pypdf` or Tesseract. Scanned PDFs additionally require Poppler.
4. Extracted text and an OCR warning are returned to the client. The server does not save uploaded bytes.
5. The user can review/edit/remove the text. If attached to a question, it is passed as transient `attachment_text` to the chat endpoint and model prompt; only the typed question is persisted as the user's message.

## Personal health context

The chat route includes saved user health context only when the context router identifies a personal health question. The context is read from SQL and sent to the configured Gemini model for that response. The client consent gate is backed by server-side dependencies; bypassing the UI does not bypass the API consent requirement.

## Data stores

| Store | Contents | Persistence |
|---|---|---|
| SQL database | User, consent, conversation, message, and health-record rows | Persistent; deletion actions are available for conversations and individual health items. |
| FAISS index | Curated medical knowledge chunks and metadata | Persistent on local disk; rebuild from source documents. Never ingest patient uploads here. |
| API process memory | Uploaded file bytes and OCR-extracted text during request processing | Transient; discarded after response. |
| Browser state | Current extracted text pending review, current conversation, and access token | React state plus access token in localStorage. Clearing/restarting the browser removes pending unsubmitted OCR text. |

## Configuration boundaries

- `GEMINI_API_KEY` is only read by the backend. The frontend should never receive provider keys.
- `ENABLE_WEB_SEARCH=false` by default. A SerpAPI key alone does not enable it.
- `FAISS_INDEX_PATH` must point to an application-owned index directory. LangChain FAISS reload uses a pickle-backed docstore; never point it to an untrusted directory.
- Uploaded documents are not stored in FAISS, SQL, or object storage in this version.
- `CORS_ORIGINS` are configured through `FRONTEND_URL` and `CORS_ORIGINS`.
- `METRICS_ENABLED=true` enables the internal Prometheus endpoint at `/metrics`. Restrict it to the monitoring network at the proxy/firewall; metrics are not user-authenticated.

## Operational metrics

The custom metric registry is process-local. HTTP metrics use route templates, bounded status/method labels, and histogram buckets; model metrics count individual attempts, durations, and provider-reported tokens when available; FAISS, OCR, limiter, and database instrumentation report bounded outcomes/durations. SQL text, bind values, prompts, identifiers, IPs, filenames, and extracted health text are intentionally excluded. See [`OPERATIONS_METRICS.md`](OPERATIONS_METRICS.md) for PromQL, Grafana/Prometheus setup, and horizontal-scaling caveats.

## Important limitations

This is not a clinical triage system. Keyword detection can miss urgent descriptions and can trigger on context that is not urgent. RAG quality depends on permitted, current, reviewed sources. The example knowledge file contains sample content; review and replace it before deployment. Web-search filters are not a guaranteed de-identification system. No privacy/security certification is implied by this design.
