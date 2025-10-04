from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import numpy as np
import json
import os

app = FastAPI(title="eShopCo Latency Monitor", version="1.0.0")

# Enable CORS for all origins (as required)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow any origin for dashboard access
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods including POST
    allow_headers=["*"],  # Allow all headers
)

# Request model
class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

# Response model
class RegionMetrics(BaseModel):
    avg_latency: float
    p95_latency: float
    avg_uptime: float
    breaches: int

class LatencyResponse(BaseModel):
    emea: RegionMetrics
    amer: RegionMetrics

# Sample telemetry data (fallback if file not found)
SAMPLE_TELEMETRY = {
    "emea": [
        {"latency_ms": 145, "uptime": 99.9},
        {"latency_ms": 167, "uptime": 99.8},
        {"latency_ms": 123, "uptime": 99.9},
        {"latency_ms": 189, "uptime": 99.7},
        {"latency_ms": 156, "uptime": 99.8},
        {"latency_ms": 134, "uptime": 99.9},
        {"latency_ms": 178, "uptime": 99.6},
        {"latency_ms": 142, "uptime": 99.9},
        {"latency_ms": 165, "uptime": 99.8},
        {"latency_ms": 149, "uptime": 99.9}
    ],
    "amer": [
        {"latency_ms": 98, "uptime": 99.95},
        {"latency_ms": 112, "uptime": 99.92},
        {"latency_ms": 87, "uptime": 99.97},
        {"latency_ms": 125, "uptime": 99.89},
        {"latency_ms": 103, "uptime": 99.94},
        {"latency_ms": 95, "uptime": 99.96},
        {"latency_ms": 118, "uptime": 99.91},
        {"latency_ms": 92, "uptime": 99.98},
        {"latency_ms": 108, "uptime": 99.93},
        {"latency_ms": 101, "uptime": 99.95}
    ]
}

def load_telemetry_data():
    """Load telemetry data from file or use sample data"""
    try:
        # Try to load from the sample file
        if os.path.exists("q-vercel-latency.json"):
            with open("q-vercel-latency.json", "r") as f:
                return json.load(f)
        else:
            # Return sample data if file not found
            return SAMPLE_TELEMETRY
    except Exception as e:
        print(f"Error loading telemetry data: {e}")
        return SAMPLE_TELEMETRY

def calculate_metrics(latencies: List[float], uptimes: List[float], threshold_ms: float) -> Dict[str, float]:
    """Calculate latency and uptime metrics"""
    if not latencies:
        return {
            "avg_latency": 0.0,
            "p95_latency": 0.0,
            "avg_uptime": 0.0,
            "breaches": 0
        }
    
    # Calculate average latency
    avg_latency = float(np.mean(latencies))
    
    # Calculate 95th percentile latency
    p95_latency = float(np.percentile(latencies, 95))
    
    # Calculate average uptime
    avg_uptime = float(np.mean(uptimes))
    
    # Count breaches (latency above threshold)
    breaches = sum(1 for latency in latencies if latency > threshold_ms)
    
    return {
        "avg_latency": round(avg_latency, 2),
        "p95_latency": round(p95_latency, 2),
        "avg_uptime": round(avg_uptime, 2),
        "breaches": breaches
    }

@app.post("/api/latency", response_model=Dict[str, Any])
async def get_latency_metrics(request: LatencyRequest):
    """
    Process latency telemetry data and return per-region metrics.
    
    Accepts POST request with JSON body:
    {
        "regions": ["emea", "amer"],
        "threshold_ms": 155
    }
    
    Returns per-region metrics including avg_latency, p95_latency, avg_uptime, and breaches.
    """
    try:
        # Load telemetry data
        telemetry_data = load_telemetry_data()
        
        # Validate requested regions
        for region in request.regions:
            if region not in telemetry_data:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Region '{region}' not found in telemetry data"
                )
        
        # Calculate metrics for each requested region
        response = {}
        
        for region in request.regions:
            region_data = telemetry_data[region]
            latencies = [record["latency_ms"] for record in region_data]
            uptimes = [record["uptime"] for record in region_data]
            
            metrics = calculate_metrics(latencies, uptimes, request.threshold_ms)
            
            response[region] = {
                "avg_latency": metrics["avg_latency"],
                "p95_latency": metrics["p95_latency"],
                "avg_uptime": metrics["avg_uptime"],
                "breaches": metrics["breaches"]
            }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "eShopCo Latency Monitor"}

@app.get("/api/health")
async def api_health():
    """API health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}