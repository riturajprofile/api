from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import json
from pathlib import Path

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TelemetryRequest(BaseModel):
    regions: list[str]
    threshold_ms: float

# Load telemetry data
def load_telemetry_data():
    possible_paths = [
        Path(__file__).parent / "q-vercel-latency.json",
        Path("app/q-vercel-latency.json"),
        Path("q-vercel-latency.json"),
    ]
    
    for path in possible_paths:
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
    
    raise FileNotFoundError("q-vercel-latency.json not found")

telemetry = load_telemetry_data()

@app.post("/")
async def analyze(req: TelemetryRequest):
    regions = req.regions
    threshold = req.threshold_ms
    
    result = {}
    
    for region in regions:
        # Filter records for this region
        records = [r for r in telemetry if r.get("region") == region]
        
        if not records:
            continue
        
        # Extract latencies and uptimes
        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]
        
        # Calculate metrics
        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = sum(1 for l in latencies if l > threshold)
        
        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }
    
    return result
