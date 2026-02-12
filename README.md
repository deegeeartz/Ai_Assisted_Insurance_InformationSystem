# InsurBridge AI

## Environment Variables

Create a `.env` file with:

```env
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=insurbridge
GOOGLE_API_KEY=your_gemini_api_key
ENCRYPTION_KEY=your_fernet_key
REDIS_URL=redis://localhost:6379
```

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
