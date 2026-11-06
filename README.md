# Freelance Job Fit Radar

Small portfolio MVP: rank sample freelance jobs against a skills profile, explain the match, and expose results through a FastAPI API.

> The included job records are synthetic portfolio fixtures. This project does not currently connect to Upwork or claim access to bid/client data.

## Requirements

- Python 3.12
- `uv`

## Setup (Windows PowerShell)

```powershell
uv sync
uv run uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs> to try the API.

## Endpoints

- `GET /health` — process health check.
- `GET /jobs` — sample jobs ranked against a demo profile; returns score, matched/missing skills, and reasons.

The score is exact skill overlap against the demo profile, not a prediction of whether a client will hire you.

## Tests and lint

```powershell
uv run pytest -q
uv run ruff check .
```

## Next milestone

Add configurable profiles and Telegram notifications. Only integrate a real job source after verifying access permissions, terms, and the actual fields supplied by that source. Missing fields must stay unknown rather than be inferred.
