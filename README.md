# SentryRouter

A resilient multi-provider LLM gateway and routing engine with circuit breaking, fallback support, and controllable testing providers.

## Project Structure

```text
sentry-router/
├── app/
│   ├── main.py              # FastAPI app, routes, provider dispatch
│   ├── providers/
│   │   ├── base.py          # Abstract BaseLLMProvider interface
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   └── mock_provider.py # Controllable fail/slow provider for testing
│   ├── core/
│   │   ├── config.py        # Pydantic Settings & environment variables
│   │   └── models.py        # Pydantic schemas (requests, responses, enums)
│   └── db/
│       └── postgres.py      # Async SQLAlchemy session and health checks
├── docker-compose.yml       # api, redis, postgres setup
├── Dockerfile               # Multi-stage/lightweight python container
├── requirements.txt         # Core dependencies
└── tests/                   # Pytest suite
    ├── test_api.py
    └── test_mock_provider.py
```

## Getting Started

### 1. Local Environment Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
```

### 2. Run with Docker Compose

Start the API, PostgreSQL, and Redis instances:

```bash
docker-compose up --build
```

- API: [http://localhost:8000](http://localhost:8000)
- Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Endpoint: [http://localhost:8000/health](http://localhost:8000/health)

### 3. Run Tests

```bash
pytest
```
