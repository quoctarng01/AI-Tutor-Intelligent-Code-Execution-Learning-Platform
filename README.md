# AI Tutor

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)
![Node](https://img.shields.io/badge/node-18+-339933?logo=node.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)

> An AI-powered Python programming tutor built for educational research. Designed to study how
> progressive hint delivery affects learning outcomes, it combines a secure code execution sandbox
> with a 4-level adaptive hint system, pre/post assessments, and Likert scale surveys — enabling
> rigorous A/B comparisons between tutored and control groups.

## 📺 Project Demo

<p align="center">
  <img src="./assets/image.gif" width="900" alt="AI Tutor Interface Demo">
</p>

> **Key Feature:** The interface above shows the automated hint generation system and the Monaco-based code editor integrated with the Python backend.
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

## Graceful Degradation

This project is fully functional without the optional services:

| Without | Behaviour |
|---------|-----------|
| `OPENAI_API_KEY` | L3/L4 hints are disabled. Students still receive L1/L2 pre-authored hints. The tutor and all assessments remain fully operational. |
| `JUDGE0_API_KEY` | The cloud Judge0 service is unavailable, but code execution falls back to the local Python subprocess sandbox automatically. All test case evaluation continues to work. |
| Redis | Caching is skipped silently. No functionality is lost; responses may be marginally slower under load. |

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

[MIT License](./LICENSE) — Nguyen Quoc Trang