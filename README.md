# InsurBridge AI

## Environment Variables

Create a `.env` file with:

```env
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=insurbridge
GOOGLE_API_KEY=your_gemini_api_key
JWT_SECRET_KEY=replace_with_a_long_random_secret
ENCRYPTION_KEY=your_fernet_key
REDIS_URL=redis://localhost:6379
SQL_ECHO=false
EXPOSE_ERROR_DETAILS=false
AUTO_CREATE_TABLES=false
AUTO_SEED_DATA=false
```

Notes:

- `JWT_SECRET_KEY` (or `SECRET_KEY`) is now required for authentication flows.
- `ENCRYPTION_KEY` must stay stable across restarts or encrypted manuals cannot be read back.
- `AUTO_CREATE_TABLES` and `AUTO_SEED_DATA` are disabled by default; enable them only for local demo/bootstrap scenarios.
- `EXPOSE_ERROR_DETAILS=true` is intended only for local debugging.

## Token Storage Security (Demo vs Production)

- Current frontend apps store auth tokens in `localStorage` (`token` / `ib_token`) for demo simplicity.
- This is acceptable for hackathon demos but is more exposed to token theft in XSS scenarios.
- For production, prefer short-lived access tokens in **HttpOnly**, **Secure**, **SameSite** cookies with server-side refresh rotation.
- If `localStorage` is temporarily retained, enforce strict CSP, sanitize all user input, and keep token lifetimes short.

## Quick Start

```bash
# 1. Start infrastructure
docker-compose up -d

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the API
uvicorn app.main:app --reload --port 8000
```

## API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI.

## Architecture & UI Documentation

Detailed documentation for the hackathon can be found in the `docs/` folder:

- [Project Overview & Architecture](docs/project_overview.md) - System design, Liquid Logic, and remaining tasks.
- [Frontend UI Walkthrough](docs/walkthrough.md) - Explains the multi-insurer scalable product catalog design.
