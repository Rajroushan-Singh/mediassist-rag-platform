# MediAssist API Reference

API prefix: `/api/v1`. Authentication uses a bearer access token returned by login. OpenAPI is available at `/docs` in local development.

## Authentication

| Method | Route | Auth | Purpose |
|---|---|---|---|
| `POST` | `/auth/register` | No | Create an account. Password length is validated by the schema. |
| `POST` | `/auth/login` | No | Return a JWT bearer token. |
| `GET` | `/auth/me` | Yes | Return the current account. |
| `POST` | `/auth/logout` | Yes | Informational endpoint; the client discards its token. There is no server-side token revocation list. |

## Consent

| Method | Route | Auth | Purpose |
|---|---|---|---|
| `GET` | `/consent` | Yes | List consent event history. |
| `POST` | `/consent` | Yes | Append an acceptance or withdrawal event. |

Example acceptance/withdrawal body:

```json
{
  "consent_type": "health_information",
  "consent_version": "1.0",
  "accepted": true
}
```

Use `accepted: false` to record a withdrawal. The latest record for the health-information consent type controls access. Current consent is required for conversation, health-record, and document-extraction routes. Withdrawal blocks future requests but does not delete stored records.

## Conversations and chat

All routes require current health-information consent.

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/conversations` | Create a conversation. |
| `GET` | `/conversations` | List the current user's conversations. |
| `PATCH` | `/conversations/{conversation_id}` | Rename an owned conversation. |
| `DELETE` | `/conversations/{conversation_id}` | Delete an owned conversation and its messages. |
| `GET` | `/conversations/{conversation_id}/messages` | List messages for an owned conversation. |
| `POST` | `/conversations/{conversation_id}/messages` | Save a question, retrieve permitted context, and generate an answer. |

Example chat body:

```json
{
  "content": "What can cause a headache?",
  "attachment_text": "Optional user-reviewed OCR text; not persisted as a message."
}
```

`attachment_text` is optional and limited by `MAX_ATTACHMENT_CHARS`. Do not include any attachment text unless the user explicitly reviewed and elected to send it. The current chat response contains `user_message`, `assistant_message`, and a list of retrieved `sources` with optional `url`, `page`, and `kind` fields. The source list is returned with the send response; source metadata is not currently persisted on historical message rows.

## Health records

All routes require current health-information consent. The API supports reading/updating a health profile and listing, creating, updating, and deleting medical conditions, medications, and treatments. See the FastAPI OpenAPI schema for exact request fields and validation limits.

## Documents

| Method | Route | Auth/consent | Content type | Purpose |
|---|---|---|---|---|
| `POST` | `/documents/extract` | Authenticated + current consent | `multipart/form-data`, field `file` | Extract text from one supported file in memory. |

Supported signatures: PDF, JPEG, PNG, and WebP. Default maximum size is 10 MB. PDF page count and image dimensions are bounded. Response:

```json
{
  "filename": "report.pdf",
  "content_type": "application/pdf",
  "extracted_text": "Text extracted from the document...",
  "warning": "OCR may contain recognition errors; review the extracted text before use."
}
```

The endpoint does not persist the original file. OCR text is returned for client review and only reaches the model if sent with a chat message.

## Health check

`GET /health` returns basic service status. It intentionally does not expose secrets or database contents.

## Operational metrics

When `METRICS_ENABLED=true`, `GET /metrics` serves Prometheus text exposition format. This endpoint is intended for internal monitoring only and is excluded from its own HTTP metrics. Protect it from public access at the deployment network or reverse proxy. It does not require a user access token by default.

Available metric families cover HTTP requests/latency/in-flight work, 429 rate-limit rejections, provider/model attempts and reported tokens, FAISS outcomes/latency, OCR outcomes/latency, and SQL operation outcomes/latency. Labels contain only bounded route templates, HTTP methods/statuses, configured model names, file content types, SQL operations, and fixed outcomes. Never add prompts, health information, identifiers, IP addresses, credentials, or filenames to metric labels. Full definitions and example PromQL are in [`OPERATIONS_METRICS.md`](OPERATIONS_METRICS.md).
