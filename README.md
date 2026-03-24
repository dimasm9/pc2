# Система учёта и реализации оборудования (MVP)

Внутреннее веб-приложение на Django для учёта оборудования, бронирования, фиксации осмотров, печати документов и контроля статусов.

## Что реализовано
- Django + DRF + PostgreSQL.
- Роли через группы: `admin`, `manager`, `approver`, `operator`.
- Сущности: общества, типы оборудования, статусы, оборудование, фото, клиенты, брони, осмотры, типы документов, документы, история статусов, аудит.
- Service layer для ключевой бизнес-логики (`inventory/services.py`).
- Ограничения статусов и правил печати.
- Soft delete оборудования.
- Веб-интерфейс на Django Templates + Bootstrap.
- REST API по основным endpoint из ТЗ.
- Fixtures для ролей, статусов, типов документов.
- Dockerfile, docker-compose, `.env.example`.
- Тесты pytest для MVP-сценариев.

## Быстрый запуск через Docker
```bash
cp .env.example .env
docker compose up --build
```

Приложение: http://localhost:8000

## Локальный запуск (без Docker)
1. Создайте venv и установите зависимости:
```bash
pip install -r requirements.txt
```
2. Для локального SQLite (удобно для разработки):
```bash
export USE_SQLITE=1
python manage.py migrate
python manage.py loaddata fixtures/initial_data.json
python manage.py createsuperuser
python manage.py runserver
```

## API (ключевые endpoint)
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET|POST /api/equipment`
- `GET|PATCH|DELETE /api/equipment/{id}`
- `POST /api/equipment/{id}/change-status`
- `GET|POST /api/clients`
- `GET|PATCH /api/clients/{id}`
- `GET /api/reservations`
- `POST /api/equipment/{id}/reserve`
- `POST /api/equipment/{id}/inspect`
- `GET /api/equipment/{id}/documents`
- `POST /api/equipment/{id}/documents/generate`
- `POST /api/documents/{id}/mark-signed`
- `POST /api/equipment/{id}/mark-receipt-printed`
- `GET /api/equipment/{id}/status-history`
- `GET /api/audit-log`

## Тесты
```bash
pytest
```

## Ограничения MVP
- PDF-шаблоны базовые; можно расширить поля и дизайн.
- В `AuditLogApi` оставлен минимальный ответ-заглушка, при необходимости легко расширяется.
- Нет внешних интеграций (касса/SMS/email), как и требовалось для MVP.
