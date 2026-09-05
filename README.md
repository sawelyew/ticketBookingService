# Ticket Booking Service API

Асинхронный REST API сервис для бронирования мест на мероприятия, обработки оплаты, фоновой генерации QR-кодов и отправки e-mail уведомлений.

## Технологический стек

* **Язык**: Python 3.13
* **Фреймворк**: FastAPI
* **База данных**: PostgreSQL + SQLAlchemy 2.0 + Alembic
* **Кэширование и блокировки**: Redis
* **Хранилище файлов**: MinIO / S3 (асинхронный клиент `aioboto3`)
* **Асинхронные задачи / Воркеры**: Taskiq + RabbitMQ
* **Контейнеризация**: Docker + Docker Compose

---

## Основной функционал

* **Аутентификация и авторизация**: 
  * JWT Access/Refresh токены, безопасное хеширование паролей (Bcrypt).
  * Подтверждение регистрации и email через **OTP-коды** с автоматической отправкой писем.
* **События и места (CRUD / Read-Only)**: 
  * Получение афиши, деталей мероприятий и схемы мест.
  * Кеширование запросов в Redis с учетом параметров поиска, фильтрации по датам и пагинации.
* **Бронирование билетов**: 
  * Защита от **Race Condition** при одновременной покупке одного и того же места с помощью распределенных блокировок (Seat Locking) в Redis.
  * Обработка оплаты и статусов бронирования.
* **Фоновые задачи и интеграции (Taskiq + RabbitMQ)**: 
  * Асинхронная генерация **QR-кодов** для купленных билетов и их сохранение в MinIO / S3.
  * Фоновая отправка билетов и OTP-кодов на email пользователя.
* **Профиль пользователя**: 
  * Просмотр личных данных.
  * Списки активных билетов и пагинированная история прошлых бронирований.
  * Получение безопасных временных Presigned URLs (с закешированным TTL) для скачивания QR-кодов билетов.

---

## Архитектура кеширования

В сервисе реализовано кеширование в Redis для оптимизации нагрузки на PostgreSQL и S3:

### 1. События и места (Public Cache)
* **Events List Cache**: `events:list:{params_hash}` — кеш списка событий с учетом фильтров и пагинации.
* **Event Details Cache**: `event:details:{event_id}` — детальная информация о конкретном мероприятии.

### 2. Пользовательские данные (User Cache)
* **User Profile Cache**: `user:{user_id}:profile` — профиль авторизованного пользователя.
* **Active Tickets Cache**: `user:{user_id}:tickets:active` — список активных купленных билетов.
* **Tickets History Cache**: `user:{user_id}:tickets:history:p{page}:s{page_size}` — пагинированная история заказов.

### 3. Файлы и ссылки (S3 / Presigned URLs)
* **S3 Presigned URLs Cache**: `user:{user_id}:ticket:{ticket_id}:download_url` — персональный кеш временных ссылок на скачивание билетов из MinIO (TTL = expiration time - 15m).

---

## Запуск проекта через Docker Compose

### 1. Клонирование и подготовка переменных
Клонируйте репозиторий и создайте файл `.env` в корневом каталоге (воспользуйтесь `.env.example` в качестве шаблона):

```bash
git clone [https://github.com/your-username/ticket-booking-service.git](https://github.com/your-username/ticket-booking-service.git)
cd ticket-booking-service
cp .env.example .env
```
### 2. Сборка и запуск контейнеров
Запустите приложение и всю инфраструктуру в фоновом режиме:
```bash
docker compose up -d --build
```
### 3. Применение миграций базы данных
Автоматически создайте таблицы в базе данных PostgreSQL через Alembic:
```bash
docker compose exec app alembic upgrade head
```

### Интерактивная документация и сервисы
После запуска сервисы доступны по следующим адресам:
- Swagger UI (OpenAPI): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- MinIO Console: http://localhost:9001 (логин/пароль из .env)
- RabbitMQ Management: http://localhost:15672 (guest / guest)

## Локальная разработка (без Docker)
Если требуется запустить FastAPI сервер локально для отладки:

## 1. Создайте и активируйте виртуальное окружение:
```bash
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
```
## 2. Установите зависимости:
```bash
pip install -r requirements.txt
```
## 3. Запустите uvicorn:
```bash
uvicorn app.main:app --reload
```









