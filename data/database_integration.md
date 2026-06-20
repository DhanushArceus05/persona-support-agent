# Database Integration Troubleshooting Guide

## Supported Database Integrations
Our platform supports native connectors for:
- PostgreSQL (v12+)
- MySQL / MariaDB (v8+)
- MongoDB (v5+)
- Redis (v6+ — caching only)
- Snowflake (Enterprise plan)

---

## Common Errors and Resolutions

### Error: "Connection Refused" (ECONNREFUSED)

**Root Cause**: The platform cannot reach your database host.

**Checklist**:
1. Confirm the database host and port are correct in **Dashboard → Integrations → Database**.
2. Ensure your database server allows inbound connections from our static IP range:
   - `52.14.88.100/32`
   - `52.14.88.101/32`
   - `52.14.88.102/32`
3. Verify your firewall or security group rules permit traffic on the database port (default: PostgreSQL=5432, MySQL=3306, MongoDB=27017).
4. Test connectivity from your server: `telnet <DB_HOST> <PORT>`

---

### Error: "Authentication Failed" for Database Connector

**Root Cause**: Incorrect credentials or insufficient database user privileges.

**Resolution**:
1. Re-enter credentials in **Dashboard → Integrations → Database → Edit Connection**.
2. The database user requires the following minimum privileges:
   - PostgreSQL: `CONNECT`, `SELECT` on target schemas
   - MySQL: `SELECT`, `SHOW DATABASES`
   - MongoDB: `readAnyDatabase` role
3. Do NOT use the root/admin database user — create a dedicated read-only integration user.

---

### Error: "SSL Certificate Verification Failed"

**Root Cause**: The database requires SSL but the certificate cannot be verified.

**Resolution**:
1. Download your database server's CA certificate.
2. Upload it in **Dashboard → Integrations → Database → SSL Configuration → Upload CA Certificate**.
3. If using self-signed certificates, enable "Allow Self-Signed SSL" (not recommended for production).

---

### Slow Query Performance

If data sync is slow or queries time out:

1. **Add indexes** on columns used in sync filters (e.g., `updated_at`, `created_at`).
2. **Increase query timeout** in **Dashboard → Integrations → Database → Advanced → Query Timeout (seconds)**.
3. **Reduce sync frequency** for large tables — full table scans on every sync are expensive.
4. Check the **Sync Logs** under Dashboard for long-running query timestamps.

---

### "Internal Server Error" During Sync

Typically caused by:
- Schema changes (column renamed, type changed) — re-map columns in the integration settings.
- NULL values in NOT NULL mapped columns — clean data before syncing.
- Encoding issues — ensure your database uses UTF-8 encoding.

**Debugging steps**:
1. Go to **Dashboard → Integrations → Database → Sync Logs**.
2. Download the error log for the failed sync run.
3. Look for `ERROR:` lines — they include the offending SQL and the row count.

---

### PostgreSQL-Specific: Logical Replication Setup

For real-time CDC (Change Data Capture):
1. Set `wal_level = logical` in `postgresql.conf`.
2. Restart PostgreSQL.
3. Create a replication slot:
   ```sql
   SELECT pg_create_logical_replication_slot('platform_slot', 'pgoutput');
   ```
4. Grant the integration user replication permission:
   ```sql
   ALTER USER integration_user REPLICATION;
   ```
5. Enable the slot in **Dashboard → Integrations → Database → Enable CDC**.

---

## Getting Further Help

If none of the above resolves your issue:
1. Export the sync error log from the dashboard.
2. Note your database version, OS, and the exact error message.
3. Contact support@platform.io with the subject line: "DB Integration Issue — [Account ID]"

Response time for database integration issues: P2 (High) — 1-hour first response.
