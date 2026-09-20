# Database SSL Certificates

This directory is designated for public Certificate Authority (CA) root certificates used to verify secure database connections (such as Aiven MySQL).

## Aiven MySQL CA Certificate
Aiven MySQL uses TLS with a project-specific Root CA certificate.

### Recommended Usage Options:
1. **Repository File (Zero-Configuration on Render)**:
   - Download `ca.pem` from your Aiven Project / Service dashboard.
   - Save it in this directory as:
   - Store the certificate via Render Secret File or secure volume.
   - Do NOT commit certificates or private keys to git.
   - Sakhi AI automatically discovers and loads `aiven-ca.pem` from `backend/certs/` or `/etc/secrets/` if present.

2. **Render Environment Variable (`MYSQL_SSL_CA` or `DATABASE_SSL_CA`)**:
   - In your Render dashboard, add the environment variable `MYSQL_SSL_CA`.
   - Set the value to either:
     - The file path: `/etc/secrets/aiven-ca.pem` (if added as a Render Secret File)
     - OR the raw certificate content (PEM format starting with `-----BEGIN CERTIFICATE-----`).

> **Security Note**: Never commit certificates (`*.pem`, `*.crt`), private keys (`*.key`), or secrets to git. Always use Render Secret Files or environment variables.
