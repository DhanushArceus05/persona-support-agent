# API Authentication & Troubleshooting Guide

## Overview
This document covers common API authentication errors, their root causes, and step-by-step resolution pathways for our SaaS platform REST API (v3).

---

## 1. HTTP 401 Unauthorized

### Root Cause
A 401 error indicates that the Bearer token supplied in the `Authorization` header is missing, malformed, expired, or has been revoked.

### Verification Steps
1. Confirm the header is formatted correctly:
   ```
   Authorization: Bearer <your_api_key>
   ```
2. Check token expiry — API keys issued before January 2024 expire after 90 days. Regenerate via **Dashboard → Settings → API Keys**.
3. Ensure no trailing whitespace or newline characters in the token string.
4. Verify the key is scoped to the correct environment (production vs. sandbox).

### Resolution
- Regenerate your API key from the developer dashboard.
- Update all environment variables and deployment secrets with the new key.
- Run a smoke-test request against `GET /v3/health` before re-deploying.

---

## 2. HTTP 403 Forbidden

### Root Cause
The token is valid but the associated account lacks permission for the requested resource or endpoint.

### Resolution
1. Review the OAuth scope list in your API key settings.
2. Add the required scopes: `read:data`, `write:data`, `admin:billing`.
3. Re-issue the token after updating scopes — existing tokens are NOT retroactively updated.

---

## 3. HTTP 429 Rate Limit Exceeded

### Limits
| Plan     | Requests/min | Burst |
|----------|-------------|-------|
| Starter  | 60          | 100   |
| Pro      | 300         | 500   |
| Enterprise | Unlimited | Custom |

### Resolution
- Implement exponential backoff with jitter in your retry logic.
- Cache responses locally where possible to reduce redundant calls.
- Upgrade your plan or request a temporary limit increase via support.

---

## 4. Webhook Signature Validation Failures

All webhook payloads are signed using HMAC-SHA256. Validate using the `X-Webhook-Signature` header:

```python
import hmac, hashlib

def validate_signature(payload_body: bytes, secret: str, signature_header: str) -> bool:
    expected = "sha256=" + hmac.new(
        secret.encode(), payload_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)
```

Common failure reasons:
- Reading the request body as a string (must use raw bytes).
- Incorrect webhook secret (Dashboard → Integrations → Webhooks).

---

## 5. SSL/TLS Certificate Errors

All API endpoints enforce TLS 1.2+. If you receive `SSL_ERROR_HANDSHAKE`:
1. Update your HTTP client library to the latest version.
2. Ensure your system CA bundle is current.
3. Do NOT disable SSL verification (`verify=False`) in production — this creates a security vulnerability.

---

## Contact
For persistent API issues, open a ticket at support@platform.io with:
- The full request/response including headers (redact the token).
- Your account ID.
- Timestamp of first failure.
