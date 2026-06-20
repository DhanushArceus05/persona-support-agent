# Error Codes Reference

## HTTP Status Codes

| Code | Name | Description | Recommended Action |
|------|------|-------------|-------------------|
| 400 | Bad Request | Malformed request body or missing required parameters | Validate request schema against the API docs |
| 401 | Unauthorized | Missing or invalid Bearer token | Regenerate API key; check header format |
| 403 | Forbidden | Valid token but insufficient permissions | Add required OAuth scopes to the API key |
| 404 | Not Found | Resource does not exist or has been deleted | Verify resource ID; check if it was archived |
| 409 | Conflict | Duplicate resource creation attempt | Check for existing resource before creating |
| 422 | Unprocessable Entity | Request is well-formed but semantically invalid | Review field validation rules in the docs |
| 429 | Too Many Requests | Rate limit exceeded | Implement exponential backoff; consider plan upgrade |
| 500 | Internal Server Error | Unexpected server-side error | Retry after 30 seconds; report if persistent |
| 502 | Bad Gateway | Upstream service temporarily unavailable | Check status.platform.io; retry after 2 minutes |
| 503 | Service Unavailable | Platform undergoing maintenance | Monitor status.platform.io for resolution update |

---

## Platform-Specific Error Codes

### Authentication Errors (AUTH_*)
- `AUTH_001` — Token expired. Regenerate via Dashboard → Settings → API Keys.
- `AUTH_002` — Token revoked (security event detected). Contact support.
- `AUTH_003` — IP address not in allowlist. Add your IP under Dashboard → Security.
- `AUTH_004` — 2FA required. Enable 2FA at Dashboard → Account → Security.

### Billing Errors (BILL_*)
- `BILL_001` — Payment method declined. Update card at Dashboard → Billing.
- `BILL_002` — Subscription expired. Renew at Dashboard → Billing → Renew.
- `BILL_003` — Usage limit exceeded for current plan. Upgrade or reduce usage.
- `BILL_004` — Invoice generation failed. Contact billing@platform.io.

### Data Errors (DATA_*)
- `DATA_001` — Record not found. The ID may be incorrect or the record deleted.
- `DATA_002` — Schema validation failed. Ensure all required fields are present.
- `DATA_003` — Storage quota exceeded. Archive or delete data to free space.
- `DATA_004` — Data export in progress. Only one export can run at a time.

### Integration Errors (INT_*)
- `INT_001` — Database connection failed. Check host, port, and firewall rules.
- `INT_002` — Webhook delivery failed after 5 retries. Check endpoint health.
- `INT_003` — OAuth token revoked by third party. Re-authorise the integration.
- `INT_004` — Sync schema mismatch. A database column was renamed or removed.

---

## Reading Error Responses

All API errors follow this JSON structure:
```json
{
  "error": {
    "code": "AUTH_001",
    "message": "API token has expired",
    "details": "Token issued 2024-09-01 expired after 90 days",
    "request_id": "req_a1b2c3d4e5",
    "docs_url": "https://docs.platform.io/errors/AUTH_001"
  }
}
```

Always include the `request_id` when contacting support — it allows us to
retrieve the full server-side trace for your request.

---

## Debugging Tips

1. Log the full HTTP response including status code, headers, and body.
2. Check the `X-RateLimit-Remaining` header to monitor remaining quota.
3. The `X-Request-ID` response header matches `request_id` in the error body.
4. Enable verbose logging in the SDK:
   ```python
   from platform_sdk import Client
   client = Client(api_key="...", log_level="DEBUG")
   ```
