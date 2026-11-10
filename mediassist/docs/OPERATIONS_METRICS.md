# Operational metrics and monitoring

MediAssist exports Prometheus text format at `GET /metrics` when `METRICS_ENABLED=true` (the default in the example environment). The endpoint is excluded from its own traffic counters. Keep it on an internal network or restrict access at the reverse proxy/firewall; do not publish it directly to the public internet. Metrics contain aggregate operational signals only: there are no prompt, OCR text, user, email, IP, token-secret, conversation, or file-name labels.

## Included metrics

| Metric | Type and labels | Meaning |
|---|---|---|
| `mediassist_http_requests_total` | Counter: `method`, route template, `status_code` | Completed API requests, including 429s and 5xx responses. `/metrics` itself is excluded. |
| `mediassist_http_request_duration_seconds` | Histogram: `method`, route template | End-to-end request duration, seconds. Use histogram quantiles for p50/p95/p99. |
| `mediassist_http_requests_in_progress` | Gauge: `method`, route template | Requests currently being processed. |
| `mediassist_rate_limit_rejections_total` | Counter: route template | Requests rejected with HTTP 429 by the app limiter. |
| `mediassist_llm_requests_total` | Counter: provider, configured model, outcome | Individual upstream attempts, including retries; outcome is `success` or `error`. |
| `mediassist_llm_request_duration_seconds` | Histogram: provider, configured model | Duration of one upstream model attempt. |
| `mediassist_llm_tokens_total` | Counter: provider, configured model, direction | Provider-reported input/output tokens when LangChain returns usage metadata. Missing provider usage is not guessed. |
| `mediassist_rag_searches_total` | Counter: bounded outcome | FAISS search outcomes: results, empty results, unavailable index, empty query, or error. |
| `mediassist_rag_search_duration_seconds` | Histogram | FAISS retrieval latency. |
| `mediassist_ocr_requests_total` | Counter: detected content type, bounded outcome | OCR/document extraction successes, empty extractions, client errors, and failures. |
| `mediassist_ocr_request_duration_seconds` | Histogram: detected content type | End-to-end extraction endpoint duration, including AI vision if used. |
| `mediassist_database_statements_total` | Counter: SQL operation, outcome | SQL statement successes/errors; SQL text and bind values are never stored in metrics. |
| `mediassist_database_statement_duration_seconds` | Histogram: SQL operation | SQL statement execution time. |

All HTTP route labels are registered route templates (for example `/api/v1/conversations/{conversation_id}/messages`), never raw paths with identifiers. Methods, SQL operations, status codes, content types, providers, and outcomes are controlled/bounded dimensions.

## Calculate common indicators in Prometheus

The provided `monitoring/prometheus.yml` scrapes MediAssist every 15 seconds. Example PromQL:

```promql
# Requests per second, overall or by route
sum(rate(mediassist_http_requests_total[5m]))
sum by (route) (rate(mediassist_http_requests_total[5m]))

# HTTP 5xx rate as a fraction of all API responses
sum(rate(mediassist_http_requests_total{status_code=~"5.."}[5m]))
/
clamp_min(sum(rate(mediassist_http_requests_total[5m])), 1e-9)

# API p95 latency, seconds, overall or by route
histogram_quantile(0.95, sum by (le) (rate(mediassist_http_request_duration_seconds_bucket[5m])))
histogram_quantile(0.95, sum by (le, route) (rate(mediassist_http_request_duration_seconds_bucket[5m])))

# LLM upstream failure ratio and p95
sum(rate(mediassist_llm_requests_total{outcome="error"}[5m]))
/
clamp_min(sum(rate(mediassist_llm_requests_total[5m])), 1e-9)
histogram_quantile(0.95, sum by (le, provider, model) (rate(mediassist_llm_request_duration_seconds_bucket[5m])))

# Provider-reported token throughput (tokens/second), split by direction
sum by (provider, model, direction) (rate(mediassist_llm_tokens_total[5m]))

# Empty-result share among FAISS queries with an available index
sum(rate(mediassist_rag_searches_total{outcome="empty_results"}[15m]))
/
clamp_min(sum(rate(mediassist_rag_searches_total{outcome=~"results|empty_results"}[15m])), 1e-9)

# OCR failure share (server errors, excluding invalid client submissions)
sum(rate(mediassist_ocr_requests_total{outcome="error"}[15m]))
/
clamp_min(sum(rate(mediassist_ocr_requests_total[15m])), 1e-9)

# Database statement error ratio and p95
sum(rate(mediassist_database_statements_total{outcome="error"}[5m]))
/
clamp_min(sum(rate(mediassist_database_statements_total[5m])), 1e-9)
histogram_quantile(0.95, sum by (le, operation) (rate(mediassist_database_statement_duration_seconds_bucket[5m])))

# Rate-limit rejections per minute
sum by (route) (rate(mediassist_rate_limit_rejections_total[5m]) * 60)
```

Request/error ratios above are fractions (multiply by 100 for a percentage). Histogram quantiles are estimates; select a window long enough to include useful traffic. Do not average per-instance quantiles; aggregate histogram buckets first as shown.

## Token cost

The application exposes reported input/output token totals but intentionally does not hard-code provider prices, because rates differ by model and change over time. For a chosen reporting period, calculate:

```text
estimated_cost = input_tokens × current_input_price_per_token
               + output_tokens × current_output_price_per_token
```

Use your current provider/model price sheet and convert its per-million pricing into a per-token price. This is an estimate; it may exclude cached tokens, image charges, retries, or other provider-specific billing. Compare it to the provider invoice. If a provider does not return usage metadata, token totals will be incomplete and the metrics do not infer usage from prompt text.

## Start local monitoring

With Docker Compose installed:

```bash
cd monitoring
cp .env.example .env
# Set GRAFANA_ADMIN_PASSWORD in .env to a strong local password.
docker compose up -d
```

The sample compose file binds Prometheus at `http://127.0.0.1:9090` and Grafana at `http://127.0.0.1:3000`; Prometheus is preconfigured as Grafana's data source and the MediAssist dashboard is provisioned automatically. If the API runs outside Docker, compose scrapes `host.docker.internal:8000`; the included `extra_hosts` maps this name on Linux. Because the API must accept traffic from the monitoring container, run the development API with `uvicorn app.main:app --host 0.0.0.0` for this setup and use a host firewall to limit access. This bind is for local monitoring only and must not be treated as deployment hardening. Start the API with `METRICS_ENABLED=true` and verify `http://localhost:8000/metrics` locally.

The alert rules in `monitoring/alerts.yml` are starting examples, not service-level objectives. Tune thresholds after collecting a baseline. Do not alert on emergency phrase counts as if they represented confirmed medical emergencies; the detector is not clinically validated.

## Deployment and limitations

The rate limiter and Prometheus registry are in-process. They are suitable for a single development instance. With multiple Uvicorn workers/replicas, each worker keeps separate rate-limit state and separate metric state unless you configure a supported multiprocess or external metrics architecture. Therefore these counters are not automatically cluster-wide. For production, use a shared rate-limit backend such as Redis and configure Prometheus multiprocess collection or scrape each replica separately. Do not sum duplicate replicas accidentally.

Track application process/resource metrics (CPU, memory, restarts), database availability/pool saturation, and host/container health with your deployment platform/exporters. These are not inferred by the custom MediAssist metrics. Token-based cost is a model spend proxy, not a bill. No clinical answer-quality score is produced from production telemetry; evaluate answer quality with reviewed synthetic cases and appropriate clinical oversight.
