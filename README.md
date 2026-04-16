# HRMS-AI — Technical Design Document

> AI-powered Human Resource Management System built for the 3SC Hackathon.  
> Combines Django REST APIs, LangGraph-based AI agents, MCP tools, RAG, and async Celery pipelines into a unified conversational HR platform.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Architecture Overview](#3-architecture-overview)
4. [Project Structure](#4-project-structure)
5. [Data Models](#5-data-models)
6. [API Endpoints](#6-api-endpoints)
7. [AI Agent Architecture](#7-ai-agent-architecture)
8. [MCP Tools (Model Context Protocol)](#8-mcp-tools-model-context-protocol)
9. [RAG — Retrieval-Augmented Generation](#9-rag--retrieval-augmented-generation)
10. [Async Task Pipeline (Celery)](#10-async-task-pipeline-celery)
11. [LLM Provider Strategy](#11-llm-provider-strategy)
12. [Core Utilities & Patterns](#12-core-utilities--patterns)
13. [Authentication & RBAC](#13-authentication--rbac)
14. [Settings & Configuration](#14-settings--configuration)
15. [Running the Project](#15-running-the-project)
16. [Key Design Decisions](#16-key-design-decisions)

---

## 1. Project Overview

HRMS-AI is an AI-augmented HR system that allows employees, managers, HR personnel, and CFOs to interact with HR data through a natural language chat interface. Instead of navigating menus and forms, users simply type requests like:

- *"Apply casual leave from 21st to 23rd April"*
- *"Check burnout risk for my team"*
- *"Show pending approvals"*
- *"Apply sick leave for 2 days and casual leave next week"*

The system understands intent, fetches live data via MCP tools, validates against company policies via RAG, and executes HR actions — all through a single conversational API.

### Key Capabilities

| Capability | Description |
|---|---|
| Conversational Leave Management | Apply, approve, reject, cancel leave via chat |
| Multi-Leave Collection | Apply multiple leave types in one conversation |
| Policy Validation | Real-time validation against company HR policy documents |
| Burnout Detection | Attendance anomaly scoring + risk alerts |
| Org Query | Natural language org chart traversal ("who reports to Rahul?") |
| Role-Based Access | Employee / Manager / HR / CFO role separation enforced end-to-end |

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | Python 3.12 + Django 5 + Django REST Framework |
| AI/Agent | LangGraph-style pipeline + LangChain LLM abstractions |
| LLM Providers | OpenAI (GPT-4o), Anthropic (Claude), Google Gemini, Ollama (local) |
| Vector Search | PostgreSQL + pgvector (1536-dim embeddings) |
| Message Broker | RabbitMQ |
| Task Queue | Celery + Celery Beat |
| Cache / Memory | Redis |
| Auth | JWT (djangorestframework-simplejwt) |
| Frontend | React 18 + TypeScript + Tailwind CSS + Vite |
| Containerization | Docker + Docker Compose |
| Schema Docs | drf-spectacular (OpenAPI 3.0 / Swagger UI) |

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        React Frontend                        │
│              (Employee / Manager / HR / CFO UIs)            │
└──────────────────────────┬──────────────────────────────────┘
                           │ JWT + REST
┌──────────────────────────▼──────────────────────────────────┐
│                     Django REST API                          │
│   Views (thin) → Services → Repositories → ORM              │
│   /api/employees/  /api/leaves/  /api/ai/chat/  ...         │
└──────────┬───────────────────────────┬──────────────────────┘
           │                           │
           ▼                           ▼
┌──────────────────┐       ┌───────────────────────────────┐
│  Django Services │       │       AI Agent Pipeline        │
│  LeaveService    │       │  Router → Nodes → LLM Response │
│  AttendanceServ. │       │  (LangGraph-style graph)       │
│  NotificationSvc │       └───────────┬───────────────────┘
└──────────────────┘                   │
           │                           │
           ▼                           ▼
┌──────────────────┐       ┌───────────────────────────────┐
│  PostgreSQL DB   │       │         MCP Tools              │
│  + pgvector      │◄──────│  leave_tools / employee_tools  │
└──────────────────┘       │  attendance_tools / perf_tools │
                           └───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│              Celery Workers (RabbitMQ Broker)                 │
│  leave_tasks / burnout_tasks / chat_tasks / forecast_tasks   │
└──────────────────────────────────────────────────────────────┘
```

### Four Golden Rules

1. **Django owns all writes** — AI never touches the DB directly.
2. **Every AI action is async via RabbitMQ + Celery** — never block HTTP.
3. **MCP tools are the ONLY way AI reads live data.**
4. **Open for extension, closed for modification (OCP).**

---

## 4. Project Structure

```
hackathon/
├── backend/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py          # Shared settings (DB, JWT, Celery, CORS)
│   │   │   ├── local.py         # Native Django dev (debug toolbar, SQL logs)
│   │   │   ├── development.py   # Full Docker stack
│   │   │   └── production.py    # Hardened production settings
│   │   ├── celery.py            # Celery app + task discovery
│   │   └── urls.py              # Root URL routing
│   │
│   ├── core/
│   │   ├── llm/                 # LLM provider strategy pattern
│   │   │   ├── base.py          # BaseLLMProvider (abstract)
│   │   │   ├── factory.py       # LLMProviderFactory (selects by env var)
│   │   │   ├── openai_provider.py
│   │   │   ├── anthropic_provider.py
│   │   │   ├── gemini_provider.py
│   │   │   └── ollama_provider.py
│   │   ├── cache/
│   │   │   ├── base.py          # BaseCacheBackend (abstract)
│   │   │   ├── redis_backend.py # Redis implementation
│   │   │   └── keys.py          # ALL Redis key constants live here
│   │   ├── repositories/
│   │   │   └── base.py          # BaseReadRepository / BaseWriteRepository
│   │   ├── notifications/
│   │   │   ├── base.py
│   │   │   ├── dispatcher.py    # Routes notifications to handlers
│   │   │   └── handlers/        # EmailHandler, SlackHandler, InAppHandler
│   │   ├── tasks/
│   │   │   └── base.py          # BaseHRMSTask (logging + retry)
│   │   ├── permissions.py       # IsEmployee / IsManager / IsHR / IsCFO
│   │   └── decorators.py        # @rate_limit etc.
│   │
│   ├── apps/
│   │   ├── employees/           # User, Employee, Department models + auth
│   │   ├── leaves/              # Leave requests, policies, balances, comp-off
│   │   ├── attendance/          # Check-in logs, anomaly detection
│   │   ├── payroll/             # Payroll slips
│   │   ├── performance/         # Goals, review cycles, AI drafts
│   │   ├── notifications/       # In-app notification inbox
│   │   ├── ai/                  # Chat sessions, messages, summaries + embeddings
│   │   └── rag/                 # RAG documents, policy chunks + embeddings
│   │
│   ├── agents/
│   │   ├── state.py             # AgentState (TypedDict)
│   │   ├── graph.py             # Pipeline definitions per intent
│   │   ├── router.py            # Intent classification (keyword → embed → LLM)
│   │   ├── intent_registry.py   # Intent definitions + examples
│   │   └── nodes/
│   │       ├── leave_collector.py   # Multi-turn stateful leave collection
│   │       ├── mcp_tools.py         # Executes MCP tools for current intent
│   │       ├── rag_retrieval.py     # pgvector similarity search
│   │       ├── policy_checker.py    # Validates leaves against HR policies
│   │       ├── spof.py              # Single Point of Failure detection
│   │       ├── conflict.py          # Leave overlap detection
│   │       ├── burnout.py           # Burnout score computation
│   │       ├── nl_query.py          # Deterministic org query planner
│   │       └── llm_generate.py      # Final LLM response generation
│   │
│   ├── mcp/
│   │   ├── registry.py          # Tool registration + dispatch
│   │   ├── rbac.py              # ensure_role() helper
│   │   └── tools/
│   │       ├── leave_tools.py
│   │       ├── employee_tools.py
│   │       ├── attendance_tools.py
│   │       └── performance_tools.py
│   │
│   ├── tasks/
│   │   ├── leave_tasks.py       # Monthly accrual etc.
│   │   ├── burnout_tasks.py     # Daily burnout scan
│   │   ├── chat_tasks.py        # Entity extraction, session summarization
│   │   ├── forecast_tasks.py    # Daily leave forecast
│   │   ├── notification_tasks.py
│   │   └── rag_policy_tasks.py  # Policy ingestion
│   │
│   └── rag/
│       ├── ingest.py            # Document ingestion pipeline
│       ├── retrieval.py         # General RAG retrieval
│       ├── policy_retrieval.py  # Policy-targeted retrieval
│       └── chunkers.py          # Document chunking strategies
│
├── frontend/                    # React 18 + TS + Tailwind
├── docker-compose.yml           # Full stack
├── docker-compose.local.yml     # Infra only (postgres + redis + rabbitmq)
└── .env.example
```

---

## 5. Data Models

### employees app

**User** (extends AbstractUser)
- `email` (unique) — primary identifier, no username
- `name` — full name
- `phone_number` (unique)

**Employee**
- `user` (OneToOne → User)
- `employee_id` (unique string, e.g. "EMP001")
- `role` — employee | manager | hr | cfo | admin
- `department` (FK → Department)
- `manager` (FK → self, nullable)
- `title`, `is_active`, `joined_on`

**Department**
- `name` (unique), `code` (unique slug)

---

### leaves app

**LeavePolicy**
- `leave_type` — CL | PL | SL | CO | LOP
- `annual_allocation`, `accrual_per_month`
- `requires_balance`, `allow_backdate_days`

**LeaveBalance** (OneToOne with Employee)
- `casual_remaining`, `privilege_remaining`, `sick_remaining`, `comp_off_remaining`
- Methods: `get_remaining(type)`, `deduct(type, days)`, `credit(type, days)`

**LeaveRequest**
- `employee`, `applied_by`, `approver`
- `leave_type`, `from_date`, `to_date`, `days_count`
- `status` — PENDING | APPROVED | REJECTED | CANCELLED
- `is_half_day`, `half_day_session` — AM | PM
- `spof_flag`, `conflict_flag` — AI risk signals
- `balance_deducted` — idempotency guard
- `ai_context_card` (JSON) — AI-generated context summary

**CompOffRequest**
- `employee`, `worked_on`, `days_claimed`, `reason`
- `status` — PENDING | APPROVED | REJECTED
- `approved_by`

---

### attendance app

**AttendanceLog**
- `employee`, `date` (unique together)
- `check_in`, `check_out`, `status` — PRESENT | ABSENT | WFH

**AttendanceAnomaly**
- `employee`, `date`, `anomaly_type` — LATE | MISSING | OTHER
- `description`, `resolved`

---

### ai app

**ChatSession**
- `id` (UUID PK), `user`, `employee`, `title`, `is_active`

**ChatMessage**
- `session`, `role` — user | assistant | system
- `content`, `intent`
- `tool_snapshot` (JSON) — tool results at time of message
- `retrieved_docs` (JSON list)
- `embedding` (pgvector, 1536-dim) — for semantic search across history

**ChatSummary**
- `session`, `start_message_id`, `end_message_id`
- `summary` text, `embedding` (pgvector)
- Used to compress long conversation windows

---

### rag app

**RAGDocument** — General document chunks with embeddings

**PolicyDocument** — HR policy metadata (name slug, title)

**PolicyVersion** — Versioned snapshots of a policy document

**PolicyChunk** — Individual policy chunks with embeddings + metadata

---

## 6. API Endpoints

### Auth
```
POST   /api/auth/token/             JWT login (rate limited: 10/min)
POST   /api/auth/token/refresh/     Refresh access token
```

### Employees
```
GET    /api/employees/              List all employees
POST   /api/employees/              Create employee
GET    /api/employees/me/           Authenticated user's profile
GET    /api/employees/{id}/         Employee by ID
```

### Leaves
```
GET    /api/leaves/                 My leave history
POST   /api/leaves/                 Apply leave
GET    /api/leaves/balance/         My leave balances
GET    /api/leaves/{id}/            Leave details
POST   /api/leaves/{id}/approve/    Approve leave (manager+)
POST   /api/leaves/{id}/reject/     Reject leave (manager+)
POST   /api/leaves/{id}/cancel/     Cancel leave
GET    /api/leaves/pending/         Pending approvals (manager+)
GET    /api/leaves/team/            Team leave calendar (manager+)
POST   /api/leaves/comp-off/        Request comp-off
GET    /api/leaves/comp-off/pending/ Pending comp-off (manager+)
```

### Attendance
```
POST   /api/attendance/check-in/    Record check-in
```

### Payroll
```
GET    /api/payroll/me/             My payroll slips
```

### Performance
```
GET    /api/performance/me/         My goals + review cycles
```

### Notifications
```
GET    /api/notifications/          Inbox
GET    /api/notifications/unread-count/
POST   /api/notifications/read-all/
POST   /api/notifications/{id}/read/
```

### AI Chat
```
POST   /api/ai/chat/                Single unified conversational endpoint
```

Request body:
```json
{
  "message": "Apply sick leave from 21st to 23rd April",
  "session_id": "uuid (optional, for multi-turn)",
  "collection_stage": "collecting_details (echoed from previous turn)",
  "leave_items": [],
  "policy_violations": []
}
```

Response:
```json
{
  "reply": "...",
  "session_id": "uuid",
  "collection_stage": "awaiting_confirmation",
  "leave_items": [...],
  "policy_violations": [...]
}
```

### Docs
```
GET    /api/docs/                   Swagger UI
GET    /api/schema/                 OpenAPI 3.0 schema
```

---

## 7. AI Agent Architecture

### Agent State

Every agent invocation carries a typed state dict (`AgentState`) through the pipeline:

```python
class AgentState(TypedDict):
    intent: str
    employee_id: int
    requester_id: int
    requester_role: str
    user_profile: dict           # name, role, title, dept, manager_name
    input_data: dict
    chat_session_id: str
    chat_history: list           # last 12 turns (Redis + DB)
    retrieved_docs: list[str]    # RAG chunks
    tool_results: dict           # MCP tool outputs
    llm_response: Optional[str]
    spof_flag: bool
    conflict_detected: bool
    conflict_summary: Optional[str]
    burnout_score: Optional[float]
    burnout_signals: Optional[dict]
    # Multi-leave collection state
    leave_items: list
    collection_stage: Optional[str]
    collecting_index: int
    policy_violations: list
    error: Optional[str]
```

### Intent Classification (Router)

Three-tier classification — fastest first:

```
1. Keyword matching       (< 1ms)   — regex patterns on message text
2. Embedding similarity   (< 50ms)  — cosine distance against intent examples
3. LLM classification     (< 2s)    — fallback for ambiguous queries
```

Supported intents: `leave_application`, `leave_collection`, `approve_leave`, `reject_leave`, `cancel_leave`, `comp_off_request`, `comp_off_approve`, `burnout_check`, `review_summary`, `policy_query`, `employee_query`, `leave_status`, `pending_approvals`, `renotify_manager`

### Agent Pipelines (per intent)

```
leave_collection   → leave_collector → mcp_tools → rag_retrieval → policy_checker → spof → conflict → llm_generate
leave_application  → mcp_tools → spof → conflict → rag_retrieval → llm_generate
burnout_check      → mcp_tools → rag_retrieval → llm_generate
review_summary     → mcp_tools → rag_retrieval → llm_generate
policy_query       → rag_retrieval → llm_generate
employee_query     → nl_query → mcp_tools → llm_generate
approve_leave      → mcp_tools → llm_generate
(other actions)    → mcp_tools → llm_generate
```

### Node Descriptions

**leave_collector** — Stateful multi-turn leave collection. Parses initial request into structured leave items (type, from, to, reason). Asks clarifying questions turn-by-turn. Advances through stages: `collecting_details → checking_policy → awaiting_confirmation → applying → done`. Client echoes state each turn for statefulness without server-side session storage.

**mcp_tools** — Executes MCP tools mapped to the current intent. Uses deterministic planners for common self-referential queries ("my team", "who am I") to avoid LLM overhead. Falls back to LLM-driven tool planning for complex queries. Stamps `_tools_called_this_turn` for accurate context injection.

**rag_retrieval** — Embeds user query + intent context, runs cosine similarity search against `RAGDocument` and `PolicyChunk` tables via pgvector. Falls back to keyword search if vector store unavailable.

**policy_checker** — Validates each leave item in `leave_items` against retrieved policy docs. Two-pass: LLM soft evaluation first, then hard rule checks (max consecutive days, annual limits, balance availability). Violations tagged as `error` (block) or `warning` (overridable by user confirmation).

**spof** — Detects Single Point of Failure risk: employee is the sole person with their job title in their department. Flags `spof_flag` on the leave request.

**conflict** — Checks for overlapping approved leaves from the same employee. Flags `conflict_detected` with summary.

**burnout** — Computes a 0–1 burnout score from attendance anomalies, absences, and unresolved issues over the past 30 days. Returns score + signal breakdown.

**nl_query** — Deterministic planner for common org queries. Avoids LLM entirely for patterns like "who is my manager", "list my team", "org tree for X".

**llm_generate** — Generates the final user-facing response. Builds a personalised system prompt (*"You are talking to Kartik (Senior Engineering Manager)..."*). Injects conversation history, tool results, RAG chunks, and intent context. Addresses the user by first name, adjusts tone by role. Temperature: 0.3.

### Conversation Memory (Hybrid)

```
Redis (fast, recent)
  chat:turns:{session_id}    → last N turns (name, message pairs)
  chat:tools:{session_id}    → pinned tool results

DB (durable, semantic)
  ChatMessage.embedding      → pgvector, searched by cosine similarity
  ChatSummary                → compressed older context windows

Resolution order for pronouns:
  1. entity log (chat:entities:{session_id}) — extracted async after each turn
  2. tool_results heuristics — fallback
```

---

## 8. MCP Tools (Model Context Protocol)

Tools are the ONLY way the AI reads live data from the database.

Every tool:
- Is registered in `mcp/registry.py`
- Checks RBAC at entry via `ensure_role()`
- Returns `{"error": "...", "code": "SNAKE_CASE"}` on failure — never raises
- Is idempotent where it performs writes

### leave_tools.py
| Tool | Description |
|---|---|
| `get_leave_balance` | Current CL/PL/SL/CO/LOP balance |
| `get_leave_history` | Last 30 leave requests |
| `get_leave_details` | Single leave by ID |
| `get_pending_approvals` | Manager's pending leaves + comp-off |
| `create_leave_request` | Apply leave (employee) |
| `approve_leave_request` | Approve (manager+) |
| `reject_leave_request` | Reject (manager+) |
| `cancel_leave_request` | Cancel (employee or manager) |
| `request_comp_off` | Request comp-off credit |
| `approve_comp_off` | Approve comp-off (manager+) |
| `reject_comp_off` | Reject comp-off (manager+) |
| `renotify_manager` | Send reminder to manager |

### employee_tools.py
| Tool | Description |
|---|---|
| `get_employee_profile` | Full profile by ID |
| `get_my_profile` | Requester's own profile |
| `get_employee_manager_chain` | Hierarchy up 5 levels |
| `get_direct_reports` | Team members reporting to employee |
| `get_peers` | Same manager or department |
| `get_org_tree` | Recursive subtree (max depth 3) |
| `get_department_employees` | All in a department |
| `list_departments` | Departments with headcount |
| `search_employees` | Filter by role/title/dept/joined_after |
| `get_largest_teams` | Managers ranked by team size |
| `get_new_hires` | Joined within N days |
| `find_employee_by_name` | Fuzzy name search |

### attendance_tools.py
| Tool | Description |
|---|---|
| `get_attendance_summary` | Stats over a date range |
| `get_attendance_anomalies` | Flagged anomalies |

### performance_tools.py
| Tool | Description |
|---|---|
| `get_employee_goals` | Employee goals |
| `get_review_cycles` | Review periods + AI drafts |

---

## 9. RAG — Retrieval-Augmented Generation

Used to ground the AI's leave advice and policy validation in actual company policy documents.

### Flow
```
User query + intent
     ↓
EmbeddingProviderFactory.embed(query)
     ↓
pgvector cosine similarity search
  → RAGDocument  (general docs)
  → PolicyChunk  (HR policy chunks)
     ↓
Top-k chunks injected into LLM context
```

### Ingestion Pipeline
```bash
python manage.py create_pgvector_extension   # one-time setup
python manage.py ingest_rag_docs             # ingest PDF/TXT policy docs
```

Documents in `rag/documents/*.txt` are chunked, embedded, and stored in `RAGDocument` / `PolicyChunk` tables.

### Fallback
If pgvector is unavailable or embedding fails: falls back to keyword tokenization (split on non-alphanumeric, min length 3 chars).

---

## 10. Async Task Pipeline (Celery)

### Broker & Queues
- **Broker:** RabbitMQ
- **Result Backend:** Redis
- **Queues:** `leave`, `notifications`, `analytics`, `ai_heavy`

### Scheduled Tasks (Celery Beat)
| Task | Schedule | Description |
|---|---|---|
| `burnout_scan_all` | Daily 2am UTC | Scan all employees for burnout signals |
| `generate_leave_forecast` | Daily 3am UTC | Leave forecast for current month |
| `accrue_monthly_leaves` | 1st of month 00:01 UTC | Accrue PL/SL per employee |

### On-Demand Tasks
| Task | Trigger | Description |
|---|---|---|
| `dispatch_notification` | Service events | Email + Slack + InApp dispatch |
| `extract_turn_entities` | After each chat turn | Extract focus_employee_id + entities for pronoun resolution |
| `summarize_chat_session` | > N messages in session | Compress old context into ChatSummary |

### Base Task Class
All tasks inherit `BaseHRMSTask`:
```python
class BaseHRMSTask(Task):
    max_retries = 3
    default_retry_delay = 60  # seconds

    def run(self, *args, **kwargs):
        try:
            return self.execute(*args, **kwargs)
        except Exception as exc:
            logger.exception("[TASK FAILED] %s", exc)
            raise self.retry(exc=exc)
```

Every `.delay()` call in services is wrapped in `try/except` — broker errors never cause HTTP 500s.

---

## 11. LLM Provider Strategy

Providers are swappable with zero agent code changes — just change `LLM_PROVIDER` env var.

```python
class LLMProviderFactory:
    _REGISTRY = {
        "openai":    OpenAIProvider,
        "anthropic": AnthropicProvider,
        "gemini":    GeminiProvider,
        "ollama":    OllamaProvider,
    }

    @staticmethod
    def get_provider(name=None) -> BaseLLMProvider:
        name = name or config("LLM_PROVIDER", default="openai")
        return _REGISTRY[name](...)

    @staticmethod
    def register(name, cls):
        _REGISTRY[name] = cls   # extension without modification
```

**Default models:**
- OpenAI: `gpt-4o`
- Anthropic: `claude-sonnet-4-6`
- Gemini: `gemini-pro`
- Ollama: `gpt-oss:120b-cloud` (local inference)

**Rule:** Agent nodes always call `LLMProviderFactory.get_provider()` — never instantiate `ChatOpenAI()` directly.

---

## 12. Core Utilities & Patterns

### Service Layer
```
View → Service → Repository → ORM
```
Views are thin (auth + deserialize + call service). Business logic lives in `XxxService`. DB queries live in `XxxReadRepository` / `XxxWriteRepository`.

### Repository Pattern
```python
class BaseReadRepository(Generic[T]):
    model: Type[T]
    def get(self, pk) -> T: ...
    def filter(self, **kwargs) -> QuerySet: ...

class BaseWriteRepository(Generic[T]):
    model: Type[T]
    def create(self, **kwargs) -> T: ...
    def update(self, instance, **kwargs) -> T: ...
```

Agents receive read-only repositories. Services receive write repositories. Explicit dependencies, testable in isolation.

### Cache Keys
All Redis keys defined in `core/cache/keys.py`:
```python
class CacheKeys:
    CHAT_TURNS    = "chat:turns:{session_id}"
    CHAT_TOOLS    = "chat:tools:{session_id}"
    CHAT_ENTITIES = "chat:entities:{session_id}"
    RATE_LIMIT    = "rate:{user_id}:{endpoint}"
    # ...
```
No inline string keys anywhere in the codebase.

### Notification Dispatcher
```python
class NotificationDispatcher:
    _handlers: list[BaseNotificationHandler] = [
        EmailHandler(),
        SlackHandler(),
        InAppHandler(),
    ]

    def dispatch(self, notification: Notification):
        for handler in self._handlers:
            handler.send(notification)
```

Add new channels by registering a new handler — no modification to dispatcher.

### Error Response Format
All API errors return:
```json
{
  "error": "Human-readable message",
  "code": "SNAKE_CASE_ERROR_CODE",
  "details": {}
}
```

---

## 13. Authentication & RBAC

### JWT Auth
- Access token: 60 min (configurable via `JWT_ACCESS_TOKEN_LIFETIME_MINUTES`)
- Refresh token: 7 days
- Header: `Authorization: Bearer <token>`

### Role Hierarchy
```
admin > hr > cfo > manager > employee
```

### DRF Permission Classes
```python
class IsEmployee(BasePermission):
    # User has active employee profile
class IsManager(BasePermission):
    # role in (manager, hr, cfo, admin)
class IsHR(BasePermission):
    # role in (hr, admin)
class IsCFO(BasePermission):
    # role in (cfo, hr, admin)
```

### MCP Tool RBAC
```python
def ensure_role(requester_role: str, allowed_roles: list[str]) -> dict | None:
    if requester_role not in allowed_roles:
        return {"error": "Permission denied", "code": "FORBIDDEN"}
    return None
```

Every MCP tool calls `ensure_role()` at entry. Data is also filtered by role within the tool (e.g. managers only see their own team's data).

### Rate Limiting
- Anonymous: 20 requests/min
- Authenticated: 200 requests/min
- Auth endpoints: 10 requests/min

---

## 14. Settings & Configuration

### Environment Variables

```bash
# Django
DJANGO_SETTINGS_MODULE=config.settings.local
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://hrms:hrms_secret@127.0.0.1:5432/hrms

# Cache / Broker
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1
RABBITMQ_URL=amqp://hrms:hrms_secret@127.0.0.1:5672//

# LLM
LLM_PROVIDER=openai          # openai | anthropic | gemini | ollama
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gpt-oss:120b-cloud
EMBEDDING_PROVIDER=openai

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Security
INTERNAL_API_TOKEN=change-this-in-production
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

### Settings Files
| File | Use |
|---|---|
| `base.py` | Shared config — DB, JWT, Celery, DRF |
| `local.py` | Native Django dev — debug toolbar, SQL logging, CORS open |
| `development.py` | Full Docker stack |
| `production.py` | Hardened — SSL, secure cookies, enforced secret key |

---

## 15. Running the Project

### Prerequisites
- Docker + Docker Compose
- Python 3.12 + virtualenv (for native dev)
- Node 18+ (for frontend)

### Option A: Full Docker Stack
```bash
cp .env.example .env          # fill in API keys
mkdir -p data/{postgres,redis,rabbitmq,media}
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py create_pgvector_extension
docker-compose exec web python manage.py ingest_rag_docs
docker-compose exec web python manage.py seed_demo_data
```

### Option B: Native Django + Docker Infra
```bash
# Start only infra
docker-compose -f docker-compose.local.yml up -d

# Activate venv
source ~/.venvs/hackathon-backend/bin/activate
cd backend
pip install -r requirements/development.txt

# Run Django
python manage.py migrate
python manage.py create_pgvector_extension
python manage.py runserver 0.0.0.0:8002

# Run Celery (separate terminal)
celery -A config.celery worker -l info
celery -A config.celery beat -l info
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:5173
```

### VS Code Debugger
Open the `hackathon/` root folder in VS Code and press **F5** — selects "Django: runserver (env.all.local)" config automatically.

---

## 16. Key Design Decisions

### Why LangGraph-style pipeline instead of a monolithic LLM call?
Each concern (policy check, SPOF detection, conflict detection, RAG retrieval) is isolated in its own node. Nodes can be added, removed, or reordered per intent without touching other nodes. The pipeline is deterministic and debuggable — every node's output is visible in `AgentState`.

### Why MCP tools instead of direct DB access from the agent?
MCP tools are the contract between the AI layer and the data layer. They enforce RBAC, provide consistent error handling, and ensure all reads go through validated, tested code paths. The agent cannot accidentally bypass business rules.

### Why RabbitMQ instead of Redis as Celery broker?
RabbitMQ provides message durability, dead-letter queues, and true pub-sub semantics. Redis as a broker loses messages on restart. For an HR system where leave application tasks must not be silently dropped, RabbitMQ is the right choice.

### Why pgvector instead of a separate vector DB?
Keeps the operational footprint small (one fewer service). PostgreSQL + pgvector gives transactional consistency between relational data and vector embeddings. Suitable for the scale of an internal HR system.

### Why client-side state echoing for multi-turn leave collection?
The leave collection flow requires tracking which leave items have been collected across multiple chat turns. Rather than storing this in a server-side session (Redis key per session), the client echoes `collection_stage` + `leave_items` back with each turn. This makes the server stateless for the collection flow, simplifies horizontal scaling, and makes the state fully visible to the frontend for UI rendering.

### Why hybrid Redis + DB conversation memory?
Redis gives sub-millisecond access to recent turns (last 12) for in-flight conversations. The DB (`ChatMessage` with pgvector embeddings) enables semantic search across full conversation history for long-running sessions. `ChatSummary` compresses old context so the LLM context window doesn't overflow on long sessions.

---

*Built for the 3SC Hackathon — Team Dhurandar.*
