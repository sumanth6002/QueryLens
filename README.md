# QueryLens

**SQL Schema Design & Query Performance Analyzer**

QueryLens is a full-stack web application for designing database schemas, visualizing ER diagrams, analyzing query execution plans, checking normalization (1NF–BCNF), and receiving index recommendations.

## Architecture

```
Frontend (Vanilla JS, port 5500)
    ↓ REST API
Backend (Flask, port 5000)
    ├── SQLite — app metadata (workspaces, schema snapshots, reports)
    └── MySQL  — per-workspace query databases (querylens_ws_<id>)
```

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Backend | Python 3.11+, Flask, SQLAlchemy |
| App metadata DB | SQLite (dev) or MySQL via `DATABASE_URL` |
| Workspace query DB | MySQL 8+ via `MYSQL_*` env vars |
| Visualization | Mermaid.js (ER), D3.js (EXPLAIN) |
| Auth | JWT (disabled in development — guest user) |

## Features

| Page | Route | Status |
|------|-------|--------|
| Schema Builder | `pages/schema-builder.html` | Create/edit tables, PK/FK, preview & execute DDL |
| ER Diagram | `pages/er-diagram.html` | Mermaid diagram from logical schema |
| EXPLAIN Visualizer | `pages/explain.html` | Real MySQL `EXPLAIN FORMAT=JSON` with fallback |
| Normalization Checker | `pages/normalization.html` | 1NF–BCNF analysis |
| Index Advisor | `pages/index-advisor.html` | Index recommendations from SQL |

**Note:** SQL editor API exists (`/api/workspaces/<id>/sql/*`) but has no dedicated frontend page yet.

## Installation

### Prerequisites

- Python 3.11+
- MySQL 8.0+ (required for EXPLAIN, schema execution, SQL sandbox)
- A static file server for the frontend (Live Server, etc.)

### Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env   # then edit credentials

python -m database.init_db
python app.py
```

API: `http://localhost:5000`

### Frontend

Serve the `frontend/` directory on port 5500 (or update `CORS_ORIGINS` in `.env`).

### Environment variables (`backend/.env`)

```env
# Flask
FLASK_ENV=development
SECRET_KEY=change-me
JWT_SECRET_KEY=change-me

# MySQL for EXPLAIN / schema execution / SQL sandbox (required for query features)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password

# Optional: app metadata on MySQL instead of SQLite
# DATABASE_URL=mysql+pymysql://root:password@localhost:3306/querylens

CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

Test MySQL connectivity:

```bash
python -m explain.test_connection
```

### Health checks

```bash
curl http://localhost:5000/api/health
curl http://localhost:5000/api/health/db
```

### Run tests

```bash
cd backend
python -m unittest tests.test_core -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | API liveness |
| GET | `/api/health/db` | Metadata DB readiness |
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login (JWT) |
| GET | `/api/workspaces` | List workspaces |
| POST | `/api/workspaces` | Create workspace |
| DELETE | `/api/workspaces/<id>` | Delete workspace |
| GET | `/api/workspaces/<id>/schema` | Get logical schema |
| POST | `/api/workspaces/<id>/schema/tables` | Create table |
| PUT | `/api/workspaces/<id>/schema/tables/<name>` | Update table |
| DELETE | `/api/workspaces/<id>/schema/tables/<name>` | Delete table |
| GET | `/api/workspaces/<id>/schema/sql` | Preview CREATE TABLE SQL |
| POST | `/api/workspaces/<id>/schema/execute` | Execute DDL on MySQL |
| GET | `/api/workspaces/<id>/schema/er-diagram` | ER diagram data |
| POST | `/api/workspaces/<id>/explain` | Run EXPLAIN on SELECT |
| POST | `/api/workspaces/<id>/normalization/analyze` | Normalization analysis |
| POST | `/api/workspaces/<id>/index-advisor/analyze` | Index recommendations |
| POST | `/api/workspaces/<id>/sql/execute` | Execute sandbox SQL |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cannot reach the API" | Start backend: `cd backend && python app.py` |
| "MySQL is not configured" | Set `MYSQL_*` in `backend/.env` and restart backend |
| "Table does not exist" in EXPLAIN | Define table in Schema Builder (same workspace); schema auto-syncs before EXPLAIN |
| ER diagram empty | Add tables in Schema Builder first |
| Duplicate workspace name | Names must be unique per user |

## Development status

Authentication is **temporarily disabled**. All routes use a shared guest user. JWT code remains for re-enablement.

## License

MIT
