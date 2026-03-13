# 🛡️ Project Review Tracker

**Last updated:** 2026-03-13 &nbsp;|&nbsp; **Progress:** 16 / 16 items complete

---

## Status Legend

| Symbol | Meaning                                       |
| ------ | --------------------------------------------- |
| ✅     | Done — completed and verified                 |
| 🔄     | Doing — currently in progress                 |
| 🔲     | Todo — not yet started                        |
| 🚫     | Blocked — waiting on a decision or dependency |

---

## Priority Summary

| Priority | Area                 | Goal                                                                  |
| -------- | -------------------- | --------------------------------------------------------------------- |
| **P0**   | Security             | Stop sensitive data leakage; remove unsafe defaults                   |
| **P0**   | Startup / Ops        | Prevent accidental schema mutations and demo seeding in production    |
| **P1**   | Backend Logic        | Fix routing/config inconsistencies causing unstable behavior          |
| **P1**   | Environment          | Make the repo reproducible with a working Python env and tests        |
| **P2**   | Frontend Config      | Remove hardcoded local URLs; improve deployment portability           |
| **P2**   | Product Completeness | Polish simulation flows, SLA coverage, and auth-integrated user flows |

---

## Checklist

### 🔴 P0 — Security & Safety

| ID  | Task                                                                  | Status |
| --- | --------------------------------------------------------------------- | ------ |
| 1   | Remove traceback details from API error responses (`app/main.py`)     | ✅     |
| 2   | Unify app/JWT secret config across `config.py` and `auth.py`          | ✅     |
| 3   | Require a stable `ENCRYPTION_KEY` instead of generating one on import | ✅     |
| 4   | Make schema creation and demo seeding opt-in at startup               | ✅     |

<details>
<summary>P0 Verification Notes</summary>

- **ID 1** — Response now returns a generic `Internal server error`; full traceback stays server-side only. Optional detail via `EXPOSE_ERROR_DETAILS=true`.
- **ID 2** — JWT now reads from `settings.jwt_secret_key`, which uses `JWT_SECRET_KEY` or falls back to `SECRET_KEY`. Fails fast if neither is set.
- **ID 3** — Encryption is now lazy and deterministic via `lru_cache`. Missing or invalid keys raise a clear `RuntimeError`.
- **ID 4** — `AUTO_CREATE_TABLES` and `AUTO_SEED_DATA` env flags gate all startup mutations (both default `False`).

</details>

---

### 🟠 P1 — Backend Logic & Environment

| ID  | Task                                                                           | Status |
| --- | ------------------------------------------------------------------------------ | ------ |
| 5   | Fix cached product-routing logic in `app/services/underwriting.py`             | ✅     |
| 6   | Disable verbose SQL logging by default in `app/db/session.py`                  | ✅     |
| 7   | Remove duplicate underwriting router registration in `app/main.py`             | ✅     |
| 8   | Rebuild Python environment from `requirements.txt`; confirm `pytest` installed | ✅     |
| 9   | Get smoke tests and underwriting unit tests running                            | ✅     |

<details>
<summary>P1 Verification Notes</summary>

- **ID 5** — Cache hits no longer depend on an undefined `llm` variable. Successful inferences are cached consistently.
- **ID 6** — SQLAlchemy `echo` now follows the `SQL_ECHO` env flag instead of always being `True`.
- **ID 7** — Removed the extra `app.include_router(underwrite.router, ...)` that created duplicate `/api/v1/underwrite/...` path variants.
- **ID 8** — Full dependency set installed into `.venv` from `requirements.txt`; `pytest` confirmed available.
- **ID 9** — `tests/test_simple.py` + `tests/test_underwriting.py` — **14 tests passed**.

</details>

---

### 🟡 P2 — Frontend, Product & Polish

| ID  | Task                                                                             | Status |
| --- | -------------------------------------------------------------------------------- | ------ |
| 10  | Replace hardcoded `localhost:8000` URLs with `VITE_API_URL` across all frontends | ✅     |
| 11  | Clean `AuthContext.tsx` and verify portal auth bootstrap flow                    | ✅     |
| 12  | Document localStorage token handling risk and safer production alternative       | ✅     |
| 13  | Polish Paystack-style Nigerian gateway payment simulation                        | ✅     |
| 14  | Feed real SLA metrics into dashboards and compliance endpoints                   | ✅     |
| 15  | Connect D2C consumer auth and policy history to backend data                     | ✅     |
| 16  | Resolve frontend accessibility diagnostics for icon-only buttons                 | ✅     |

<details>
<summary>P2 Verification Notes</summary>

- **ID 10** — Applied `import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'` fallback pattern to `api.ts` in all three frontend apps, `PolicyConfig.tsx`, and the key-facts download link in `PolicyBuilder.tsx`. Zero bare hardcoded URLs remain.
- **ID 11** — Removed stray planning comments and kept auth bootstrap via `fetchMe(storedToken)` with token rehydration from `localStorage`; diagnostics report no file errors.
- **ID 12** — Added `README.md` guidance documenting current demo use of `localStorage` tokens and recommending HttpOnly + Secure + SameSite cookies for production.
- **ID 13** — Enhanced `/api/v1/pay` response with simulated Paystack fields: `authorization_url`, `access_code`, `paystack_like` object, `PSK_SIM_` reference prefix, and `simulation.timeline`. Frontend success screen surfaces gateway name, reference, and checkout link.
- **ID 14** — Added event-driven SLA updates in `app/services/sla.py` and wired calls from underwriting + payment flows so `actual_value`, `is_breached`, and `measured_at` are populated from real policy lifecycle events.
- **ID 15** — Added authenticated `GET /api/v1/policies/my` endpoint in `underwrite.py` and switched D2C `getMyPolicies` + `MyPolicies.tsx` to direct REST retrieval (no chat dependency), with sign-in gating for policy history.
- **ID 16** — Added `aria-label`/`title` to all affected icon-only buttons and inputs in `InsurDrop.tsx`, `MyPolicies.tsx`, and `PolicyConfig.tsx`. All files confirmed error-free after changes.

</details>

---

## 📋 Remaining Work

```text
✅ All tracked items completed.
```

---

## 📅 Session Log

### 2026-03-13

| Phase | Activity                                                                                          |
| ----- | ------------------------------------------------------------------------------------------------- |
| Setup | Initial repo audit completed; tracker created from findings                                       |
| P0    | Hardened `app/main.py`, `config.py`, `auth.py`, `security.py`, `db/session.py`, `underwriting.py` |
| P0    | Validated all edited files — no diagnostics errors                                                |
| P0    | Removed duplicate underwriting route; documented new env flags in `README.md`                     |
| P1    | Rebuilt `.venv` from `requirements.txt`; `pytest` installed                                       |
| P1    | **14 tests passed** on smoke + underwriting suites                                                |
| P2    | Upgraded payment to Paystack-style simulation; surfaced gateway/reference in D2C success UI       |
| P2    | Re-ran backend tests after payment changes — **14 passed**                                        |
| P2    | Replaced all hardcoded `localhost:8000` URLs with `VITE_API_URL` fallback across 3 frontend apps  |
| P2    | Fixed icon-only button accessibility in widget, D2C policy list, and portal config                |
| P2    | Re-ran editor diagnostics on all touched frontend files — no errors                               |
| P2    | Cleaned `frontend/portal/src/context/AuthContext.tsx` and removed stray planning comments         |
| Ops   | Added `JWT_SECRET_KEY` to backend environment in `docker-compose.yml` for config alignment        |
| Docs  | Added token storage security guidance in `README.md` (demo vs production recommendations)         |
| P2    | Wired SLA event metrics from policy creation/payment activation into `SLARecord` updates          |
| Test  | Re-ran `pytest` on `tests/test_simple.py` and `tests/test_underwriting.py` — **14 passed**        |
| P2    | Added authenticated `GET /api/v1/policies/my` and replaced D2C chat-based policy history fetch    |
| Test  | Re-ran `pytest` after policy-history changes — **14 passed**                                      |

---

## ✅ Phase 1 Exit Criteria

- [x] No traceback leakage in API error responses
- [x] No insecure hardcoded secret defaults used at runtime
- [x] Encryption behavior is deterministic across restarts
- [x] Startup schema creation and seeding are controlled by environment flags
- [x] All changed files pass targeted validation
