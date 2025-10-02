from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import json
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Request schema
class TelemetryRequest(BaseModel):
    regions: list[str]
    threshold_ms: float | None = 0  # optional, defaults to 0

# Load telemetry data from file
DATA_FILE = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")
with open(DATA_FILE, "r") as f:
    telemetry = json.load(f)

@app.post("/")
async def analyze(req: TelemetryRequest):
    regions = req.regions
    threshold = req.threshold_ms or 0  # default to 0 if missing

    result = {}
    for region in regions:
        records = [r for r in telemetry if r["region"] == region]
        if not records:
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = int(sum(l > threshold for l in latencies))

        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    return result
