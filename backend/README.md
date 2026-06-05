# AI Cyber Threat Investigation & Response Platform

This is the FastAPI backend for the AI Cyber Threat Investigation & Response Platform.

## Features
- **Phase 1: Backend Foundation**
  - FastAPI, SQLAlchemy, SQLite
  - SecurityEvent and Alert CRUD endpoints
- **Phase 2: Simulator**
  - Scenario-based event simulation (Normal, Impossible Travel, Brute Force, New Device, etc.)
  - CLI runner (`app/simulators/event_generator.py`)
- **Phase 3: Detection Engine**
  - Rules: Impossible Travel, Brute Force, New Device Login
  - Endpoint to trigger detection runs manually

## Running the Server
```bash
python -m uvicorn app.main:app --reload
```

## Running the Simulator
```bash
python -m app.simulators.event_generator --interval 2.0 --count 10
```

## Running Tests
```bash
python -m pytest tests/ -v
```
