# 🏥 Clinexa Backend

<p align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge)
![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens)

</p>

A scalable healthcare appointment management backend built using **FastAPI**, **PostgreSQL**, **Redis**, and **Celery**. Clinexa provides secure authentication, appointment scheduling, doctor availability management, background task processing, Redis caching, and automated email notifications following production-ready backend practices.

---

# ✨ Features

### 🔐 Authentication & Security

- JWT Authentication
- Role-Based Authorization
- Password Hashing (BCrypt)
- Protected APIs
- Rate Limiting using SlowAPI

### 👨‍⚕️ Doctor Module

- Doctor Profile Management
- Doctor Discovery
- Search & Filter Doctors
- Recurring Weekly Availability
- Custom Availability Overrides
- Dynamic Slot Generation

### 👤 Patient Module

- Patient Profile Management
- Appointment Booking
- Appointment Update
- Appointment Cancellation
- Appointment History

### 📅 Appointment System

- Dynamic Slot Validation
- Double Booking Prevention
- Past Date & Time Validation
- Appointment Status Management
- Confirmation Emails
- Reminder Emails

### ⚡ Performance

- Redis Caching
- Automatic Cache Invalidation
- Optimized Database Queries
- Pagination
- Background Jobs using Celery

---

# 🏗 System Architecture

```text
                    Client
                       │
                       ▼
                  FastAPI API
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
 PostgreSQL      Redis Cache     Celery Queue
        │                             │
        │                             ▼
        │                      Celery Worker
        │                             │
        ▼                             ▼
    Database                    Email Service

                 Celery Beat
                      │
                      ▼
         Appointment Reminder Scheduler
```

---

# 🛠 Tech Stack

| Category | Technology |
|-----------|------------|
| Backend | FastAPI |
| Language | Python |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Authentication | JWT |
| Cache | Redis |
| Background Jobs | Celery |
| Scheduler | Celery Beat |
| Email | FastAPI-Mail |
| Rate Limiting | SlowAPI |
| Migrations | Alembic |
| Containerization | Docker |

---

# ⚡ Database & Performance Optimizations

- Redis caching for recurring availability
- Redis caching for custom availability
- Cached slot generation
- Automatic cache invalidation
- Indexed frequently queried columns
- Optimized SQLAlchemy queries
- Reduced database round trips
- Pagination support
- Background task processing
- Asynchronous email delivery

---

# 📧 Background Processing

Celery and Celery Beat are used for asynchronous task processing.

Implemented Tasks

- Appointment Confirmation Email
- Appointment Reminder Email
- Scheduled Reminder Service

---

# 🚀 Getting Started

## Clone Repository

```bash
git clone https://github.com/shivapal13/clinexa-backend.git

cd clinexa-backend
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

```env
DATABASE_URL=

SECRET_KEY=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

REDIS_URL=

POSTGRES_PASSWORD=

MAIL_USERNAME=

MAIL_PASSWORD=

MAIL_FROM=

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_STARTTLS=true
MAIL_SSL_TLS=false

# Comma-separated email addresses allowed to review doctor profiles.
# These addresses must also have a registered Clinexa account.
ADMIN_EMAILS=reviewer@example.com
```

Keep `.env` out of source control. Use a unique database password and rotate any
credential that was previously committed or shared. `POSTGRES_PASSWORD` is
required by Docker Compose and must match the password in `DATABASE_URL`.

---

## Run Migrations

```bash
alembic upgrade head
```

---

## Start Application

```bash
docker compose up --build
```

## Doctor profile review

Doctor profiles are private from patient search and booking until reviewed.
Set `ADMIN_EMAILS` to a comma-separated allowlist of reviewer email addresses.
Each reviewer signs in with a normal Clinexa account; public registration does
not grant reviewer access. With that account's bearer token, use
`GET /doctor/profile/admin/pending` to view submissions, then
`PATCH /doctor/profile/admin/{doctor_id}/verification` with
`{"verification_status":"VERIFIED"}` or `{"verification_status":"REJECTED"}`.
Reviewers should independently verify the submitted professional license
number against the relevant licensing authority before approving.

Admins can also create a profile for an existing Doctor account that does not
have one. In the frontend, use **Doctor setup**; the admin API lists eligible
accounts at `GET /doctor/profile/admin/accounts` and creates a profile at
`POST /doctor/profile/admin/accounts/{user_id}/profile`. Profiles created this
way remain pending and are not visible for discovery or booking until approved.

Swagger

```
http://localhost:8000/docs
```

---

# 📂 Project Structure

```text
app/
├── core/
├── models/
├── routes/
├── schemas/
├── services/
├── tasks/
├── main.py

alembic/
Dockerfile
docker-compose.yml
```

---

# 📈 Future Enhancements

- Forgot Password (OTP)
- Refresh Tokens
- Video Consultation
- Payment Gateway
- Push Notifications
- Admin Dashboard

---

# 👨‍💻 Author

**Shiva Pal**

- GitHub: https://github.com/shivapal13
- LinkedIn: https://linkedin.com/in/shivapal13

---

⭐ If you found this project useful, consider giving it a star.