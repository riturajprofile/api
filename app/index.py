from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            # Read JSON file
            with open('q-vercel-latency.json', 'r') as f:
                data = json.load(f)
            
            # Parse request
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
            
            regions = body.get('regions', [])
            threshold = body.get('threshold_ms', 180)
            
            result = {}
            for region in regions:
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
                breaches = sum(1 for lat in latencies if lat > threshold)
                
                result[region] = {
                    "avg_latency": round(avg_lat, 2),
                    "p95_latency": round(p95_lat, 2),
                    "avg_uptime": round(avg_up, 2),
                    "breaches": breaches
                }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))