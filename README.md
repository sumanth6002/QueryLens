# QueryLens

**SQL Schema Design & Query Performance Analyzer**

A full-stack web application for designing database schemas, executing SQL safely, visualizing ER diagrams, analyzing query execution plans, checking normalization (1NF–BCNF), and receiving intelligent index recommendations.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Backend | Python, Flask, SQLAlchemy |
| Database | MySQL |
| Auth | JWT, Werkzeug password hashing |
| Visualization | Mermaid.js (ER), D3.js (EXPLAIN) |

## Project Structure

```
querylens/
├── backend/
│   ├── app.py              # Application factory
│   ├── config.py           # Environment-based configuration
│   ├── requirements.txt
│   ├── routes/             # Flask blueprints (URL routing)
│   ├── controllers/        # Request handlers
│   ├── services/           # Business logic
│   ├── models/             # SQLAlchemy ORM models
│   ├── database/           # Connection, init scripts, SQL helpers
│   ├── middleware/         # Auth, error handling
│   └── utils/              # Shared helpers
└── frontend/
    ├── index.html
    ├── css/
    ├── js/
    ├── pages/
    └── assets/
```

## Getting Started

### Prerequisites

- Python 3.11+
- MySQL 8.0+
- A static file server for the frontend (e.g. Live Server extension)

### Backend Setup

```bash
cd querylens/backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # then edit with your credentials

# Create database + tables
python -m database.init_db

python app.py
```

The API runs at `http://localhost:5000`.

### Frontend Setup

Serve the `frontend/` directory with any static file server on port 5500 (or update `CORS_ORIGINS` in `.env`).

### Health Check

```bash
curl http://localhost:5000/api/health
curl http://localhost:5000/api/health/db
```

Expected responses:

```json
{"status": "ok", "service": "QueryLens API"}
{"status": "ok", "database": "connected"}
```

### Database Connection Test (standalone)

```bash
python -m database.test_connection
```

## Development Status

Authentication is **temporarily disabled** for development. All API routes are open and use a default guest user internally. Auth code remains in the repo for re-enablement later.

- [x] Project skeleton & Flask app factory
- [x] Database foundation (MySQL, User & Workspace models)
- [x] Authentication (register, login, JWT, logout)
- [x] Workspace management
- [x] Schema builder
- [x] SQL editor
- [x] ER diagram
- [x] EXPLAIN visualizer
- [x] Normalization checker
- [x] Index advisor

## License

MIT
