# WorkTime

Система учета рабочего времени сотрудников на Django и Django REST Framework.

## Возможности

- JWT API: регистрация, логин, refresh, logout
- Роли `employee` и `manager`
- CRUD задач
- Запуск и остановка таймера с ограничением на один активный таймер
- Защита от конкурентного запуска таймеров
- Дневные и недельные отчеты с фильтрами по дате и сотруднику
- Экспорт отчетов в CSV
- Web UI на Django Templates
- Поиск, фильтрация, пагинация и Django messages
- Docker Compose для `web + db + redis`
- Redis-ready cache слой для активных таймеров
- Тесты на `pytest`

## Стек

- Python 3.12
- Django
- Django REST Framework
- SimpleJWT
- PostgreSQL или SQLite для локального старта
- Redis

## Запуск

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Открыть:

- Web UI: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

## Переменные окружения

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DJANGO_TIME_ZONE`
- `DATABASE_URL`
- `REDIS_URL`

Пример для PostgreSQL:

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/worktime
```

Если `DATABASE_URL` не задан, проект использует SQLite. Также можно задать `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`.

Для старта через Docker:

```bash
cp .env.example .env
docker compose up --build
```

## API

### Auth

- `POST /api/register/`
- `POST /api/login/`
- `POST /api/logout/`
- `POST /api/token/refresh/`

### Tasks

- `GET /api/tasks/`
- `POST /api/tasks/`
- `GET /api/tasks/<id>/`
- `PUT /api/tasks/<id>/`
- `DELETE /api/tasks/<id>/`

### Time Tracking

- `POST /api/time/start/<task_id>/`
- `POST /api/time/stop/<task_id>/`
- `GET /api/time/my/`

### Reports

- `GET /api/reports/daily/`
- `GET /api/reports/weekly/`
- `GET /api/reports/daily/export/`
- `GET /api/reports/weekly/export/`

Параметры фильтрации:

- `date=YYYY-MM-DD`
- `user_id=<id>` для менеджера

## Роли

- `employee`: видит свои задачи, создает задачи, запускает свои таймеры, смотрит свои отчеты
- `manager`: видит все задачи и все отчеты

## Тесты

```bash
pytest
```
