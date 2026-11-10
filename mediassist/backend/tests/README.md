# Backend tests

Run from `backend/` after installing `requirements.txt`:

```bash
pytest -q
```

These tests are provider-independent and do not make live Gemini, embedding, OCR, or SERP API calls. OCR engine availability and external provider credentials should be checked separately when configuring a local development environment.
