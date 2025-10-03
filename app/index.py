from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Embedded data
DATA = [
    {"region": "apac", "service": "catalog", "latency_ms": 142.93, "uptime_pct": 99.191, "timestamp": 20250301},
    {"region": "apac", "service": "checkout", "latency_ms": 206.2, "uptime_pct": 98.217, "timestamp": 20250302},
    {"region": "apac", "service": "support", "latency_ms": 210.98, "uptime_pct": 97.188, "timestamp": 20250303},
    {"region": "apac", "service": "support", "latency_ms": 126.58, "uptime_pct": 98.599, "timestamp": 20250304},
    {"region": "apac", "service": "recommendations", "latency_ms": 194.82, "uptime_pct": 98.088, "timestamp": 20250305},
    {"region": "apac", "service": "catalog", "latency_ms": 138.68, "uptime_pct": 98.777, "timestamp": 20250306},
    {"region": "apac", "service": "analytics", "latency_ms": 111.97, "uptime_pct": 97.703, "timestamp": 20250307},
    {"region": "apac", "service": "analytics", "latency_ms": 161.04, "uptime_pct": 98.231, "timestamp": 20250308},
    {"region": "apac", "service": "recommendations", "latency_ms": 197.94, "uptime_pct": 98.132, "timestamp": 20250309},
    {"region": "apac", "service": "recommendations", "latency_ms": 211.45, "uptime_pct": 99.032, "timestamp": 20250310},
    {"region": "apac", "service": "analytics", "latency_ms": 169.93, "uptime_pct": 98.584, "timestamp": 20250311},
    {"region": "apac", "service": "payments", "latency_ms": 189.98, "uptime_pct": 98.109, "timestamp": 20250312},
    {"region": "emea", "service": "analytics", "latency_ms": 117.62, "uptime_pct": 98.77, "timestamp": 20250301},
    {"region": "emea", "service": "recommendations", "latency_ms": 156.09, "uptime_pct": 97.441, "timestamp": 20250302},
    {"region": "emea", "service": "checkout", "latency_ms": 171.36, "uptime_pct": 99.269, "timestamp": 20250303},
    {"region": "emea", "service": "analytics", "latency_ms": 135.25, "uptime_pct": 98.543, "timestamp": 20250304},
    {"region": "emea", "service": "checkout", "latency_ms": 113.35, "uptime_pct": 97.872, "timestamp": 20250305},
    {"region": "emea", "service": "support", "latency_ms": 224.92, "uptime_pct": 98.268, "timestamp": 20250306},
    {"region": "emea", "service": "recommendations", "latency_ms": 154.83, "uptime_pct": 99.205, "timestamp": 20250307},
    {"region": "emea", "service": "payments", "latency_ms": 207.53, "uptime_pct": 97.474, "timestamp": 20250308},
    {"region": "emea", "service": "catalog", "latency_ms": 182.65, "uptime_pct": 98.107, "timestamp": 20250309},
    {"region": "emea", "service": "support", "latency_ms": 159.9, "uptime_pct": 97.407, "timestamp": 20250310},
    {"region": "emea", "service": "payments", "latency_ms": 125.72, "uptime_pct": 99.468, "timestamp": 20250311},
    {"region": "emea", "service": "payments", "latency_ms": 160.78, "uptime_pct": 98.452, "timestamp": 20250312},
    {"region": "amer", "service": "checkout", "latency_ms": 225.15, "uptime_pct": 97.916, "timestamp": 20250301},
    {"region": "amer", "service": "catalog", "latency_ms": 152.02, "uptime_pct": 97.653, "timestamp": 20250302},
    {"region": "amer", "service": "catalog", "latency_ms": 125.1, "uptime_pct": 97.642, "timestamp": 20250303},
    {"region": "amer", "service": "recommendations", "latency_ms": 195.81, "uptime_pct": 98.24, "timestamp": 20250304},
    {"region": "amer", "service": "recommendations", "latency_ms": 195.32, "uptime_pct": 98.935, "timestamp": 20250305},
    {"region": "amer", "service": "catalog", "latency_ms": 223.92, "uptime_pct": 97.695, "timestamp": 20250306},
    {"region": "amer", "service": "checkout", "latency_ms": 182.8, "uptime_pct": 98.11, "timestamp": 20250307},
    {"region": "amer", "service": "payments", "latency_ms": 178.61, "uptime_pct": 99.27, "timestamp": 20250308},
    {"region": "amer", "service": "catalog", "latency_ms": 207.78, "uptime_pct": 99.37, "timestamp": 20250309},
    {"region": "amer", "service": "support", "latency_ms": 146.07, "uptime_pct": 98.178, "timestamp": 20250310},
    {"region": "amer", "service": "payments", "latency_ms": 145.07, "uptime_pct": 99.165, "timestamp": 20250311},
    {"region": "amer", "service": "catalog", "latency_ms": 118.72, "uptime_pct": 99.032, "timestamp": 20250312}
]

class LatencyRequest(BaseModel):
    regions: list[str]
    threshold_ms: float

@app.post("/api")
async def analyze_latency(request: LatencyRequest):
    result = {}
    for region in request.regions:
        records = [r for r in DATA if r['region'] == region]
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
handler = Mangum(app)
