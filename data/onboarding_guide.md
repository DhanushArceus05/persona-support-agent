# Getting Started — Onboarding Guide

Welcome to the platform! This guide walks you through the first-time setup from account creation to your first API call.

---

## Step 1: Create Your Account

1. Visit **app.platform.io/signup**.
2. Enter your business email and choose a strong password.
3. Verify your email address via the link sent to your inbox.
4. Complete your company profile (used for invoicing and support escalation).

---

## Step 2: Choose a Subscription Plan

After email verification, you are prompted to select a plan:
- **Starter** — ideal for individuals and small teams exploring the platform.
- **Pro** — recommended for growing teams needing higher API throughput.
- **Enterprise** — contact sales@platform.io for custom pricing and features.

You can start with a **14-day free trial** on the Pro plan with no credit card required.

---

## Step 3: Generate Your First API Key

1. Go to **Dashboard → Settings → API Keys → Create New Key**.
2. Give the key a descriptive name (e.g., "Production Backend").
3. Select the required OAuth scopes for your use case.
4. Copy and securely store the key — it is shown only once.
5. Store in an environment variable, never hard-code in source files.

---

## Step 4: Make Your First API Call

```bash
curl -X GET "https://api.platform.io/v3/health" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

Expected response:
```json
{ "status": "ok", "version": "3.4.1", "latency_ms": 12 }
```

---

## Step 5: Explore the SDK

We publish official SDKs for:
- **Python**: `pip install platform-sdk`
- **Node.js**: `npm install @platform/sdk`
- **Go**: `go get github.com/platform-io/sdk-go`

Quick Python example:
```python
from platform_sdk import Client

client = Client(api_key="YOUR_API_KEY")
result = client.data.list(limit=10)
print(result)
```

---

## Step 6: Set Up Webhooks (Optional)

To receive real-time event notifications:
1. Navigate to **Dashboard → Integrations → Webhooks → Add Endpoint**.
2. Enter your HTTPS endpoint URL.
3. Select the events to subscribe to (e.g., `data.created`, `billing.invoice_paid`).
4. Copy the webhook secret and use it to validate incoming signatures (see API Troubleshooting Guide).

---

## Step 7: Invite Your Team

Under **Dashboard → Team → Invite Member**, send invitations to colleagues. Assign roles appropriately (Viewer, Editor, or Admin).

---

## Common First-Day Issues

| Problem | Solution |
|---------|----------|
| Verification email not received | Check spam; resend from the login page |
| API key returning 401 | Confirm the key is copied correctly with no extra spaces |
| Dashboard loading slowly | Clear browser cache or try a different browser |
| Cannot select Enterprise plan | Contact sales@platform.io directly |

---

## Support Resources

- Documentation: docs.platform.io
- API Reference: api.platform.io/docs
- Community Forum: community.platform.io
- Live Chat: Available on the dashboard (Mon–Fri 9 AM–8 PM)
- Email: support@platform.io
