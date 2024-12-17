import logging
import random
import time

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import get_tracer
from prometheus_client import Gauge, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
import yaml

import models
import crud
import schemas
from database import engine
from models import Task

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, APIRouter
from database import SessionLocal

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

# Настройка логирования
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Создаем инструментатор
instrumentator = Instrumentator()
# Кастомные метрики для задач

total_tasks_gauge = Gauge("total_task", "Number of total tasks")
active_tasks_gauge = Gauge("task_statuses_active", "Number of active tasks")
completed_tasks_gauge = Gauge("task_statuses_completed", "Number of completed tasks")

# Инициализация провайдера и экспорта трейсов
resource = Resource(attributes={"service.name": "task-manager"})
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://tempo:4317"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = get_tracer(__name__)

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

router = APIRouter()


# Получение сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Эндпоинт для получения списка всех задач
@router.get("", response_model=list[schemas.Task])
def read_tasks(db: Session = Depends(get_db)):
    with tracer.start_as_current_span("get_tasks") as span:
        delay = random.uniform(0.1, 1.0)  # Случайная задержка
        time.sleep(delay)
        span.set_attribute("task_delay", delay)  # Атрибут спана
        tasks = crud.get_tasks(db)
        if random.choice([True, False]):  # Случайная ошибка
            span.record_exception(Exception("Random error occurred"))
            raise HTTPException(status_code=500, detail="Random error")
        logger.info("GET /tasks request received")
        return tasks


# Эндпоинт для получения задачи по ID
@router.get("/{task_id}", response_model=schemas.Task)
def read_task(task_id: int, db: Session = Depends(get_db)):
    with tracer.start_as_current_span("read_task") as span:
        logger.info(f"GET /tasks/{task_id} request received")
        span.set_attribute("task_id", task_id)
        task = crud.get_task(db, task_id)
        if task is None:
            span.set_status("error")
            span.add_event("Task not found")
            raise HTTPException(status_code=404, detail="Task not found")
        return task


# Эндпоинт для создания новой задачи
@router.post("", response_model=schemas.Task)
async def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    with tracer.start_as_current_span("create_task") as span:
        logger.info("POST /tasks request received")
        span.set_attribute("task_name", task.title)
        new_task = crud.create_task(db, task)
        span.add_event("Task created successfully")
        return new_task


# Эндпоинт для обновления задачи
@router.put("/{task_id}", response_model=schemas.Task)
async def update_task(task_id: int, task: schemas.TaskCreate, db: Session = Depends(get_db)):
    with tracer.start_as_current_span("update_task") as span:
        logger.info(f"PUT /tasks/{task_id} request received")
        span.set_attribute("task_id", task_id)
        db_task = crud.get_task(db, task_id)
        if db_task is None:
            span.set_status("error")
            span.add_event("Task not found")
            raise HTTPException(status_code=404, detail="Task not found")
        updated_task = crud.update_task(db, task_id, task)
        span.add_event("Task updated successfully")
        return updated_task


# Эндпоинт для удаления задачи
@router.delete("/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    with tracer.start_as_current_span("delete_task") as span:
        logger.info(f"DELETE /tasks/{task_id} request received")
        span.set_attribute("task_id", task_id)
        db_task = crud.get_task(db, task_id)
        if db_task is None:
            span.set_status("error")
            span.add_event("Task not found")
            raise HTTPException(status_code=404, detail="Task not found")
        crud.delete_task(db, task_id)
        span.add_event("Task deleted successfully")
        return {"detail": "Задача удалена"}


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
