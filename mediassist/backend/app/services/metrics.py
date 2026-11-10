"""Privacy-conscious Prometheus metrics for MediAssist.

Metric labels are intentionally limited to controlled route templates, HTTP
methods/statuses, configured provider/model names, and bounded outcomes. Never
add user IDs, IP addresses, tokens, prompts, filenames, or extracted text here.
"""

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

REGISTRY = CollectorRegistry(auto_describe=True)

HTTP_REQUESTS_TOTAL = Counter(
    "mediassist_http_requests_total",
    "Completed HTTP requests (the /metrics scrape endpoint is excluded).",
    labelnames=("method", "route", "status_code"),
    registry=REGISTRY,
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "mediassist_http_request_duration_seconds",
    "End-to-end HTTP request duration in seconds, excluding /metrics scrapes.",
    labelnames=("method", "route"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
    registry=REGISTRY,
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "mediassist_http_requests_in_progress",
    "HTTP requests currently being processed.",
    labelnames=("method", "route"),
    registry=REGISTRY,
)
RATE_LIMIT_REJECTIONS_TOTAL = Counter(
    "mediassist_rate_limit_rejections_total",
    "Requests rejected by the application rate limiter.",
    labelnames=("route",),
    registry=REGISTRY,
)

LLM_REQUESTS_TOTAL = Counter(
    "mediassist_llm_requests_total",
    "Individual upstream LLM call attempts, including retry attempts.",
    labelnames=("provider", "model", "outcome"),
    registry=REGISTRY,
)
LLM_REQUEST_DURATION_SECONDS = Histogram(
    "mediassist_llm_request_duration_seconds",
    "Duration of individual upstream LLM call attempts in seconds.",
    labelnames=("provider", "model"),
    buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 30, 60, 120),
    registry=REGISTRY,
)
LLM_TOKENS_TOTAL = Counter(
    "mediassist_llm_tokens_total",
    "Provider-reported input and output tokens when returned by the provider.",
    labelnames=("provider", "model", "direction"),
    registry=REGISTRY,
)

RAG_SEARCHES_TOTAL = Counter(
    "mediassist_rag_searches_total",
    "FAISS retrieval calls by bounded result outcome.",
    labelnames=("outcome",),
    registry=REGISTRY,
)
RAG_SEARCH_DURATION_SECONDS = Histogram(
    "mediassist_rag_search_duration_seconds",
    "FAISS retrieval duration in seconds.",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
    registry=REGISTRY,
)

DATABASE_STATEMENTS_TOTAL = Counter(
    "mediassist_database_statements_total",
    "SQL statements executed by bounded operation and outcome; SQL text is never recorded.",
    labelnames=("operation", "outcome"),
    registry=REGISTRY,
)
DATABASE_STATEMENT_DURATION_SECONDS = Histogram(
    "mediassist_database_statement_duration_seconds",
    "SQL statement execution duration in seconds.",
    labelnames=("operation",),
    buckets=(0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
    registry=REGISTRY,
)

OCR_REQUESTS_TOTAL = Counter(
    "mediassist_ocr_requests_total",
    "Document extraction requests by detected content type and bounded outcome.",
    labelnames=("content_type", "outcome"),
    registry=REGISTRY,
)
OCR_DURATION_SECONDS = Histogram(
    "mediassist_ocr_request_duration_seconds",
    "Document extraction endpoint duration in seconds.",
    labelnames=("content_type",),
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 20, 30, 60, 120),
    registry=REGISTRY,
)
