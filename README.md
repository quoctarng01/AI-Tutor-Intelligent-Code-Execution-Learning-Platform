# AI Tutor

An AI-powered Python programming tutor with a 4-level progressive hint system, code execution sandbox, pre/post assessment quizzes, and Likert scale survey collection for research data gathering.

## Features

- **4-Level Progressive Hints**: Adaptive hint system that progressively reveals more information
  - L1/L2: Pre-authored hints (instant delivery)
  - L3/L4: LLM-generated hints with answer leakage validation
- **Code Execution Sandbox**: Secure Python code evaluation with test cases
- **Pre/Post Assessment Quizzes**: Multiple choice and short answer questions
- **Likert Scale Surveys**: Research-quality feedback collection
- **Session Tracking**: A/B testing support (tutor vs. control groups)
- **Monaco Editor**: Professional code editing experience

## Tech Stack

For detailed architecture documentation, see [ARCHITECTURE.md](./ARCHITECTURE.md).

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite, Monaco Editor, Tailwind CSS |
| Backend | FastAPI, Python, SQLAlchemy (async) |
| Database | PostgreSQL |
| Code Execution | Judge0 CE, Python subprocess sandbox |
| AI | OpenAI GPT-4o-mini |
| Auth | JWT (python-jose) |

## Prerequisites

- **PostgreSQL** running on port 5432
- **Python** 3.12 or higher
- **Node.js** 18 or higher
- **Redis** (optional, for caching)
- **OpenAI API Key** (optional, for LLM hints L3/L4)

## Installation

### Backend

```bash
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your DATABASE_URL and API keys

# Run database migrations
alembic upgrade head

# Seed the database with exercises
python data/seed.py

# Start the backend server
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Environment Variables

See [.env.example](./.env.example) for all configuration options.

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | JWT signing key | Yes |
| `OPENAI_API_KEY` | OpenAI API key for LLM hints | No |
| `JUDGE0_API_KEY` | Judge0 RapidAPI key | No |

## Running Tests

```bash
# Backend tests
pytest

# With coverage
pytest --cov=backend

# Frontend type checking
cd frontend && npm run type-check
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Python: Follow PEP 8, use `ruff` for linting
- TypeScript: Use strict mode, run `npm run type-check`

## License

[MIT License](./LICENSE) — *Nguyen Quoc Trang*
