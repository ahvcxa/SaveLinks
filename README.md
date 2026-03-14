<div align="center">
  <img src="assets/logo.png" alt="SaveLinks Logo" width="200" height="auto" />
  
  # 🔗 SaveLinks

  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
</div>

<br/>

**SaveLinks** is a highly scalable, performant link-saving platform. It is built using modern technologies following [Hexagonal Architecture (Ports and Adapters)](https://en.wikipedia.org/wiki/Hexagonal_architecture_(software)) principles. It features an asynchronous API, automatic metadata extraction (titles, descriptions, etc.), and secure JWT-based authentication.

---

## ✨ Features

- **⚡ Asynchronous API:** High-RPS, non-blocking asynchronous endpoints powered by FastAPI.
- **🏛️ Hexagonal Architecture:** Clean structure isolating business logic from databases, frameworks, and external services.
- **🔐 JWT Authentication:** Secure session management and authorization infrastructure.
- **🗄️ PostgreSQL:** Powerful, relational database managed via `SQLAlchemy` and `asyncpg`.
- **🚀 Redis:** Fast in-memory data store for caching and background operations (like rate-limiting).
- **🤖 Automatic Metadata Extraction:** Automatically fetches titles, descriptions, and images of saved links using `beautifulsoup4` and `httpx`.
- **📦 Docker Support:** Easy, isolated setup for the database, Redis, and application via Docker Compose.

---

## 🛠️ Technology Stack

- **Language:** Python 3.11+
- **Web Framework:** FastAPI
- **Database (ORM):** SQLAlchemy 2.0 (Async) + asyncpg
- **Database Migration:** Alembic
- **Cache & Queue:** Redis
- **Authentication:** JWT (python-jose), bcrypt
- **Scraping / Data Fetching:** httpx, beautifulsoup4
- **Configuration:** Pydantic V2
- **Testing:** pytest, pytest-asyncio

---

## 🚀 Setup & Installation

Follow these steps to set up and run the project in your own environment.

### 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL
- Redis
- Docker & Docker Compose (Optional but recommended)

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/ahvcxa/SaveLinks.git
cd SaveLinks
```

### 2️⃣ Configure Environment Variables

Copy the example `.env` file and update it according to your system:

```bash
cp .env.example .env
```
*(Default values are generally set for local Docker or local development environments)*

### 3️⃣ Running with Docker (Recommended)

If your project includes a `docker-compose.yml`, you can start the entire system with a single command:

```bash
docker-compose up -d --build
```
To view the logs:
```bash
docker-compose logs -f
```

### 4️⃣ Local Development Setup

If you prefer to use databases installed on your local system instead of Docker, ensure the database configurations (URLs) in your `.env` file are set correctly.

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # For Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Initialize database tables (Migration):

```bash
alembic upgrade head
```

Run the application (using Uvicorn):

```bash
uvicorn src.main:app --reload
```

---

## 📚 API Documentation

Once the application is running, you can access the automatically generated interactive API documentation:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🗂️ Project Structure

Project files are organized according to **Hexagonal Architecture (Clean Architecture)** principles.

```text
src/
├── api/             # HTTP Routes, API Controllers (Adapters)
│   └── v1/
├── core/            # Core Business Logic and Domain Rules (Ports and Use Cases)
│   ├── link/
│   │   ├── domain/
│   │   └── ...
│   └── auth/
├── infrastructure/  # External Dependencies (Database Repositories, Redis, etc.)
│   └── database/
└── main.py          # Application Entry Point (FastAPI App)
```

---

## 🤝 Contributing

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/NewFeature`).
3. Commit your changes (`git commit -m 'feat: Add some NewFeature'`).
4. Push to the branch (`git push origin feature/NewFeature`).
5. Open a Pull Request.
