from fastapi import FastAPI

from app.routes.auth import router as auth_router
from app.routes.project import router as projects_router
from app.routes.tasks import router as tasks_router
from app.redis import close_redis, init_redis

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код до yield выполняется ДО запуска приема запросов
    await init_redis()
    yield
    # Код после yield выполняется ПРИ graceful shutdown сервера
    await close_redis()
    
app = FastAPI(title="TaskFlow API", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(tasks_router)


@app.get("/")
def health():
    return {"status": "ok"}
