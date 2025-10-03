from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello from FastAPI on Vercel"}

handler = Mangum(app)  # Vercel Lambda handler
