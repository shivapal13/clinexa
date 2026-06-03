# 🏥 Clinexa - Healthcare Management Backend

Clinexa is a healthcare management backend built with FastAPI that enables secure interactions between doctors and patients. The system provides appointment scheduling, medical record management, and prescription tracking through a role-based authentication system.

## 🚀 Features

### Authentication & Authorization

* JWT-based authentication
* Secure password hashing
* Role-based access control (Doctor & Patient)
* Protected API endpoints

### Doctor Management

* Create and manage doctor profiles
* View assigned appointments
* Create medical records
* Update medical records
* Create and manage prescriptions

### Patient Management

* Create and manage patient profiles
* Book appointments with doctors
* View medical records
* Access prescriptions

### Appointment Management

* Schedule appointments
* Track appointment status
* Manage doctor-patient interactions

### Medical Records

* Records linked to completed appointments
* Diagnosis and symptoms tracking
* Doctor notes
* Follow-up recommendations

### Prescription Management

* Prescription creation by doctors
* Medication details and dosage instructions
* Treatment duration tracking
* Patient prescription history

---

## 🛠 Tech Stack

| Category            | Technology              |
| ------------------- | ----------------------- |
| Backend Framework   | FastAPI                 |
| Database            | PostgreSQL              |
| ORM                 | SQLAlchemy              |
| Authentication      | JWT                     |
| Validation          | Pydantic                |
| Database Migrations | Alembic                 |
| Containerization    | Docker & Docker Compose |
| API Documentation   | Swagger UI              |

---

## 📂 Project Structure

```text
app/
├── auth/
├── models/
├── routes/
├── schemas/
├── config.py
├── database.py
└── main.py

alembic/

Dockerfile
docker-compose.yml
requirements.txt
```

---

## 📌 Core Modules

* Authentication
* Doctor Management
* Patient Management
* Appointment Management
* Medical Records
* Prescription Management

---

## ⚙️ Environment Variables

Create a `.env` file:

```env
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 🖥 Local Development Setup

Clone the repository:

```bash
git clone <repository-url>
cd clinexa-backend
```

Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
uvicorn app.main:app --reload
```

---

## 🗄 Database Migrations

Create a migration:

```bash
alembic revision --autogenerate -m "migration message"
```

Apply migrations:

```bash
alembic upgrade head
```

---

## 🐳 Docker Setup

Build and start containers:

```bash
docker compose up --build
```

Stop containers:

```bash
docker compose down
```

---

## 📖 API Documentation

Swagger UI:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

---

## 📚 What I Learned

This project helped me gain practical experience with:

* FastAPI application development
* REST API design
* JWT Authentication
* Role-Based Access Control
* PostgreSQL database design
* SQLAlchemy ORM
* Alembic database migrations
* Docker and Docker Compose
* Environment configuration
* Backend project structure and organization

---

## 🔮 Future Improvements

* Automated Testing with Pytest
* CI/CD Pipeline
* Email Notifications
* Redis Caching
* Appointment Reminder System

---

## 👨‍💻 Author

Shiva
