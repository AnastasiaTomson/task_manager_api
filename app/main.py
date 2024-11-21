import yaml
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from prometheus_fastapi_instrumentator import Instrumentator

from starlette.responses import JSONResponse

from app import models
from app.database import engine
from app.routers.tasks import router

# Создание таблиц
models.Base.metadata.create_all(bind=engine)

# Открываем файл openapi.yaml
with open("docs/openapi.yaml", "r", encoding="utf-8") as file:
    custom_openapi = yaml.safe_load(file)

# Создаем приложение FastAPI
app = FastAPI(
    title="Task Manager API",  # Название для Swagger UI
    description="API для управления задачами",
    version="1.0.0",
    docs_url="/docs",  # Оставляем путь для Swagger UI
    openapi_url=None  # Отключаем стандартный JSON OpenAPI
)

# Интеграция метрик
instrumentator = Instrumentator()

# Настройка и активация экспорта метрик
instrumentator.instrument(app).expose(app)


# Настраиваем кастомную спецификацию OpenAPI
@app.get("/openapi.yaml", include_in_schema=False)
def get_openapi_yaml():
    return custom_openapi


# Настройка кастомной документации Swagger UI
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.yaml",  # Указываем на кастомный YAML
        title="Task Manager API Docs"
    )


# Отключаем доступ к стандартной JSON спецификации OpenAPI
@app.get("/openapi.json", include_in_schema=False)
async def openapi_json():
    return JSONResponse(status_code=404, content={"detail": "JSON OpenAPI спецификация недоступна."})


app.include_router(router, prefix="/tasks", tags=["tasks"])
