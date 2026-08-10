from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="SIH Smart Precision Agriculture API",
    version="1.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "online", "system": "SIH Backend Core Active"}

@app.get("/", response_class=HTMLResponse)
def root():
    return """<html><body style="background:#0f172a;color:#fff;font-family:sans-serif;
    display:flex;align-items:center;justify-content:center;height:100vh;text-align:center;">
    <div><h1>🎉 Congrats, you made it!</h1><p>SIH Backend is live and running.</p></div>
    </body></html>"""