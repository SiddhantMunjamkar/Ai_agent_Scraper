# High-Level Design (HLD) - Multi-Agent AI Scraper System

## 1. Executive Summary

The Multi-Agent AI Scraper System is a sophisticated orchestration framework that leverages multiple specialized Large Language Model (LLM) agents to decompose, execute, and validate complex engineering tasks. The system employs a pipeline-based architecture with three distinct roles: planning, execution, and quality assurance, all powered by the Ollama-hosted Qwen2.5:7B LLM model.

---

## 2. System Overview

### 2.1 Purpose
- Break down complex engineering tasks into manageable subtasks
- Execute subtasks using LLM-powered agents
- Validate execution quality and ensure correctness
- Handle failures gracefully with automatic retry mechanisms

### 2.2 Key Characteristics
- **Multi-Agent Architecture**: Three specialized agents working in sequence
- **LLM-Driven**: All reasoning and task execution powered by Qwen2.5:7B
- **Quality Assurance**: Built-in review loop for each subtask
- **Retry Mechanism**: Automatic retries for failed executions
- **Asynchronous Operation**: Async/await throughout the pipeline
- **RESTful API**: FastAPI-based HTTP interface

---

## 3. Architecture & Components

### 3.1 System Layers

```
┌─────────────────────────────────────────────┐
│           Client Layer (FastAPI)            │
│    POST /execute {task} → Response          │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│       Orchestration Layer                   │
│    (Orchestrator - Central Coordinator)     │
└────────────────┬────────────────────────────┘
                 │
        ┌────────┼────────┐
        │        │        │
┌───────▼──┐ ┌──▼──────┐ ┌─▼──────────┐
│ Planner  │ │Executor │ │  Reviewer  │
│  Agent   │ │ Agent   │ │   Agent    │
└───────┬──┘ └──┬──────┘ └─┬──────────┘
        │       │          │
        └───────┴──────┬───┘
                       │
           ┌───────────▼──────────┐
           │   Ollama Client      │
           │  (LLM Interface)     │
           │ qwen2.5:7b Model     │
           └──────────────────────┘
                       │
           ┌───────────▼──────────┐
           │  Ollama Server       │
           │  (localhost:11434)   │
           └──────────────────────┘
                       │
           ┌───────────▼──────────┐
           │ LLM Model Instance   │
           │  (qwen2.5:7b)        │
           └──────────────────────┘
```

### 3.2 Core Components

#### **3.2.1 FastAPI Server** (`main.py`)
- **Role**: HTTP REST API server
- **Responsibility**: 
  - Receive task requests from clients
  - Instantiate Orchestrator
  - Return execution results
- **Endpoint**: `POST /execute`
- **Input**: `TaskRequest { task: str }`
- **Output**: `{ original_task: str, results: [ExecutionResult] }`

#### **3.2.2 Orchestrator** (`orchestrator.py`)
- **Role**: Central workflow coordinator
- **Responsibility**:
  - Initialize all agents (Planner, Executor, Reviewer)
  - Create and manage TaskState
  - Execute the three-phase pipeline
  - Manage retry logic and error handling
- **Key Method**: `async run(task: str) → TaskState`
- **Process**:
  1. Phase 1: Task Planning (PlannerAgent)
  2. Phase 2: Subtask Execution (ExecutorAgent + ReviewerAgent)
  3. Phase 3: Result Collection & Return

#### **3.2.3 Agent Layer** (`agents/`)

**Base Agent** (`agents/base.py`)
```python
- Abstract base class for all agents
- Defines interface: async run(state: TaskState)
- Ensures consistency across all agent types
```

**PlannerAgent** (`agents/planner.py`)
- **Purpose**: Decompose complex tasks into subtasks
- **Input**: Original task description
- **LLM Prompt**: 
  - Role: "Senior software architect"
  - Task: Break task into 3-5 concrete engineering subtasks
  - Output Format: JSON array (enforced)
- **Output**: `List[str]` of subtasks
- **Error Handling**: Single retry if JSON parsing fails
- **JSON Extraction**: Uses regex fallback if direct parsing fails

**ExecutorAgent** (`agents/executor.py`)
- **Purpose**: Execute each subtask in detail
- **Input**: Current subtask from state
- **LLM Prompt**:
  - Role: "Senior backend engineer"
  - Task: Provide technical, structured solution
  - Context: Current subtask
- **Output**: Detailed execution text
- **No Validation**: Raw output passed to Reviewer

**ReviewerAgent** (`agents/reviewer.py`)
- **Purpose**: Validate execution quality
- **Input**: Subtask + Execution output
- **LLM Prompt**:
  - Role: "Strict code reviewer"
  - Task: Evaluate execution (PASS/FAIL)
  - Output Format: JSON with status & reason
- **Output**: `{ status: "PASS" | "FAIL", reason: str }`
- **Strict Validation**: Throws exception if invalid JSON

#### **3.2.4 Ollama Client** (`ollama_client.py`)
- **Role**: LLM communication interface
- **Configuration**:
  - URL: `http://localhost:11434/api/chat`
  - Model: `qwen2.5:7b`
  - Temperature: `0` (deterministic responses)
  - Timeout: `320` seconds
  - Stream: `False` (wait for full response)
- **Method**: `call_ollama(prompt: str) → str`
- **Responsibility**:
  - Format HTTP requests to Ollama API
  - Handle responses and errors
  - Return model output as string
  - Log raw responses for debugging

#### **3.2.5 State Management** (`state.py`)

**TaskState**
```python
- original_task: str              # Initial user task
- subtasks: List[str]             # Decomposed subtasks
- current_subtask: str | None     # Active subtask
- results: List[ExecutionResult]  # Completed results
- retry_count: int                # Current retry count
- max_retries: int = 1            # Maximum retry attempts
```

**ExecutionResult**
```python
- subtask: str                # The subtask name
- output: str                 # Executor's output
- review_status: str          # "PASS" or "FAILED"
- review_reason: str          # Reviewer's feedback
```

---

## 4. Data Flow & Processing Pipeline

### 4.1 End-to-End Flow

```
User Task
   │
   ▼
┌─────────────────────┐
│  FastAPI /execute   │
│   (TaskRequest)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Orchestrator      │
│   .run(task)        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Create TaskState   │
│  (original_task)    │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────┐
│  PHASE 1: PLANNING       │
│  PlannerAgent.run(state) │
│  LLM: Break into tasks   │
└──────────┬───────────────┘
           │
           ▼ state.subtasks = [...]
┌──────────────────────────┐
│  PHASE 2: EXECUTION LOOP │
│  FOR each subtask:       │
│                          │
│  ┌─────────────────────┐ │
│  │ RETRY LOOP          │ │
│  │                     │ │
│  │ ExecutorAgent.run() │ │
│  │ LLM: Execute task   │ │
│  │         ↓           │ │
│  │ ReviewerAgent.run() │ │
│  │ LLM: Review output  │ │
│  │         ↓           │ │
│  │ If PASS: break      │ │
│  │ If FAIL: retry++    │ │
│  │ If max exceeded:    │ │
│  │   mark FAILED       │ │
│  │                     │ │
│  └─────────────────────┘ │
│                          │
│  Append ExecutionResult  │
└──────────┬───────────────┘
           │
           ▼
┌─────────────────────────┐
│  Return TaskState       │
│  (with all results)     │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  FastAPI Response       │
│  {original_task,        │
│   results[]}            │
└──────────┬──────────────┘
           │
           ▼
        Client
```

### 4.2 Retry Mechanism

```
For each subtask:
│
├─ Retry Attempt 1
│  ├─ Execute subtask
│  ├─ Review result
│  └─ If FAIL → increment retry_count
│
├─ Retry Attempt 2 (if retry_count ≤ max_retries)
│  ├─ Execute subtask again
│  ├─ Review result
│  └─ If FAIL → check if max_retries exceeded
│
└─ Result Decision
   ├─ If PASS: Store ExecutionResult with status="PASS"
   └─ If all retries exhausted: Store with status="FAILED"
```

---

## 5. Agent Specifications

### 5.1 PlannerAgent

| Aspect | Details |
|--------|---------|
| **Role** | Task Decomposition |
| **Input** | `TaskState.original_task` |
| **Output** | `List[str]` subtasks |
| **LLM Role Prompt** | Senior software architect |
| **Output Format** | JSON array (enforced) |
| **Validation** | Regex-based JSON extraction with fallback |
| **Retry Logic** | Single retry if parsing fails |
| **Model Temperature** | 0 (deterministic) |

**Sample Prompt:**
```
Your are a senior software architect.
Break the following task into 3-5 concrete engineering substasks.

CRITICAL RULES:
- output MUST be JSON
- Only output JSON array
- No explanation

Example:
["design system architecture","define kafka topics","implement producer service"]

Task: {original_task}
```

### 5.2 ExecutorAgent

| Aspect | Details |
|--------|---------|
| **Role** | Task Execution |
| **Input** | `TaskState.current_subtask` |
| **Output** | `str` (detailed solution) |
| **LLM Role Prompt** | Senior backend engineer |
| **Output Format** | Free text (no validation) |
| **Retry Logic** | Handled by Orchestrator |
| **Model Temperature** | 0 (deterministic) |

**Sample Prompt:**
```
Your are a senior backend engineer.

Execute the following engineering task in detail.
Be technical and structured.

Task: {current_subtask}
```

### 5.3 ReviewerAgent

| Aspect | Details |
|--------|---------|
| **Role** | Quality Assurance |
| **Input** | `TaskState.current_subtask`, execution output |
| **Output** | `Dict` with status & reason |
| **LLM Role Prompt** | Strict code reviewer |
| **Output Format** | JSON (enforced, strict validation) |
| **Validation** | Throws exception if invalid |
| **Model Temperature** | 0 (deterministic) |

**Sample Prompt:**
```
You are a strict code reviewer.
Evaluate the execution result below.

Return ONLY valid JSON in this format:
{
 "status": "PASS" or "FAIL",
 "reason": "short explanation"
}

subtask: {current_subtask}
Execution: {execution_output}
```

---

## 6. LLM Integration Strategy

### 6.1 Model Configuration
- **Model**: Qwen2.5:7B (via Ollama)
- **Host**: `localhost:11434`
- **API**: Chat Completion (`/api/chat`)
- **Temperature**: 0 (reproducible outputs)
- **Stream**: False (wait for full response)
- **Timeout**: 320 seconds (for large responses)

### 6.2 Prompt Engineering

**Three-Tier Role Prompting:**
1. **Planner**: "Senior software architect" → Strategic thinking
2. **Executor**: "Senior backend engineer" → Technical implementation
3. **Reviewer**: "Strict code reviewer" → Quality assessment

**Output Control:**
- Explicit output format requirements (JSON where needed)
- JSON examples provided
- Fallback extraction logic (regex patterns)
- Strict validation with retry/exception handling

### 6.3 Communication Pattern

```
Agent
  │
  ├─ Create specialized prompt
  │  (with role, task, output format)
  │
  ├─ Call: call_ollama(prompt)
  │
  ▼
Ollama Client
  │
  ├─ Format request
  │  { model, messages, temperature, stream, timeout }
  │
  ├─ POST to http://localhost:11434/api/chat
  │
  ▼
Ollama Server (qwen2.5:7b)
  │
  ├─ Process prompt
  ├─ Generate response
  │
  ▼
Ollama Client
  │
  ├─ Parse response JSON
  ├─ Extract message.content
  ├─ Log for debugging
  │
  ▼
Agent
  │
  ├─ Validate output format
  ├─ Extract JSON if needed (regex fallback)
  ├─ Return or retry
  │
  ▼
Orchestrator
```

---

## 7. Error Handling & Resilience

### 7.1 Error Categories

| Error Type | Location | Handling |
|-----------|----------|----------|
| **JSON Parse Error** | PlannerAgent | Single retry, throw exception if both fail |
| **Invalid Reviewer JSON** | ReviewerAgent | Throw exception (stops subtask) |
| **Ollama Connection Error** | OllamaClient | Exception propagates up |
| **Timeout** | OllamaClient | 320-second timeout, requests library handles |
| **Execution Quality** | Orchestrator | Automatic retry up to `max_retries` |
| **Max Retries Exceeded** | Orchestrator | Mark as FAILED, continue to next subtask |

### 7.2 Retry Strategy

```python
max_retries = 1  # Default: 1 retry (2 total attempts per subtask)

While retry_count <= max_retries:
    execution_output = executor.run(state)
    review = reviewer.run(state, execution_output)
    
    if review["status"] == "PASS":
        → Add successful result
        → break
    else:
        retry_count += 1
        if retry_count > max_retries:
            → Add FAILED result
            → break
        else:
            → Continue to next iteration
```

### 7.3 Logging & Monitoring

- **Planning Phase**: Raw LLM output logged
- **Execution Phase**: Raw LLM output logged
- **Review Phase**: Raw LLM response logged
- **All Responses**: Pretty-printed JSON for debugging

---

## 8. Key Design Patterns

### 8.1 Agent Pattern
```
Abstract BaseAgent
    ├── PlannerAgent
    ├── ExecutorAgent
    └── ReviewerAgent

All implement: async run(state)
Promotes: Extensibility, consistency, testability
```

### 8.2 Pipeline Pattern
```
Task → Planner → Executor → Reviewer → Result
       ↑___________________________ Retry Loop
```

### 8.3 State Machine Pattern
```
TaskState maintains workflow state:
- Original task
- Current subtask
- Partial results
- Retry counters

Orchestrator drives transitions
```

### 8.4 Strategy Pattern (Implicit)
```
Each agent = different strategy for task processing
Swappable implementations for different models/approaches
```

---

## 9. Data Structures

### 9.1 Task State Lifecycle

```
Creation:
  TaskState(original_task="...")
         ↓
  { original_task: "...",
    subtasks: [],
    current_subtask: None,
    results: [],
    retry_count: 0,
    max_retries: 1 }

After Planning:
  { original_task: "...",
    subtasks: ["task1", "task2", "task3"],  ← Updated by Planner
    current_subtask: None,
    results: [],
    retry_count: 0,
    max_retries: 1 }

During Execution (first subtask):
  { original_task: "...",
    subtasks: ["task1", "task2", "task3"],
    current_subtask: "task1",  ← Set by Orchestrator
    results: [],
    retry_count: 0,
    max_retries: 1 }

After First Subtask Completes:
  { original_task: "...",
    subtasks: ["task1", "task2", "task3"],
    current_subtask: "task2",  ← Advanced to next
    results: [ExecutionResult(...)],  ← Added result
    retry_count: 0,
    max_retries: 1 }

Final (all complete):
  { original_task: "...",
    subtasks: ["task1", "task2", "task3"],
    current_subtask: "task3",
    results: [
        ExecutionResult(...),  ← task1 result
        ExecutionResult(...),  ← task2 result
        ExecutionResult(...)   ← task3 result
    ],
    retry_count: 0,
    max_retries: 1 }
```

### 9.2 Execution Result Structure

```python
ExecutionResult {
    subtask: str              # "Implement user service"
    output: str               # LLM-generated solution
    review_status: str        # "PASS" or "FAILED"
    review_reason: str        # "Code structure is solid but missing error handling"
}
```

---

## 10. Technology Stack

| Layer | Technology |
|-------|-----------|
| **API Framework** | FastAPI (async) |
| **LLM** | Qwen2.5:7B (via Ollama) |
| **LLM Client** | Requests library (HTTP) |
| **Data Validation** | Pydantic |
| **Async Runtime** | asyncio (Python 3.7+) |
| **JSON Parsing** | Standard library + regex |

---

## 11. System Constraints & Assumptions

### 11.1 Constraints
- Ollama server must be running on `localhost:11434`
- Single Qwen2.5:7B model instance
- Synchronous Ollama calls (HTTP blocking)
- Max 320-second timeout per LLM call
- Linear subtask execution (no parallelization)

### 11.2 Assumptions
- LLM always produces valid responses (with retries)
- Reviewer can accurately assess execution quality
- Original task is well-formed and achievable
- Subtasks are independent and sequential
- Network connectivity to Ollama is stable

---

## 12. Scalability & Future Considerations

### 12.1 Current Limitations
- **Single-threaded Execution**: Subtasks processed sequentially
- **Single Model**: All agents use same model
- **No Caching**: Each task starts fresh
- **In-memory State**: No persistence between requests

### 12.2 Potential Enhancements
```markdown
1. **Parallelization**
   - Execute multiple subtasks concurrently
   - Use async task spawning

2. **Model Specialization**
   - Different models for different agent types
   - Model selection based on task type

3. **Caching/Memory**
   - Cache common subtask solutions
   - Persistent result logging

4. **Advanced Retry Logic**
   - Exponential backoff
   - Configurable retry per agent
   - Different strategies per failure type

5. **Monitoring & Analytics**
   - Success rate tracking
   - Performance metrics
   - LLM call statistics

6. **Dynamic Configuration**
   - Runtime adjustment of temperature
   - Configurable max_retries per task
   - Model switching

7. **Distributed Execution**
   - Message queue integration (RabbitMQ/Kafka)
   - Multiple Orchestrator instances
   - Distributed state management
```

---

## 13. API Contract

### 13.1 Request

```http
POST /execute
Content-Type: application/json

{
    "task": "Design and implement a real-time notification system for an e-commerce platform with Web Socket support and message persistence"
}
```

### 13.2 Response (Success)

```json
{
    "original_task": "Design and implement a real-time notification system...",
    "results": [
        {
            "subtask": "Design system architecture",
            "output": "The system should use a pub-sub pattern...",
            "review_status": "PASS",
            "review_reason": "Architecture is sound and scalable"
        },
        {
            "subtask": "Implement WebSocket server",
            "output": "Use FastAPI with WebSocket support...",
            "review_status": "PASS",
            "review_reason": "Implementation is correct and follows best practices"
        },
        {
            "subtask": "Implement message persistence",
            "output": "Use Redis for message queue...",
            "review_status": "FAILED",
            "review_reason": "Max retries exceeded - insufficient error handling"
        }
    ]
}
```

---

## 14. Security Considerations

### 14.1 Current Implementation
- No authentication on `/execute` endpoint
- No input validation/sanitization
- No rate limiting
- Localhost-only Ollama connection

### 14.2 Recommendations
- Add API key authentication
- Validate task length/complexity
- Implement rate limiting per client
- Add request logging
- Secure Ollama endpoint (auth, TLS)
- Input sanitization for prompt injection prevention

---

## 15. Summary

The Multi-Agent AI Scraper System implements a **three-phase pipeline** (Planning → Execution → Review) with **automatic quality assurance and retry mechanisms**. By leveraging specialized agent roles and strict output validation, the system achieves reliable task decomposition and execution while maintaining flexibility for future enhancements.

**Key Strengths:**
✓ Clear separation of concerns (planning, execution, review)  
✓ Built-in quality assurance loop  
✓ Automatic retry mechanism for failed subtasks  
✓ Extensible agent architecture  
✓ Deterministic LLM outputs (temperature=0)  

**Future Focus:**
→ Parallelization of subtask execution  
→ Distributed state management  
→ Advanced metrics and monitoring  
→ Security hardening  
