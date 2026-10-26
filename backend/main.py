from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Axiom Hub", description="The design language that makes your AI harness better at design")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "axiom-hub"}

@app.get("/api/version")
async def version():
    return {"version": "0.1.0", "name": "axiom-hub-144-ryan-vo"}
