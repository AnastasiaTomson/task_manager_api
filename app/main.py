import yaml
from fastapi import FastAPI, Depends, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from sqlalchemy.orm import Session

from starlette.responses import JSONResponse

from app import crud, models, schemas
from app.database import SessionLocal, engine

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


# Получение сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Эндпоинт для получения списка всех задач
@app.get("/tasks", response_model=list[schemas.Task])
def read_tasks(db: Session = Depends(get_db)):
    tasks = crud.get_tasks(db)
    return tasks


# Эндпоинт для получения задачи по ID
@app.get("/tasks/{task_id}", response_model=schemas.Task)
def read_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


# Эндпоинт для создания новой задачи
@app.post("/tasks", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db, task)


# Эндпоинт для обновления задачи
@app.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, task: schemas.TaskCreate, db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return crud.update_task(db, task_id, task)


# Эндпоинт для удаления задачи
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    crud.delete_task(db, task_id)
    return {"detail": "Задача удалена"}
