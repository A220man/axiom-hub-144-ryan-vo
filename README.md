# Axiom Hub — Ryan Vo

> Work in progress. This checkpoint may be incomplete or fail tests. See PLAN.md and STATUS.md before use.


The design language that makes your AI harness better at design.

## Quick Start

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend (React)

```bash
cd frontend
npm install
npm start
```

## Project Structure

```
axiom-hub-144-ryan-vo/
├── feature-plan.json
├── PLAN.md
├── README.md
├── STATUS.md
├── CHANGELOG.md
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── test_main.py
├── frontend/
│   ├── package.json
│   ├── public/index.html
│   └── src/
│       ├── index.js
│       ├── App.js
│       └── App.css
└── tests/
```

## API Endpoints

- GET /api/health - Health check
- GET /api/version - Version info

## Development

Incremental development. See feature-plan.json and PLAN.md.

## License

Apache-2.0
Maintainer: Ryan Vo <ryandtvo@gmail.com>
