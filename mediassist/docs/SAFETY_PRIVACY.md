# Safety, Privacy, and Security Notes

## Intended use

MediAssist is a prototype for general health information. It does not diagnose, prescribe, replace a clinician, or determine whether a user is safe to wait. It is not a validated clinical decision-support or emergency-triage system.

## Safety controls implemented

- General-health and medication guardrails are included in the LangChain system prompt.
- A deterministic emergency phrase detector is called before retrieval/search/model generation and returns a fixed emergency response on a match.
- RAG passages, conversation history, OCR text, health notes, and web snippets are labeled as untrusted data in the prompt.
- Responses include a general-information disclaimer.
- Verified source metadata is returned separately from model-generated response text.

These controls do not guarantee safe or correct medical output. The emergency detector is an allowlist of phrase patterns: it can miss urgent language, misunderstand negation or time, and over-trigger. Do not claim clinically validated triage. Before piloting, a qualified clinical reviewer should develop and evaluate a much broader escalation policy, test it across language and accessibility cases, and ensure urgent-care instructions match each deployment location.

## Consent and access

- Chat, profile/condition/medication/treatment routes, and OCR require a current accepted `health_information` consent record.
- Acceptance and withdrawal are recorded as events. The latest event governs API access.
- Withdrawal blocks future access but does not delete conversations, health records, or account data.
- Account deletion and automated retention/deletion schedules are not implemented in this version.

## Data flow

- SQL stores accounts, consent history, chat text, and user-entered health information.
- User-reviewed OCR text is submitted to the backend only when the user sends it with a question. The upload bytes are read in memory and not persisted by this endpoint; OCR text is not saved as a separate message. The configured Groq or Gemini provider may receive the attachment context in the model request.
- Personal health context is added to a prompt only when the context router detects a relevant personal-health question.
- Web search is disabled by default. If enabled, the adapter filters obvious first-person, identifier-like, and personal-health phrases but cannot guarantee de-identification. Do not enable it for real-user health data without a privacy/vendor review.
- The browser access token is stored in localStorage in the current client. This is convenient for a prototype but is more exposed to successful script injection than a properly configured HttpOnly/SameSite cookie design.

## Operational safeguards still required

Before using non-synthetic or real patient information, assess and implement as appropriate:

- TLS termination, secure headers, key rotation, secret manager, and least-privilege access.
- Database and backup encryption, access logging, restore testing, and deletion across backups.
- Provider data-processing terms, retention settings, residency, and whether sending health information to model/OCR/search vendors is permitted.
- Log and analytics redaction. Do not log prompts, extracted text, health records, bearer tokens, or provider keys.
- The implemented rate limiter is a basic in-process sliding window. For production, use a shared store for multi-worker/replica enforcement, plus abuse detection, dependency and image/file security updates, vulnerability scanning, and incident response.
- Retention periods, deletion/export behavior, account deletion, support process, and operational ownership.
- Clinical, privacy, security, and legal review appropriate to intended function, claims, jurisdiction, and user population.

No compliance certification is claimed. SQLite, a local FAISS index, a disclaimer, or a safety prompt alone do not make the product production-ready.

## Operational telemetry

The Prometheus endpoint exports aggregate operational counters and timings only. Do not expose `/metrics` publicly; restrict it to the monitoring network or an authenticated internal proxy. Metric labels are bounded and intentionally exclude prompts, health data, file names, user IDs, IP addresses, tokens, and SQL contents. The current registry and rate limiter are process-local, so use a shared limiter and appropriate multi-process metrics strategy before running multiple workers or replicas. See [`OPERATIONS_METRICS.md`](OPERATIONS_METRICS.md) for the metric inventory, dashboard, and calculation examples.

## Knowledge quality

Only ingest sources that are permitted, relevant, dated, and reviewed. Preserve source title, publisher, URL where valid, page, and update date. The included content is sample project data; it should not be treated as an authoritative medical reference. Verify the usage rights of the bundled PDF and replace example/sample material before redistributing or deploying the application.
