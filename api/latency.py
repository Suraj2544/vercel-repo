from __future__ import annotations

import math
import statistics
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

DATA_PATH = Path(__file__).resolve().parent.parent / "q-vercel-latency.json"


class TelemetrySample(BaseModel):
    region: str
    service: str
    latency_ms: float = Field(..., ge=0)
    uptime_pct: float = Field(..., ge=0, le=100)
    timestamp: int


class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: float = Field(..., gt=0)

    @field_validator("regions")
    def validate_regions(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("regions must contain at least one region identifier")
        return value


class RegionMetrics(BaseModel):
    region: str
    avg_latency: float | None
    p95_latency: float | None
    avg_uptime: float | None
    breaches: int


class MetricsResponse(BaseModel):
    metrics: List[RegionMetrics]


@lru_cache(maxsize=1)
def load_samples() -> List[TelemetrySample]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Telemetry data not found at {DATA_PATH}")
    raw = DATA_PATH.read_text(encoding="utf-8")
    import json

    data = json.loads(raw)
    return [TelemetrySample(**item) for item in data]


def percentile(values: Iterable[float], percentile_rank: float) -> float:
    values_list = sorted(values)
    count = len(values_list)
    if count == 0:
        raise ValueError("Cannot compute percentile of empty sequence")

    index = max(math.ceil(percentile_rank * count) - 1, 0)
    return values_list[min(index, count - 1)]


def compute_metrics(samples: Iterable[TelemetrySample], threshold: float) -> Dict[str, RegionMetrics]:
    buckets: Dict[str, List[TelemetrySample]] = {}
    for sample in samples:
        key = sample.region.lower()
        buckets.setdefault(key, []).append(sample)

    metrics: Dict[str, RegionMetrics] = {}
    for region_key, region_samples in buckets.items():
        region_label = region_samples[0].region
        latencies = [item.latency_ms for item in region_samples]
        uptimes = [item.uptime_pct for item in region_samples]
        breaches = sum(latency > threshold for latency in latencies)

        avg_latency = statistics.fmean(latencies)
        avg_uptime = statistics.fmean(uptimes)
        p95 = percentile(latencies, 0.95)

        metrics[region_key] = RegionMetrics(
            region=region_label,
            avg_latency=round(avg_latency, 2),
            p95_latency=round(p95, 2),
            avg_uptime=round(avg_uptime, 3),
            breaches=breaches,
        )

    return metrics


app = FastAPI(title="eShopCo Latency Metrics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.post("/api/latency", response_model=MetricsResponse)
def get_latency_metrics(payload: LatencyRequest) -> MetricsResponse:
    try:
        samples = load_samples()
    except FileNotFoundError as err:
        raise HTTPException(status_code=500, detail=str(err)) from err

    metrics_by_region = compute_metrics(samples, payload.threshold_ms)

    response: List[RegionMetrics] = []
    for region in payload.regions:
        region_key = region.lower()
        region_metrics = metrics_by_region.get(region_key)

        if region_metrics is None:
            response.append(
                RegionMetrics(
                    region=region,
                    avg_latency=None,
                    p95_latency=None,
                    avg_uptime=None,
                    breaches=0,
                )
            )
        else:
            # Preserve the originally requested casing for clarity
            response.append(
                RegionMetrics(
                    region=region,
                    avg_latency=region_metrics.avg_latency,
                    p95_latency=region_metrics.p95_latency,
                    avg_uptime=region_metrics.avg_uptime,
                    breaches=region_metrics.breaches,
                )
            )

    return MetricsResponse(metrics=response)


try:
    from mangum import Mangum

    handler = Mangum(app)
except ImportError:  # pragma: no cover - optional dependency for Vercel/AWS
    handler = None
