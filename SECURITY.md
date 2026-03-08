# Security — Secrets Management

This repository is public. All secrets are injected via environment variables — never hardcoded.

## Managed Secrets

| Variable | Purpose | Sensitivity | Notes |
|---|---|---|---|
| `CF_API_TOKEN` | Cloudflare API (Workers AI / Vectorize) | **High** | Full access to AI and vector operations |
| `CF_ACCOUNT_ID` | Cloudflare account identifier | Medium | Harmless alone, enables API calls with token |
| `SE_EMAIL` | Standard Ebooks Patrons Circle auth | Low | Email address only, empty password |

## Injection Methods

- **Local development:** `.env` file (git-ignored)
- **CI/CD:** GitHub Actions secrets
- **Reference:** See `.env.example` for required variables

## Defense Layers

1. **`.gitignore`** — `.env*` patterns excluded (except `.env.example`)
2. **`.env.example`** — Placeholder values only, safe to commit
3. **Environment variables** — All secrets loaded via `os.environ`, never in source
4. **Test mocking** — CI tests use `respx` mocks, no real credentials needed
5. **Startup validation** — `main.py` checks for required variables before running embed/ingest

## Credential Rotation

### CF_API_TOKEN

1. Cloudflare Dashboard → My Profile → API Tokens → Regenerate
2. Update local `.env`
3. Update GitHub repo → Settings → Secrets and variables → Actions

### SE_EMAIL

No rotation needed — tied to Patrons Circle membership email.
