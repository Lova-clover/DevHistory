# Security Model

## Authentication

- **OAuth provider**: GitHub OAuth 2.0
- **Token format**: JWT (HS256) stored in **httpOnly, Secure, SameSite=Lax** cookie
- **Token lifetime**: 7 days
- **No localStorage**: Tokens are never exposed to JavaScript
- **Logout**: Clears cookie and redirects

## Cookie Configuration

| Attribute | Value |
|-----------|-------|
| `httpOnly` | `true` – inaccessible to JS |
| `Secure` | `true` in production (HTTPS only) |
| `SameSite` | `Lax` – sent with same-site + top-level GET navigations |
| `Path` | `/` |
| `Domain` | Configurable via `COOKIE_DOMAIN` |
| `Max-Age` | 7 days (604800 seconds) |

## BYO LLM Key Encryption

- User-provided API keys are encrypted at rest using **Fernet** (AES-128-CBC with HMAC)
- Server-side `CREDENTIALS_ENCRYPTION_KEY` is required (generated via `Fernet.generate_key()`)
- Only the last 4 characters of the key are stored in plaintext (for UI masking)
- Keys are decrypted only at the moment of use (in Celery worker), never logged

## Portfolio Sharing

### Public Portfolio (`/u/{slug}`)

- Opt-in: user must explicitly enable `portfolio_public`
- Slug must be 3-40 chars, alphanumeric + hyphens/underscores
- Forks are excluded from public view
- Email shown only if user enables `portfolio_show_email`

### Private Share Link (`/s/{token}`)

- Token: 32-byte URL-safe random string (`secrets.token_urlsafe(32)`)
- Optional expiry (configurable in days)
- Rotating the token invalidates the previous link
- Page served with `<meta name="robots" content="noindex, nofollow">`

## Analytics Privacy

- **IP addresses** are never stored raw
- IPs are hashed with a **daily-rotating salt** (`SHA256(date:ip)[:16]`)
- This enables daily UV counting while preventing long-term tracking
- `user_agent` is truncated to 512 characters
- The `session_id` cookie is optional and not httpOnly (analytics only)

## Admin Access

- Controlled by `ADMIN_GITHUB_USERNAMES` env var (comma-separated GitHub usernames)
- Or `is_admin` flag on the `users` table
- Admin endpoints return 403 for non-admin users

## CORS

- `allow_origins` is restricted to `FRONTEND_URL` only
- `allow_credentials: true` for cookie transmission
- In production, Caddy serves everything same-origin (no CORS needed for browser requests)

## Infrastructure

- **Caddy** auto-provisions and renews HTTPS certificates via ACME
- Security headers: `HSTS`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`
- PostgreSQL and Redis are internal-only (no exposed ports in production)
