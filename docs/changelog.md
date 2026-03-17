# Changelog

All significant changes made to the InsurBridge AI codebase, in reverse chronological order.

---

## 2026-03-17 — Security, Tenant Isolation, Chat Persistence, and Developer Experience

### Security fixes

#### Chat role spoofing closed
**File:** `app/api/endpoints/underwrite.py`

Unauthenticated `/chat` requests could previously send `role: "admin"` in the request body and receive god-mode system prompts from the LLM. The role resolution now ignores `request.role` entirely when no valid JWT is present — unauthenticated sessions are always treated as `consumer`.

```python
# Before
role = request.role  # client-controlled, could be spoofed

# After
role = "consumer"  # forced for unauthenticated requests
```

---

#### `show_policies` data leak closed
**File:** `app/api/endpoints/underwrite.py`

The `show_policies` chat action previously allowed unauthenticated callers to query the full policy list for any email address. Access now requires authentication and is scoped by role:

- **Consumer** — own policies only; email parameter ignored
- **Partner** — policies sold through them; optional email filter within that scope
- **Insurer / Compliance Officer** — tenant-scoped; optional email filter
- **Admin** — all policies; optional email filter

---

#### `rotate_api_key` role check added
**File:** `app/api/endpoints/underwrite.py`

The chat action to rotate an API key previously checked only that the user was authenticated. Any authenticated role (insurer, consumer) could trigger it. Now restricted to `role == "partner"` only.

---

### Chat improvements

#### `show_tenants` admin action implemented
**File:** `app/api/endpoints/underwrite.py`

`show_tenants` was listed in the admin system prompt but had no handler — the LLM would claim to execute it and receive empty data back. The handler now queries all `UserRole.INSURER` users and returns their `tenant_id`, `company_name`, and `email`. Still admin-only.

---

#### Chat session persistence
**Files:** `app/models/chat_log.py`, `app/schemas/underwrite.py`, `app/api/endpoints/underwrite.py`

Chat conversations were stateless — refreshing the page lost all conversation history. The fix:

- Added `session_id` (UUID string) and `user_email` columns to the `chat_logs` table.
- `ChatRequest` now accepts an optional `session_id`. The client generates a UUID on the first message and passes the same value on every subsequent turn.
- If the client sends an empty `history` but a known `session_id`, the backend loads the last 10 exchanges from the DB and uses them as conversation context.
- `session_id` is echoed back in every chat response so the client always has it.
- New endpoint: `GET /api/v1/chat/history/{session_id}` — returns stored history as `[{role, content}]` pairs for explicit restoration after a page reload.
- Alembic migration: `b2c3d4e5f6a7_add_session_fields_to_chat_logs.py`

---

### Tenant isolation

#### `_manual_tenant()` replaced with DB field lookup
**Files:** `app/services/tenant.py` (new), `app/models/manual.py`, `app/api/endpoints/compliance.py`, `app/api/endpoints/underwrite.py`, `app/api/endpoints/manuals.py`

The tenant of an underwriting manual was previously inferred by string-matching `product_type` in multiple places. This was fragile (a product type that didn't match a known keyword silently fell to the general tenant) and duplicated across files.

**What changed:**

1. **New shared utility** — `app/services/tenant.py` is the single authoritative home for `manual_tenant_from_product()` and `policy_tenant_from_product()`. The string-matching heuristic still exists here as a fallback only.

2. **`tenant_id` column on `UnderwritingManual`** — new nullable column set at upload time from the uploading user's own `tenant_id`. Never left NULL on new records (falls back to the heuristic if the user has no tenant set). Older rows are back-filled by the Alembic migration.

3. **`compliance.py`** — `_manual_tenant(manual)` now reads `manual.tenant_id` directly; falls back to the heuristic only when the field is empty (legacy rows).

4. **`underwrite.py`** — all three inline tenant assignments (`/underwrite`, `/soap/underwrite`, chat `start_quote`) replaced with `manual.tenant_id or policy_tenant_from_product(manual.product_type)`.

5. **`manuals.py` upload endpoint** — now requires authentication (`get_current_user` dependency added). Sets `tenant_id` from the uploading user at record creation time.

6. **Alembic migration:** `a1b2c3d4e5f6_add_tenant_id_to_manuals.py`

---

### Auth boundary tests
**File:** `tests/test_compliance_auth.py` (new — 24 tests)

Test coverage for role and tenant scoping was absent. New test file covers:

- `_is_admin()` — correctly identifies admin vs all other roles
- `_tenant_scope()` — returns `tenant_id` when set; falls back to email
- `manual_tenant_from_product()` — life/gadget/device/auto/None edge cases
- `_manual_tenant(manual)` — prefers `manual.tenant_id` over product-type fallback
- HTTP 403 enforcement — consumer and partner cannot reach `/audit-log` or `/sla/breaches`; insurer, compliance officer, and admin can

All 38 tests (14 original + 24 new) pass.

---

### CORS — env-driven origins
**Files:** `app/core/config.py`, `app/main.py`

CORS origins were hardcoded to localhost only. Production deployments had no way to add their frontend domains without editing code.

- Added `CORS_ORIGINS` env var (comma-separated string, default empty).
- `main.py` now merges localhost dev origins with any origins from the env var.
- Set `CORS_ORIGINS=https://your-d2c.vercel.app,https://your-portal.vercel.app` when deploying.

---

### Developer experience

#### `.env.example` updated
**File:** `.env.example`

The example env file was missing `ENCRYPTION_KEY`, `JWT_SECRET_KEY`, `AUTO_CREATE_TABLES`, `AUTO_SEED_DATA`, `REDIS_URL`, and `CORS_ORIGINS`. All required and optional variables are now documented with generation commands inline.

#### `docker-compose.yml` — missing env vars added
**File:** `docker-compose.yml`

`ENCRYPTION_KEY`, `AUTO_CREATE_TABLES`, `AUTO_SEED_DATA`, `SQL_ECHO`, and `EXPOSE_ERROR_DETAILS` were not being passed into the backend container. Added with safe defaults (`AUTO_CREATE_TABLES` and `AUTO_SEED_DATA` default to `true` so first-boot schema creation works without manual intervention).

#### Local dev setup guide
**File:** `docs/local_dev_setup.md` (new)

Step-by-step guide written for developers with no prior experience with Docker or Python environments. Covers:
- Prerequisites with download links
- Generating `JWT_SECRET_KEY` and `ENCRYPTION_KEY` with exact commands
- Option A (Docker Compose — one command, everything)
- Option B (native/mixed — Docker for infra, local processes for code)
- Demo account table (all seeded users, passwords, and what each role can do)
- Testing without a frontend via Swagger UI
- Running the test suite
- Seven common first-run errors with fixes
- File structure reference

---

## Summary of files changed

| File | Change type |
|---|---|
| `app/core/config.py` | Added `CORS_ORIGINS` setting |
| `app/main.py` | CORS origins now env-driven |
| `app/models/manual.py` | Added `tenant_id` column |
| `app/models/chat_log.py` | Added `session_id` and `user_email` columns |
| `app/schemas/underwrite.py` | Added `session_id` field to `ChatRequest` |
| `app/services/tenant.py` | New — shared tenant resolution utility |
| `app/api/endpoints/compliance.py` | `_manual_tenant()` uses DB field; removed dead `_role_value()` helper |
| `app/api/endpoints/manuals.py` | Upload requires auth; sets `tenant_id` on record creation |
| `app/api/endpoints/underwrite.py` | Role spoofing fix; `show_policies` scoped; `rotate_api_key` role check; `show_tenants` handler; session persistence; inline tenant assignments replaced |
| `docker-compose.yml` | All required env vars now passed to backend container |
| `.env.example` | Complete — all required and optional vars documented |
| `tests/test_compliance_auth.py` | New — 24 auth boundary tests |
| `alembic/versions/a1b2c3d4e5f6_add_tenant_id_to_manuals.py` | New migration — adds `tenant_id` to `underwriting_manuals`, back-fills existing rows |
| `alembic/versions/b2c3d4e5f6a7_add_session_fields_to_chat_logs.py` | New migration — adds `session_id` and `user_email` to `chat_logs` |
| `docs/local_dev_setup.md` | New — newbie-friendly local setup guide |
| `docs/changelog.md` | New — this file |
