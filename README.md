# Task Manager API

**Task Manager API** – это простое REST API для управления задачами с использованием FastAPI и SQLAlchemy.

## Структура проекта

```
task_manager_api/
├── app/
│   ├── crud.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
├── docs/
│   ├── openapi.yaml
├── venv/
├── README.md
├── requirements.txt
└── tasks.db
```

## Требования

- Python 3.8+
- SQLite (встроен в Python)
- Установленные зависимости из `requirements.txt`

## Установка

### 1. Клонирование репозитория

Клонируйте проект из репозитория:

```bash
git clone https://github.com/AnastasiaTomson/task_manager_api.git
cd task_manager_api
```

### 2. Создание виртуального окружения

Создайте виртуальное окружение и активируйте его:

```bash
python -m venv venv
source venv/bin/activate  # Для Windows: venv\Scripts\activate
```

### 3. Установка зависимостей

Установите все необходимые зависимости:

```bash
pip install -r requirements.txt
```

### 4. Настройка базы данных

База данных будет создана автоматически при запуске сервера, используя SQLite. Если хотите, вы можете изменить базу данных на другую в файле `app/database.py`.

```python
# app/database.py
SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"  # Путь к SQLite базе данных
```

## Запуск проекта

### 1. Запуск FastAPI приложения

Для запуска приложения используйте Uvicorn:

```bash
uvicorn app.main:app --reload
```

Это запустит сервер на `http://127.0.0.1:8000`.

### 2. Работа с API

После запуска вы можете взаимодействовать с API через браузер или Postman.

Документация Swagger UI доступна по адресу: http://127.0.0.1:8000/docs.

Также документация OpenAPI доступна по адресу: http://127.0.0.1:8000/openapi.yaml

### 3. Эндпоинты

- **Получить список задач**:
  ```bash
  GET /tasks
  ```

- **Получить задачу по ID**:
  ```bash
  GET /tasks/{task_id}
  ```

- **Создать новую задачу**:
  ```bash
  POST /tasks
  {
      "title": "Новая задача",
      "description": "Описание задачи",
      "status": "В процессе"
  }
  ```

- **Обновить задачу**:
  ```bash
  PUT /tasks/{task_id}
  ```

- **Удалить задачу**:
  ```bash
  DELETE /tasks/{task_id}
  ```