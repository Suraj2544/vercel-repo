# eShopCo Latency Metrics API

Serverless FastAPI endpoint for computing latency and uptime metrics from telemetry samples.

## Features

- Computes per-region average latency, 95th percentile latency, average uptime, and threshold breach counts.
- Accepts POST payloads specifying regions of interest and latency thresholds.
- Adds CORS support for POST requests from any origin, making it dashboard-friendly.
- Packs cached telemetry data from `q-vercel-latency.json`.

## Project Layout

```
api/
  latency.py        # FastAPI endpoint definition
requirements.txt    # Python dependencies
q-vercel-latency.json  # Sample telemetry dataset
vercel.json         # Vercel function/runtime configuration
```

## Local Development

1. Create and activate a virtual environment (`python -m venv .venv` followed by activation).
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Launch a development server:

```powershell
uvicorn api.latency:app --reload
```

4. Test the endpoint locally:

```powershell
curl -X POST http://127.0.0.1:8000/api/latency -H "Content-Type: application/json" -d '{"regions":["apac","amer"],"threshold_ms":162}'
```

## Running Tests

```powershell
pytest
```

## Deploying to Vercel

1. Log in to Vercel (`vercel login`).
2. Create the project (one-time):

```powershell
vercel --prod
```

3. For later updates, deploy with:

```powershell
vercel deploy --prod
```

Once deployed, your production endpoint will be available at:

```
https://<your-vercel-project>.vercel.app/api/latency
```

Replace `<your-vercel-project>` with the generated project name or a custom domain.
