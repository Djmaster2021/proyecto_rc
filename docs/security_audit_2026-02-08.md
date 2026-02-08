# Security Audit Report

Date: 2026-02-08  
Scope: Django backend, payment webhook, chatbot endpoint, production settings, Android release hardening.

## Summary
- Overall status: Improved baseline with hardening controls implemented.
- Critical regressions found and fixed during audit.
- Automated tests: `31/31` passing.

## What was validated
- Django deployment checks (`manage.py check --deploy`) with production-like env.
- Static review for risky patterns:
  - SQL injection primitives (`raw`, `cursor.execute`, dynamic SQL)
  - RCE patterns (`eval`, `exec`, `subprocess`, `os.system`, unsafe deserialization)
  - CSRF exemptions and public endpoints
  - token/secret handling in URLs and logs
- Dynamic checks through test suite around authz, webhook validation, and throttling behavior.

## Fixes applied in this audit
1. Webhook secret leakage removed from query string.
   - File: `paciente/mp_service.py`
   - Change: no more `?secret=...` in `notification_url`.

2. Secure webhook auth path added.
   - Files: `paciente/urls.py`, `paciente/views.py`
   - Change:
     - Added route `/paciente/pagos/webhook/<webhook_key>/`.
     - Webhook accepts either secure header (`X-WEBHOOK-SECRET`) or secure path key.
     - Constant-time comparison (`hmac.compare_digest`).

3. Webhook abuse guard.
   - File: `paciente/views.py`
   - Change: payload max size enforced (`WEBHOOK_MAX_BODY_BYTES`).

4. Chatbot hardening tests.
   - File: `api/tests.py`
   - Change:
     - Secret required via header.
     - Querystring secret is rejected.

5. Payment integration security tests.
   - File: `paciente/tests.py`
   - Change:
     - reject oversized webhook payload.
     - verify secret not leaked as query param.
     - verify secure webhook path flow.

6. Logging hygiene in payment service.
   - File: `paciente/mp_service.py`
   - Change: diagnostic `print` replaced by `logger.debug`.

## Test evidence
- Command: `python manage.py test`
- Result: `OK` (`31` tests)

- Command (prod-like):
```bash
DJANGO_DEBUG=False \
DJANGO_SECRET_KEY='this-is-a-very-long-random-production-secret-key-1234567890' \
SECURE_SSL_REDIRECT=True \
SESSION_COOKIE_SECURE=True \
CSRF_COOKIE_SECURE=True \
SECURE_HSTS_SECONDS=31536000 \
SECURE_HSTS_INCLUDE_SUBDOMAINS=True \
SECURE_HSTS_PRELOAD=True \
python manage.py check --deploy
```
- Result: no Django deploy security warnings.

## Residual risks (still pending)
1. Dependency CVE scanning tool not installed in this environment.
   - `pip-audit` and `bandit` were not available.
2. Some modules still use `print` for operational logs.
   - Not critical, but should be migrated to structured logger with redaction rules.
3. CSRF-exempt endpoints exist by design (`chatbot`, `webhook`).
   - Currently controlled by secrets/rate limits; keep monitoring.
4. Full external pentest (DAST with ZAP/Burp against a live HTTPS deployment) not executed in this local sandbox.

## Next hardening actions (recommended)
1. Add CI job for `pip-audit` + `bandit`.
2. Enforce secret rotation policy (DJANGO, MercadoPago, OAuth, SMTP).
3. Add WAF and IP rate limits at edge (Cloudflare/Nginx).
4. Add alerting for spikes in `403`, `429`, `5xx`.
5. Run quarterly OWASP Top 10 pentest in staging/prod.
