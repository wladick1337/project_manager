from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.redis import close_redis, init_redis
from app.routes.auth import router as auth_router
from app.routes.project import router as projects_router
from app.routes.tasks import router as tasks_router


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


app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
