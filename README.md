# AI Cyber Threat Investigation & Response Platform - Backend Foundation

This is the FastAPI-based backend foundation for the AI Cyber Threat Investigation & Response Platform. It provides a maintainable, clean architecture containing database session management, CRUD services, validation schemas, and endpoints for handling security events and alerts.

## Project Structure

```text
backend/
├── app/
│   ├── api/                  # API endpoints and routers
│   │   ├── endpoints/
│   │   │   ├── security_events.py
│   │   │   └── alerts.py
│   │   └── router.py
│   ├── core/                 # Global settings & configuration
│   │   └── config.py
│   ├── database/             # Database connection & setup
│   │   ├── base_class.py
│   │   ├── base.py           # Imports models to register metadata
│   │   └── session.py
│   ├── models/               # SQLAlchemy models
│   │   ├── security_event.py
│   │   └── alert.py
│   ├── schemas/              # Pydantic validation schemas
│   │   ├── security_event.py
│   │   └── alert.py
│   ├── services/             # CRUD business logic layer
│   │   ├── security_event.py
│   │   └── alert.py
│   └── main.py               # Main FastAPI entry point
├── tests/                    # Pytest endpoint unit test suite
├── requirements.txt          # Python dependencies
└── README.md                 # Project README
```

---

## Getting Started

### 1. Requirements
Ensure you have Python 3.11+ installed.

### 2. Setup Virtual Environment
Navigate to the `backend` directory and create a virtual environment:

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:

**Windows Command Prompt:**
```cmd
venv\Scripts\activate.bat
```

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies
Install all required modules from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Running the Development Server
Launch the development server with Uvicorn:

```bash
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`.

### 5. Interactive API Documentation
- **Swagger UI**: Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to test endpoints interactively.
- **ReDoc**: Visit [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) for structured document views.

---

## API Endpoints

### Security Events
- `POST /api/v1/events/` - Registers a new security event. Validates the structure and IP address.
- `GET /api/v1/events/` - Retrieves multiple events with optional filtering (`event_type`, `user_id`) and pagination.
- `GET /api/v1/events/{id}` - Retrieves detailed parameters of a specific event by ID.

### Alerts
- `POST /api/v1/alerts/` - Registers a new alert associated with a valid event ID. Enforces severity and status validation.
- `GET /api/v1/alerts/` - Retrieves multiple alerts with optional filtering (`status`, `severity`) and pagination.
- `GET /api/v1/alerts/{id}` - Retrieves details of a specific alert by ID, including its associated event metadata.

---

## Alembic Migration Guide

This project is fully prepared for Alembic migrations. To set up migrations:

1. **Initialize Alembic** in the `backend` directory:
   ```bash
   alembic init alembic
   ```

2. **Configure `alembic/env.py`**:
   Open `alembic/env.py` and modify it to import settings and base metadata:
   ```python
   from app.core.config import settings
   from app.database.base import Base

   # Set database URL dynamically
   config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)

   # Set metadata target
   target_metadata = Base.metadata
   ```

3. **Generate First Migration**:
   ```bash
   alembic revision --autogenerate -m "Initial migration"
   ```

4. **Apply Migration to Database**:
   ```bash
   alembic upgrade head
   ```

---

## Running the Security Event Simulator

This project includes a scenario-based simulator that generates multi-step attack or normal user event sequences and registers them on the backend via the POST endpoints.

To run the simulator (make sure your FastAPI server is running at `http://127.0.0.1:8000`):

1. **Run all scenarios continuously**:
   ```bash
   python -m app.simulators.event_generator --scenario all
   ```

2. **Run a specific scenario once** (e.g., `brute_force`):
   ```bash
   python -m app.simulators.event_generator --scenario brute_force --count 1
   ```

3. **Configure custom target URLs and intervals**:
   ```bash
   python -m app.simulators.event_generator --url http://127.0.0.1:8000/api/v1/events/ --interval 1.0 --scenario impossible_travel --count 2
   ```

### Available Scenarios:
- `normal_activity`: Legitimate login/logout sequence.
- `impossible_travel`: London and Tokyo logins 5 minutes apart (Expected detection: `impossible_travel`).
- `brute_force`: 5 failed logins followed by 1 successful login (Expected detection: `brute_force`).
- `new_device`: Successful login from an unrecognized device (Expected detection: `new_device`).
- `credential_compromise`: Takeover flow: failed logins -> successful login -> password reset -> new device login (Expected detection: `credential_compromise`).
- `password_reset_workflow`: Legitimate reset sequence (Legitimate, no threat flags).

---

## Running Unit Tests

The test suite runs on an isolated in-memory SQLite database (`sqlite:///:memory:`) using pytest. To execute the tests:

```bash
python -m pytest
```
