# GE Pulse

**Factory rhythm, clear.**

GE Pulse is a shop-floor intelligence platform from **S7 Inc** for injection molding and automotive component factories. It combines live machine telemetry, OEE, downtime capture, machine master data, role-based demo screens, and connector-ready edge ingestion.

## What Works Now

- FastAPI backend with JWT auth, demo mode, role-based access, and session timeout.
- Streamlit dashboard branded for GE Pulse and S7 Inc.
- Persistent database support for PostgreSQL on Render and local TimescaleDB/PostgreSQL through Docker.
- Health checks for API, dashboard dependency, database, and simulator.
- Demo factory seed/reset with plants, lines, cells, machines, processes, mold models, shifts, targets, alert rules, connector configs, and users.
- Machine master API: plant, line, cell, machine, process, mold/model, PLC protocol, target, and cycle-time standard.
- Downtime reason capture for machine stop, material shortage, quality issue, changeover, and maintenance.
- OEE API with availability, performance, quality, and loss-tree output.
- Edge connector interfaces for Mitsubishi MC Protocol, Modbus TCP, OPC UA, MQTT, and simulator mode.
- Automated API tests and GitHub Actions CI.

## Demo Credentials

Use the dashboard **Launch Demo** button for passwordless role testing.

Local password login is also available:

```text
Username: admin
Password: admin123
```

Set `DEMO_ADMIN_PASSWORD` to override the local demo password.

## Quick Start

Install dependencies:

```bash
python -m pip install -r ingress-api/requirements.txt
python -m pip install -r dashboard/requirements.txt
python -m pip install -r edge/requirements.txt
```

Run the API:

```bash
cd ingress-api
uvicorn app.main:app --reload --port 8000
```

Run the dashboard:

```bash
cd dashboard
streamlit run Home.py
```

Open:

- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- Dashboard: http://localhost:8501

## Docker Demo

```bash
docker-compose up --build
```

The compose stack includes TimescaleDB/PostgreSQL, the API, the dashboard, and the simulator gateway.

## Render Deployment

`render.yaml` provisions:

- `ge-pulse-postgres`
- `ge-pulse-api`
- `ge-pulse-dashboard`

The API receives `DATABASE_URL` from Render PostgreSQL. SQLite remains available only as a local fallback.

## API Highlights

- `POST /api/v1/auth/demo-login`
- `GET /api/v1/health`
- `GET /api/v1/factory/machines`
- `POST /api/v1/factory/machines`
- `POST /api/v1/demo/reset`
- `GET /api/v1/oee`
- `POST /api/v1/downtime`
- `GET /api/v1/connectors`
- `GET /api/v1/telemetry/latest`

## Test

```bash
pytest -q
```

## Roadmap

1. Harden PostgreSQL migrations with Alembic.
2. Build richer operator, supervisor, maintenance, manager, and admin screens.
3. Add live Andon board, escalation workflow, and notification providers.
4. Move high-volume telemetry to TimescaleDB hypertables or ClickHouse.
5. Add edge offline buffering and production connector configuration UI.
6. Add predictive maintenance and the GE Pulse AI assistant.

## License

MIT. Commercial deployment terms can be added separately for production factory use.
