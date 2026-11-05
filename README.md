```markdown
# Project Manager API (TaskFlow)

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=flat&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)

Высокопроизводительный асинхронный RESTful API для управления проектами и задачами. 

Проект спроектирован с упором на production-grade практики: изоляция данных пользователей, кэширование по паттерну Cache-Aside с инвалидацией, защита эндпоинтов от подбора паролей через Rate Limiting, автоматические миграции, детерминированные тесты и CI/CD пайплайн.

---

## 🛠 Стек технологий

* **Фреймворк:** FastAPI (Python 3.12)
* **ORM & Миграции:** SQLAlchemy 2.0 (AsyncIO + asyncpg), Alembic
* **База данных:** PostgreSQL 16 (каскадные FK, составные B-tree индексы)
* **Кэширование & Защита:** Redis 7 (кэширование списков, Fixed Window Rate Limiting)
* **Аутентификация:** OAuth2 Password Bearer, JWT (HS256), bcrypt
* **Валидация & Настройки:** Pydantic v2, `pydantic-settings`
* **Пакетный менеджер:** `uv` (ультрабыстрая сборка зависимостей)
* **Инфраструктура & CI:** Docker, Docker Compose, GitHub Actions (Ruff, Pytest AsyncIO)

---

## 🏗 Архитектурные особенности

1. **Полная асинхронность (I/O non-blocking):**  
   Все операции с PostgreSQL и Redis выполняются без блокировки event loop через `async/await`.
2. **Паттерн Cache-Aside & Инвалидация кэша:**  
   Списки задач кэшируются в Redis по составному ключу (учитывающему страницу, размер выборки, статус и приоритет). При мутациях (`POST`, `PATCH`, `DELETE`) кэш соответствующего проекта моментально инвалидируется.
3. **Безопасность и Rate Limiting:**  
   Кастомная зависимость `RateLimiter` защищает чувствительные роуты от brute-force атак и флуда, возвращая `429 Too Many Requests`.
4. **Стандартизированный контракт ошибок:**  
   Глобальные обработчики исключений унифицируют ответы сервиса: ошибки валидации (422), кастомные HTTP-ошибки и сбои (500) возвращаются в едином предсказуемом JSON-формате.

---

## 📂 Структура проекта

```text
├── .github/workflows/
│   └── tests.yml            # CI пайплайн: Ruff линтинг, форматирование, тесты
├── alembic/                 # Конфигурация и версионирование миграций БД
├── app/
│   ├── routes/              # Эндпоинты API (auth, project, tasks)
│   ├── schemas1/            # Дополнительные схемы (pagination)
│   ├── config.py            # Настройки приложения через pydantic-settings
│   ├── database.py          # Инициализация async_sessionmaker
│   ├── deps.py              # Зависимости FastAPI (get_current_user, get_db)
│   ├── exceptions.py        # Единые обработчики исключений
│   ├── main.py              # Инициализация приложения и lifespan
│   ├── models.py            # Декларативные ORM-модели SQLAlchemy
│   ├── rate_limiter.py      # Логика ограничения частоты запросов
│   ├── redis.py             # Синглтон-клиент Redis
│   ├── schemas.py           # Основные Pydantic-схемы
│   └── security.py          # Хэширование паролей и генерация JWT
├── tests/                   # Набор асинхронных тестов (pytest-asyncio)
│   ├── conftest.py          # Фикстуры тестовой БД и изоляции Redis
│   └── test_*.py            # Тесты авторизации, проектов, задач, исключений
├── docker-compose.yml       # Стек для локальной разработки (app, postgres, redis)
├── Dockerfile               # Production-образ на базе python:3.12-slim
├── pyproject.toml           # Конфигурация проекта, зависимостей и линтеров
└── uv.lock                  # Зафиксированные версии пакетов для детерминированной сборки

```

---

## 🚀 Быстрый запуск

### Вариант 1: Запуск через Docker Compose (рекомендуется)

Все сервисы (API, PostgreSQL и Redis) поднимаются и линкуются одной командой.

1. **Клонируйте репозиторий:**
```bash
git clone [https://github.com/your-username/project_manager.git](https://github.com/your-username/project_manager.git)
cd project_manager

```


2. **Создайте файл переменных окружения:**
```bash
cp .env.example .env

```


3. **Запустите контейнеры:**
```bash
docker compose up --build -d

```



После запуска сервис автоматически применит миграции. Документация будет доступна по адресам:

* **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Вариант 2: Локальная разработка (с `uv`)

1. Установите зависимости:
```bash
uv sync

```


2. Запустите инфраструктуру БД и кэша:
```bash
docker compose up -d db redis

```


3. Примените миграции:
```bash
uv run alembic upgrade head

```


4. Запустите dev-сервер:
```bash
uv run uvicorn app.main:app --reload

```



---

## ⚙️ Переменные окружения (`.env`)

| Переменная | Описание | Пример |
| --- | --- | --- |
| `DATABASE_URL` | Строка подключения к БД | `postgresql+asyncpg://user:pass@localhost:5432/db` |
| `REDIS_URL` | URL подключения к Redis | `redis://127.0.0.1:6379/0` |
| `SECRET_KEY` | Ключ подписи JWT | `your-secure-secret-key` |
| `ALGORITHM` | Алгоритм шифрования токенов | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни access-токена | `30` |

---

## 🧪 Тестирование и качество кода

В проекте настроена автоматическая изоляция тестов: БД очищается через транзакции, а Redis сбрасывается перед каждым прогоном.

```bash
# Запуск тестов
uv run pytest -v

# Проверка линтером Ruff
uv run ruff check .

# Проверка форматирования
uv run ruff format --check .
