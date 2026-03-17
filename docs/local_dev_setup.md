# Local Development Setup Guide

A step-by-step guide for getting InsurBridge AI running on your own machine.
No prior experience with Docker or Python environments required.

---

## What you are setting up

InsurBridge AI has four pieces that need to run at the same time:

| Piece | What it does | Where it runs |
|---|---|---|
| **Backend** | The FastAPI server — all the business logic and AI | http://localhost:8000 |
| **D2C frontend** | Consumer-facing policy builder | http://localhost:3000 (Docker) or 5173 (native) |
| **Portal frontend** | Insurer / partner / admin dashboard | http://localhost:3002 (Docker) or 5174 (native) |
| **Widget frontend** | Embeddable chatbot | http://localhost:3001 (Docker) or 5175 (native) |

The backend also needs two background services:

| Service | What it does |
|---|---|
| **PostgreSQL** | The database |
| **Redis** | Caching layer |

---

## Choose your path

- **[Option A — Docker Compose](#option-a--docker-compose-recommended-for-first-time-setup)** — one command starts everything. Best for first-time setup or just trying the app.
- **[Option B — Native (mixed)](#option-b--native-mixed-best-for-active-development)** — Docker for the database/Redis only, everything else runs directly. Better when you are actively editing code because changes apply instantly.

---

## Prerequisites

### Both options need:
- **Git** — to clone the repo ([git-scm.com](https://git-scm.com))
- **A Google Gemini API key** — free at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey). Click "Create API key", copy it, keep it safe.

### Option A also needs:
- **Docker Desktop** — [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop). Install it and make sure it is running (you should see the Docker whale icon in your system tray).

### Option B also needs:
- **Python 3.11+** — [python.org/downloads](https://www.python.org/downloads). During install on Windows, tick "Add Python to PATH".
- **Node.js 18+** — [nodejs.org](https://nodejs.org). Choose the LTS version.
- **Docker Desktop** — still needed for Postgres and Redis (or you can install them natively, but Docker is easier).

Verify your installs by opening a terminal and running:
```bash
python --version    # should say 3.11 or higher
node --version      # should say v18 or higher
docker --version    # should say any recent version
```

---

## One-time: clone the repo and create your .env file

These steps apply to both Option A and Option B.

```bash
# 1. Clone
git clone https://github.com/your-org/heirs_insurance_hackathon.git
cd heirs_insurance_hackathon

# 2. Copy the example env file
cp .env.example .env
```

Now open `.env` in any text editor. You need to fill in three values:

### GOOGLE_API_KEY
Paste the key you got from Google AI Studio:
```
GOOGLE_API_KEY=AIzaSy...your key here...
```

### JWT_SECRET_KEY
This is a random secret used to sign login tokens. Generate one by running:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copy the output and paste it:
```
JWT_SECRET_KEY=a3f9c2...paste the output here...
```

### ENCRYPTION_KEY
This protects uploaded insurance manual files. Generate one by running:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Copy the output and paste it:
```
ENCRYPTION_KEY=abc123...paste the output here...
```

Your completed `.env` should look like this (values are examples, use your own):
```
GOOGLE_API_KEY=AIzaSyD_example_key_do_not_copy
JWT_SECRET_KEY=d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5
ENCRYPTION_KEY=xK9mP2nQ8rT5vW1yZ3cF6hJ0lB7eN4dA=
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=insurbridge
REDIS_URL=redis://localhost:6379/0
AUTO_CREATE_TABLES=true
AUTO_SEED_DATA=true
SQL_ECHO=false
EXPOSE_ERROR_DETAILS=false
```

> **Important:** Never commit your `.env` file to Git. It is already listed in `.gitignore`.

---

## Option A — Docker Compose (recommended for first-time setup)

### Start everything
```bash
docker-compose up --build
```

This will:
1. Download Postgres and Redis images (~200 MB, first time only)
2. Build the backend Docker image (~2–3 min, first time only)
3. Build the three frontend Docker images (~3–4 min, first time only)
4. Start all six services
5. On first boot: automatically create the database schema and seed demo users

You will see a lot of log output. When you see lines like these, everything is ready:
```
backend_1   | INFO:     Application startup complete.
backend_1   | INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Open the apps
- Backend API docs: http://localhost:8000/docs
- Consumer app: http://localhost:3000
- Portal (admin/insurer): http://localhost:3002
- Widget: http://localhost:3001

### After first successful boot
Edit your `.env` and change:
```
AUTO_CREATE_TABLES=false
AUTO_SEED_DATA=false
```
Then restart the backend so it does not re-seed on every start:
```bash
docker-compose restart backend
```

### Stop everything
```bash
# Stop (keeps your database data)
docker-compose down

# Stop and delete all data (clean slate)
docker-compose down -v
```

### Start again later (without rebuilding)
```bash
docker-compose up
```

---

## Option B — Native (mixed, best for active development)

### Step 1 — Start Postgres and Redis with Docker
```bash
docker-compose up -d db redis
```

The `-d` flag runs them in the background. You only need to run this once per machine restart.

Verify they are running:
```bash
docker ps
# You should see two containers: postgres and redis
```

### Step 2 — Set up the Python virtual environment

```bash
# Create a virtual environment inside the project folder
python -m venv .venv

# Activate it
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Your terminal prompt should now start with (.venv)
# Install all dependencies
pip install -r requirements.txt
```

> If you close the terminal and come back later, just run the activate command again before working.

### Step 3 — Run the backend

Make sure your `.venv` is active (you see `(.venv)` in your prompt), then:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

The `--reload` flag means the server automatically restarts whenever you save a Python file. Very handy for development.

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Visit http://localhost:8000/docs to confirm it is working.

After the first boot, set `AUTO_CREATE_TABLES=false` and `AUTO_SEED_DATA=false` in your `.env`, then stop and restart the backend (`Ctrl+C` then re-run the command).

### Step 4 — Run the frontends

Open **three new terminals**, one for each frontend. In each one, `cd` into the frontend folder and run:

**Terminal 2 — D2C consumer app:**
```bash
cd frontend/d2c
npm install        # first time only
npm run dev
# → http://localhost:5173
```

**Terminal 3 — Portal:**
```bash
cd frontend/portal
npm install        # first time only
npm run dev
# → http://localhost:5174
```

**Terminal 4 — Widget:**
```bash
cd frontend/widget
npm install        # first time only
npm run dev
# → http://localhost:5175
```

Each frontend will open in your browser automatically, or you can visit the URLs above.

---

## Demo accounts

These are seeded automatically on first boot. Use them to log in to the portal.

| Role | Email | Password | Can do |
|---|---|---|---|
| Consumer | register any new email | any password | Buy policies, chat |
| Partner | partner@example.com | password | Dashboard, commissions, API keys |
| Insurer (Life) | admin@heirs-life.com | password | SLA monitor, audit log, rules |
| Insurer (General) | admin@heirs-general.com | password | SLA monitor, audit log, rules |
| Compliance Officer | compliance@example.com | password | Audit log, SLA breaches |
| Superadmin | superadmin@heirsholdings.com | superpassword | Everything |

---

## Testing the backend without a frontend

The interactive API docs at http://localhost:8000/docs let you call every endpoint directly in the browser.

**Quick smoke test sequence:**

1. `GET /health` — should return `{"status": "healthy"}`
2. `GET /api/v1/products` — should return the list of coverage blocks (no login needed)
3. `POST /api/v1/auth/login` — log in as a demo user to get a JWT token
   - Body: `{"username": "admin@heirs-life.com", "password": "password"}`
   - Copy the `access_token` from the response
4. Click **Authorize** (the padlock button at the top of the docs page), paste your token
5. `GET /api/v1/compliance/audit-log` — should now work with your insurer token
6. `POST /api/v1/chat` — try a message like `{"message": "what products do you have?"}`

---

## Run the automated tests

```bash
# Make sure your .venv is active
python -m pytest tests/ -v
```

You should see **38 tests passed**. These run entirely offline — no database or network needed.

---

## Common problems

**`ENCRYPTION_KEY not configured` error on startup**
You forgot to fill in `ENCRYPTION_KEY` in your `.env`. Generate one with the command in the setup section above.

**`JWT secret key not configured` error**
Same issue — fill in `JWT_SECRET_KEY` in `.env`.

**`Connection refused` on port 5432 (Postgres)**
Docker Desktop is not running, or you forgot to start the database:
```bash
docker-compose up -d db redis
```

**`npm: command not found`**
Node.js is not installed or not on your PATH. Re-install from nodejs.org and restart your terminal.

**Frontend shows a blank page or network error**
The backend is not running. Check that `uvicorn` is running in another terminal and visit http://localhost:8000/health.

**Docker Compose build fails with a Python dependency error**
Try deleting the cached image and rebuilding:
```bash
docker-compose down
docker-compose build --no-cache backend
docker-compose up
```

**Port already in use**
Another process is using port 8000, 3000, etc. Either stop the other process or change the port in `docker-compose.yml`.

---

## File structure quick reference

```
heirs_insurance_hackathon/
├── app/                    ← Backend (Python / FastAPI)
│   ├── api/endpoints/      ← Route handlers (auth, underwrite, chat, compliance…)
│   ├── models/             ← Database table definitions
│   ├── services/           ← Business logic (underwriting, payments, SLA…)
│   ├── core/               ← Config, security, LLM client
│   └── main.py             ← App entry point
├── frontend/
│   ├── d2c/                ← Consumer app (React + TypeScript)
│   ├── portal/             ← Admin/insurer/partner portal (React + TypeScript)
│   └── widget/             ← Embeddable chat widget (React + TypeScript)
├── tests/                  ← Automated tests (38 tests, all offline)
├── alembic/                ← Database migration scripts
├── docs/                   ← This file and other documentation
├── .env.example            ← Template for your .env file
├── docker-compose.yml      ← Starts all six services together
└── requirements.txt        ← Python dependencies
```
