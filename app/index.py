from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import numpy as np
import os

# Create FastAPI app instance
app = FastAPI()

# Enable CORS for all origins. Note: when allow_origins is ['*'],
# many browsers will ignore Access-Control-Allow-Credentials if
# allow_credentials is True. For a true wildcard + credentials,
# you must set allow_credentials to False or specify explicit origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ---------- models ----------
class LatencyRequest(BaseModel):
    regions: list[str]
    threshold_ms: float

# ---------- helpers ----------
def load_telemetry():
    path = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")
    with open(path) as f:
        records = json.load(f)
    grouped = {}
    for r in records:
        grouped.setdefault(r["region"], []).append(
            {"latency_ms": r["latency_ms"], "uptime": r["uptime_pct"]}
        )
    return grouped

def calc_metrics(latencies, uptimes, threshold):
    return {
        "avg_latency": round(float(np.mean(latencies)), 2),
        "p95_latency": round(float(np.percentile(latencies, 95)), 2),
        "avg_uptime": round(float(np.mean(uptimes)), 2),
        "breaches": int(np.sum(np.array(latencies) > threshold)),
    }

# ---------- routes ----------
@app.get("/")
def health():
    return {"msg": "FastAPI on Vercel works fine! :-) hello rituraj here :-) Oooooo! it working"}

@app.post("/api/latency")
def latency_metrics(body: LatencyRequest):
    telem = load_telemetry()
    resp = []  # Initialize resp as a list
    for reg in body.regions:
        if reg not in telem:
            raise HTTPException(status_code=400, detail=f"region '{reg}' not found")
        lat = [x["latency_ms"] for x in telem[reg]]
        upt = [x["uptime"] for x in telem[reg]]
        resp.append(calc_metrics(lat, upt, body.threshold_ms))
    return resp.json()