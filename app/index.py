from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LatencyRequest(BaseModel):
    regions: list[str]
    threshold_ms: float

@app.post("/")
async def analyze_latency(request: LatencyRequest):
    # Read JSON file
    with open('q-vercel-latency.json', 'r') as f:
        data = json.load(f)
    
    result = {}
    for region in request.regions:
        records = [r for r in data if r['region'] == region]
        if not records:
            continue
        
        latencies = sorted([r['latency_ms'] for r in records])
        uptimes = [r['uptime_pct'] for r in records]
        
        # Calculate metrics
        avg_lat = sum(latencies) / len(latencies)
        p95_idx = int(len(latencies) * 0.95)
        p95_lat = latencies[min(p95_idx, len(latencies) - 1)]
        avg_up = sum(uptimes) / len(uptimes)
        breaches = sum(1 for lat in latencies if lat > request.threshold_ms)
        
        result[region] = {
            "avg_latency": round(avg_lat, 2),
            "p95_latency": round(p95_lat, 2),
            "avg_uptime": round(avg_up, 2),
            "breaches": breaches
        }
    
    return result