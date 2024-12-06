from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from prometheus_client import Gauge, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
import yaml

from app import models
from app.database import engine, SessionLocal
from app.models import Task
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

# Создаем инструментатор
instrumentator = Instrumentator()
# Кастомные метрики для задач

total_tasks_gauge = Gauge("total_task", "Number of total tasks")
active_tasks_gauge = Gauge("task_statuses_active", "Number of active tasks")
completed_tasks_gauge = Gauge("task_statuses_completed", "Number of completed tasks")


# Функция для обновления кастомных метрик
def update_task_metrics():
    # Получаем сессию базы данных
    db = SessionLocal()

    # Получаем задачи с разными статусами
    total_tasks = db.query(Task).count()  # Общее количество задач
    active_tasks = db.query(Task).filter(Task.status != 'завершено').count()  # Количество активных задач
    completed_tasks = total_tasks - active_tasks  # Количество завершенных задач

    # Обновляем метрики
    total_tasks_gauge.set(total_tasks)
    active_tasks_gauge.set(active_tasks)  # Устанавливаем значение для активных задач
    completed_tasks_gauge.set(completed_tasks)  # Устанавливаем значение для завершенных задач

    db.close()  # Закрываем сессию после выполнения запроса


# Middleware для обновления кастомных метрик при каждом запросе
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Обновляем метрики перед обработкой запроса
        update_task_metrics()

        # Обрабатываем запрос дальше
        response = await call_next(request)

        return response


# Добавляем middleware в приложение
app.add_middleware(MetricsMiddleware)

# Добавляем кастомную метрику
instrumentator.instrument(app).expose(app)

app.include_router(router, prefix="/tasks", tags=["tasks"])


# Настроим метрики Prometheus для кастомных метрик
@app.get("/metrics")
def metrics():
    # Возвращаем как стандартные, так и кастомные метрики
    return Response(generate_latest(), media_type="text/plain")


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
