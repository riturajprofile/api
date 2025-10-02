from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

class TelemetryRequest(BaseModel):
    regions: list[str]
    threshold_ms: float | None = 0

# Load data file
DATA_FILE = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")

with open(DATA_FILE) as f:
    telemetry = json.load(f)

@app.post("/")
async def analyze(req: TelemetryRequest):
    regions = req.regions
    threshold = req.threshold_ms if req.threshold_ms is not None else 0
    
    result = {}
    
    for region in regions:
        # Filter records for this region
        records = [r for r in telemetry if r.get("region") == region]
        
        if not records:
            result[region] = {
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0,
            }
            continue
        
        # Extract latencies and uptimes
        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]
        
        # Calculate metrics
        avg_latency = round(float(np.mean(latencies)), 2)
        p95_latency = round(float(np.percentile(latencies, 95)), 2)
        avg_uptime = round(float(np.mean(uptimes)), 3)
        breaches = int(sum(1 for l in latencies if l > threshold))
        
        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }
    
    return result