# Code_Inspector

A lightweight workflow engine for executing agent-based code review processes with loop support. Built with FastAPI, PostgreSQL, and Python.

## Features

**Workflow Graph Engine**
- Node-based workflow execution
- Loop nodes with conditional exit
- Complex condition evaluation (AND/OR/NOT)
- Async execution with status polling

**Code Review Mini-Agent**
- AST-based function extraction
- Cyclomatic complexity calculation
- Issue detection (4 types)
- Quality scoring system
- Iterative improvement loop

**Production-Ready**
- PostgreSQL database with async SQLAlchemy
- FastAPI REST API with Swagger docs
- Background task execution
- Comprehensive error handling
- Structured logging

---

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI REST API                    │
│                                                         │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                  Graph Engine                           │
│  -  Node Executor                                       │
│  -  State Manager                                       │
│  -  Condition Evaluator                                 │
│  -  Execution Logger                                    │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                  Tool Registry                          │
│  -  Code Review Tools (6 tools)                         │
│  -  Custom Tool Support                                 │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│              PostgreSQL Database                        │
│  -  Workflows                                           │
│  -  Workflow Runs                                       │
└─────────────────────────────────────────────────────────┘
```

### Workflow Structure

```
Extract Functions (once)
         ↓
    Loop Node (max 15 iterations)
         ├─→ Check Complexity
         ├─→ Detect Issues
         ├─→ Calculate Quality
         ├─→ Decision: quality_score >= 8?
         │      YES → Exit Loop ✓
         │      NO  → Continue
         ├─→ Suggest Improvements
         ├─→ Apply Suggestions
         └─→ Loop Back
```

---

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- pip/virtualenv

### Setup

1. **Clone repository**
```
git clone https://github.com/RitamPal26/Code_Inspector.git
cd Code_Inspector
```

2. **Create virtual environment**
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```
pip install -r requirements.txt
```

4. **Setup PostgreSQL**
```
# Create database
psql -U postgres -c "CREATE DATABASE workflow_engine;"
```

5. **Configure environment**
```
# Create .env file
cp .env.example .env

# Edit .env with your settings
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5433/workflow_engine
```

6. **Run application**
```
uvicorn app.main:app --reload
```

Server will start at: **http://localhost:8000**

---

## Usage

### API Documentation

Open **http://localhost:8000/docs** for interactive Swagger UI.

### Quick Start

**1. Create a workflow**

```
curl -X POST http://localhost:8000/api/v1/graph/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Code Review Workflow",
    "description": "Automated code review",
    "graph_definition": {
      "nodes": [...],
      "edges": [...],
      "initial_state_schema": {...}
    }
  }'
```

**Response:**
```
{
  "workflow_id": "abc-123...",
  "message": "Workflow created successfully"
}
```

**2. Execute workflow**

```
curl -X POST http://localhost:8000/api/v1/graph/run \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "abc-123...",
    "initial_state": {
      "code": "def hello(): pass"
    }
  }'
```

**Response:**
```
{
  "run_id": "def-456...",
  "status": "running",
  "message": "Workflow execution started"
}
```

**3. Check status**

```
curl http://localhost:8000/api/v1/graph/state/def-456...
```

**Response:**
```
{
  "run_id": "def-456...",
  "status": "completed",
  "quality_score": 8.5,
  "iterations": 3,
  "state": {...},
  "logs": [...]
}
```

---

## Code Review Workflow

### Tools

1. **extract_functions** - Parse Python code, extract function metadata
2. **check_complexity** - Calculate cyclomatic complexity
3. **detect_issues** - Identify code quality problems
4. **calculate_quality** - Compute quality score (0-10)
5. **suggest_improvements** - Generate actionable suggestions
6. **apply_suggestions** - Apply improvements (simulated)

### Example

```
# Good code - exits loop quickly
code = '''
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
'''

# Result: quality_score = 10/10, iterations = 1
```

```
# Bad code - iterates to improve
code = '''
def complex_function(a, b, c, d, e, f):
    if a > 0:
        if b > 0:
            if c > 0:
                # deep nesting...
                pass
'''

# Result: quality_score reaches 8/10 after 3-4 iterations
```

---

## Project Structure

```
code_inspector/
├── app/
│   ├── api/
│   │   └── routes.py          # REST API endpoints
│   ├── core/
│   │   ├── graph_engine.py    # Workflow orchestration
│   │   ├── node_executor.py   # Node execution
│   │   ├── state_manager.py   # State management
│   │   ├── condition_evaluator.py  # Condition logic
│   │   └── execution_logger.py     # Logging
│   ├── models/
│   │   ├── database.py        # SQLAlchemy models
│   │   └── schemas.py         # Pydantic models
│   ├── tools/
│   │   ├── tool_registry.py   # Tool management
│   │   └── code_review_tools.py    # Code review tools
│   ├── workflows/
│   │   └── code_review_workflow.py # Workflow definition
│   ├── db/
│   │   └── session.py         # Database session
│   ├── config.py              # Configuration
│   └── main.py                # FastAPI app
├── tests/
│   └── test_code_review_workflow.py
├── .env                       # Environment variables
├── requirements.txt
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root health check |
| GET | `/health` | Detailed health check |
| POST | `/api/v1/graph/create` | Create workflow |
| GET | `/api/v1/graph/list` | List all workflows |
| POST | `/api/v1/graph/run` | Execute workflow |
| GET | `/api/v1/graph/state/{run_id}` | Get execution status |
| GET | `/api/v1/graph/runs` | List workflow runs |

---

## Testing

**Run integration tests:**
```
# Start server
uvicorn app.main:app --reload

# In another terminal
python test_code_review_workflow.py
```

**Expected output:**
```
Test 1 (Good Code): PASSED
Test 2 (Bad Code): PASSED
```

---

## What This Engine Supports

### Implemented

- [x] Normal nodes (single tool execution)
- [x] Loop nodes (repeated execution)
- [x] Simple conditions (>=, <, ==, etc.)
- [x] Complex conditions (AND, OR, NOT)
- [x] Collection operations (length, max, min, contains)
- [x] Async tool execution
- [x] State persistence
- [x] Execution logging
- [x] Max iteration limits
- [x] Background execution
- [x] Status polling

### What I Would Improve With More Time

**1. Enhanced Features**
- WebSocket support for real-time updates
- Parallel node execution (fan-out/fan-in)
- Dynamic graph modification during execution
- Workflow versioning
- Retry mechanisms with exponential backoff

**2. Observability**
- Prometheus metrics
- Distributed tracing (OpenTelemetry)
- Advanced logging (ELK stack integration)
- Performance monitoring dashboard

**3. Scalability**
- Message queue integration (Celery/RabbitMQ)
- Distributed execution across workers
- Workflow execution caching
- Redis for state management

**4. Code Review Tools**
- Integration with real linters (pylint, flake8)
- AST-based code refactoring
- Support for multiple languages
- Git integration for PR reviews

**5. Testing**
- Unit tests (pytest)
- Integration tests
- Load testing
- CI/CD pipeline

**6. Security**
- API authentication (JWT)
- Role-based access control
- Workflow execution sandboxing
- Input validation hardening

---
