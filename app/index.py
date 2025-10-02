from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import json
import os
from pathlib import Path

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TelemetryRequest(BaseModel):
    regions: list[str]
    threshold_ms: float | None = None

# Load data file - multiple path resolution strategies for Vercel
def load_telemetry_data():
    possible_paths = [
        Path(__file__).parent / "q-vercel-latency.json",
        Path("app/q-vercel-latency.json"),
        Path("q-vercel-latency.json"),
        Path("/var/task/app/q-vercel-latency.json"),
    ]
    
    for path in possible_paths:
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
    
    raise FileNotFoundError(f"Could not find q-vercel-latency.json in any of: {possible_paths}")

try:
    telemetry = load_telemetry_data()
except Exception as e:
    print(f"Error loading data: {e}")
    telemetry = []

@app.get("/")
async def root():
    return {
        "message": "Telemetry API",
        "endpoints": {
            "POST /": "Analyze telemetry data",
            "GET /health": "Health check",
            "GET /regions": "List available regions"
        },
        "records_loaded": len(telemetry)
    }

@app.post("/")
@app.post("/api")
async def analyze(req: TelemetryRequest):
    if not telemetry:
        raise HTTPException(status_code=500, detail="Telemetry data not loaded")
    
    regions = req.regions
    threshold = req.threshold_ms if req.threshold_ms is not None else 0
    
    if not regions:
        raise HTTPException(status_code=400, detail="No regions provided")
    
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

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "records": len(telemetry),
        "regions": sorted(set(r.get("region") for r in telemetry if r.get("region")))
    }

@app.get("/regions")
async def get_regions():
    """Get all available regions"""
    regions = sorted(set(r.get("region") for r in telemetry if r.get("region")))
    return {"regions": regions}