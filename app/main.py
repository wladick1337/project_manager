from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.routes.project import router as projects_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(projects_router)

@app.get("/")
def health():
    return{"status": "ok"}