from prometheus_client import Counter
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, APIRouter
from app import crud, schemas
from app.database import SessionLocal

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
    tasks = crud.get_tasks(db)
    return tasks


# Эндпоинт для получения задачи по ID
@router.get("/{task_id}", response_model=schemas.Task)
def read_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


# Эндпоинт для создания новой задачи
@router.post("", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db, task)


# Эндпоинт для обновления задачи
@router.put("/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, task: schemas.TaskCreate, db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return crud.update_task(db, task_id, task)


# Эндпоинт для удаления задачи
@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    crud.delete_task(db, task_id)
    return {"detail": "Задача удалена"}
