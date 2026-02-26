# Klarnow Voice Agent API

Backend for the Klarnow voice agent: VAPI webhooks, tool endpoints (leads, fit-check, qualification, handoff, bookings), and Cal.com integration for availability and booking.

## Requirements

- Python 3.13+
- PostgreSQL
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Environment variables

Create a `.env` file in the project root:

| Variable                | Required | Description                                                                     |
| ----------------------- | -------- | ------------------------------------------------------------------------------- |
| `DATABASE_URL`          | Yes      | PostgreSQL connection string (e.g. `postgresql://user:pass@localhost/dbname`)   |
| `SERVER_BASE_URL`       | Yes      | Base URL of this API (e.g. `http://localhost:8000`) for VAPI tool URLs          |
| `VAPI_API_TOKEN`        | Yes      | VAPI API token (min 20 chars) for creating assistants                           |
| `JWT_SECRET`            | No\*     | Secret for JWT auth (min 32 chars; default dev value exists; set in production) |
| `VAPI_TOOL_API_KEY`     | No       | Legacy single key for tools (SaaS uses per-agent keys)                          |
| `CAL_COM_API_KEY`       | No       | Platform default Cal.com key (agents can use their own)                         |
| `CAL_COM_EVENT_TYPE_ID` | No       | Platform default event type ID                                                  |
| `ASSISTANT_ID`          | No       | Legacy single assistant ID                                                      |
| `LOG_LEVEL`             | No       | Logging level (default: `INFO`)                                                 |
| `DEBUG`                 | No       | Set to `true` to log request body/headers (default: `false`)                    |
| `CAL_COM_BASE_URL`      | No       | Cal.com API base URL (default: `https://api.cal.com/v2`)                        |
| `CORS_ORIGINS`          | No       | Comma-separated origins (default includes localhost)                            |

## Run the API

```bash
# Install dependencies (uv)
uv sync

# Run migrations
uv run alembic upgrade head

# Start the server
uv run uvicorn app.main:app --reload
```

With pip:

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

API docs: `http://localhost:8000/docs` (Swagger UI).

## Register VAPI tools

After deploying the API, register the tools with your VAPI assistant (creates/updates tools and attaches them to `ASSISTANT_ID`):

```bash
uv run python -m app.services.vapi_service
```

Or with pip:

```bash
python -m app.services.vapi_service
```

## Project layout

- `app/` – FastAPI app, routers (auth, orgs, tools, bookings, webhooks), services, models, schemas
- `alembic/` – Database migrations (run these yourself after adding new models)
- `frontend/` – Next.js dashboard (auth, orgs, agents, calls, leads, bookings)

## Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local
npm run dev
```

Open http://localhost:3000 to sign up, create organizations, add agents, and view calls/leads.
