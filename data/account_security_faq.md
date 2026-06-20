# Account Management & Security FAQ

## Password & Access

### How do I reset my password?
1. Go to the login page and click **"Forgot Password"**.
2. Enter the email address registered to your account.
3. Check your inbox for a reset link (valid for 30 minutes).
4. Click the link, set a new password meeting the requirements below, and log in.

**Password requirements:**
- Minimum 12 characters
- At least one uppercase letter, one number, and one special character
- Cannot reuse any of your last 5 passwords

If you do not receive the email within 5 minutes, check your spam folder. The sender address is `noreply@platform.io`.

---

### My account is locked. What do I do?
Accounts are locked after **5 consecutive failed login attempts** (security policy). The lock lasts 15 minutes automatically.

To unlock immediately:
1. Use the "Forgot Password" flow to set a new password — this also unlocks the account.
2. Or contact support at support@platform.io with your account ID.

---

### How do I enable Two-Factor Authentication (2FA)?
1. Navigate to **Dashboard → Account → Security → Two-Factor Authentication**.
2. Choose your preferred method: Authenticator App (recommended) or SMS.
3. Scan the QR code with your authenticator app (Google Authenticator, Authy).
4. Enter the 6-digit code to confirm setup.

Losing access to your 2FA device: Use your backup recovery codes (generated during setup and stored securely). If codes are also lost, contact support with government-issued ID verification.

---

### How do I change my registered email address?
1. Log in and go to **Dashboard → Account → Profile → Edit Email**.
2. Enter the new email and confirm your current password.
3. A verification link is sent to BOTH the old and new email addresses.
4. Confirm from both to complete the change.

Note: If you have lost access to the old email, contact support@platform.io.

---

## Team & User Management

### How do I invite team members?
Navigate to **Dashboard → Team → Invite Member**, enter the team member's email, and assign a role:
- **Viewer** — Read-only access to dashboards and reports.
- **Editor** — Create and edit resources; cannot manage billing.
- **Admin** — Full access including billing and team management.

Invited members receive an email with a 72-hour activation link.

---

### How do I remove a team member?
Go to **Dashboard → Team**, find the user, click **"Remove"**, and confirm. The user loses access immediately. Their work (documents, integrations) is transferred to the account owner.

---

## Data & Privacy

### How do I export my data?
Go to **Dashboard → Account → Data Export** and click **"Request Export"**. A download link is emailed within 4 hours. Exports include all project data, API logs, and billing history in JSON format.

### What happens to my data if I cancel?
Data is retained for 30 days after cancellation, then permanently and irreversibly deleted. Export your data before the retention period expires.

### Is my data encrypted?
Yes. All data is encrypted at rest (AES-256) and in transit (TLS 1.3). We are SOC 2 Type II and GDPR compliant.

---

## Integrations

### Which third-party integrations are supported?
- Slack (notifications and alerts)
- GitHub / GitLab (CI/CD pipelines)
- Zapier (automation workflows)
- Salesforce (CRM sync)
- Google Workspace (SSO and Drive)

Configure integrations under **Dashboard → Integrations**.

### Why is my Slack integration not sending notifications?
1. Verify the Slack bot is still installed in your Slack workspace.
2. Check that the notification channel still exists and the bot has permission to post.
3. Re-authorise the integration from **Dashboard → Integrations → Slack → Re-connect**.
