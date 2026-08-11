import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Import your routers
from app.api.v1 import leaf  # Adjust import based on your folder structure

app = FastAPI(
    title="SIH Smart Precision Agriculture API",
    version="1.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    # Explicit origins (e.g., http://localhost:3000 for local Next.js dev)
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure the uploads directory exists before mounting static files
UPLOAD_DIR = os.path.join("uploads", "leaf_scans")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount local uploads directory so Next.js can render uploaded images via URL
# URL format: http://localhost:8000/static/leaf_scans/<filename>.jpg
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# Include feature routers
app.include_router(leaf.router)

@app.get("/health")
def health_check():
    return {"status": "online", "system": "SIH Backend Core Active"}

@app.get("/", response_class=HTMLResponse)
def root():
    return """<!DOCTYPE html>
<html>
  <head><title>SIH Backend</title></head>
  <body style="background:#0f172a;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center;">
    <div>
      <h1>🎉 Congrats, you made it!</h1>
      <p>SIH Backend is live and running.</p>
    </div>
  </body>
</html>"""