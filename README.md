# Gala Agent Project

This project is a small but complete Retrieval-Augmented Generation (RAG) agent built around a fictional luxury gala scenario. The goal is to create an assistant named Alfred that answers guest-related questions using an event dataset instead of relying only on generic model memory.

The current implementation is intentionally simple and modular: it loads a guest dataset, retrieves the most relevant record, builds a prompt, and sends it to a local Ollama model for a constrained answer.

## How this project was built

### 1. Use case definition

The project started from a clear business problem:

- a gala host needs a polished assistant
- guest information must be accurate and specific
- the model should answer only the requested person or topic
- the agent must not invent information or expand beyond the dataset

This is why the solution is not a generic chatbot, but a focused agentic RAG workflow.

### 2. Data source and retrieval layer

The main dataset lives in:

- [data/gala-invitees.parquet](data/gala-invitees.parquet)

The retrieval logic is implemented in:

- [src/retriever.py](src/retriever.py)

That file does the following:

- reads the parquet file with pandas
- converts each guest into a LangChain Document
- creates a BM25 retriever
- prefers exact-name matches first
- falls back to ranked retrieval when necessary
- returns only the best record for the query

This is the key step that keeps the agent grounded in known guest data.

### 3. Prompt design and behavior control

The instructions sent to the model are defined in:

- [src/prompts.py](src/prompts.py)

The system prompt explicitly tells the model to:

- answer only the guest the user asked about
- avoid mentioning other guests unless explicitly requested
- avoid extra anecdotes or side facts
- never invent details
- remain professional and elegant in tone

This was important because without strict instructions, the model tends to expand beyond the original question.

### 4. Agent orchestration

The main runtime entry point is:

- [src/app.py](src/app.py)

This file:

- loads environment variables
- initializes the local Ollama model
- binds the guest retrieval tool to the model
- builds an agent state using LangGraph
- invokes the tool and the model together
- prints the final answer for a sample question

The model used in the current setup is a local Ollama model:

- qwen2.5

This avoids external paid API dependency and keeps the project simple to run locally.

### 5. Tool structure

The current project keeps tool logic intentionally minimal and modular in:

- [src/tools.py](src/tools.py)

Right now it exists as a placeholder for future event-related helper tools, while the active guest lookup logic is handled directly by the retriever layer.

## Actual project structure

This is the real structure of the repository today:

```text
RAG UseCase/
├── .env
├── .gitignore
├── .venv/
├── config/
│   ├── requirements.txt
│   └── setup_env.ps1
├── data/
│   └── gala-invitees.parquet
├── pyproject.toml
├── PROJECT_OVERVIEW.md
├── README.md
└── src/
    ├── app.py
    ├── prompts.py
    ├── retriever.py
    └── tools.py
```

## What each file does

### Root files

- [pyproject.toml](pyproject.toml)  
  Project metadata and packaging information for Python. It is lightweight and not the main dependency source for runtime setup.

- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)  
  Conceptual project description of the gala scenario and the purpose of the agent.

- [.gitignore](.gitignore)  
  Ignores local environment files such as .env.

- [.env](.env)  
  Local environment variables for the developer machine. It is not meant to be committed.

### Configuration folder

- [config/requirements.txt](config/requirements.txt)  
  Dependency list used to set up the project environment.

- [config/setup_env.ps1](config/setup_env.ps1)  
  PowerShell helper that creates the venv, installs dependencies, and pulls the local Ollama model.

### Source folder

- [src/app.py](src/app.py)  
  Application entry point and LangGraph orchestration.

- [src/retriever.py](src/retriever.py)  
  Guest dataset loading and retrieval logic.

- [src/prompts.py](src/prompts.py)  
  System prompt for the assistant.

- [src/tools.py](src/tools.py)  
  Future place for the agent’s helper tools.

## Environment setup

The project uses a local Python virtual environment and a local Ollama model.

### 1. Create the virtual environment

```powershell
python -m venv .venv
```

### 2. Activate it

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\config\setup_env.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r .\config\requirements.txt
```

### 4. Pull the local model

```powershell
ollama pull qwen2.5
```

### 5. Run the app

```powershell
python .\src\app.py
```

## Current implementation status

This version is a working foundation for:

- guest retrieval from a parquet dataset
- exact-match and BM25 ranking
- a strict prompt for a gala assistant
- local LLM execution through Ollama
- agent orchestration with LangGraph

The project is intentionally compact and professional, without adding unnecessary infrastructure like Docker or a complex monorepo setup.

## Why this structure works

The design is simple because each concern has a clear place:

- data is stored separately in [data](data)
- runtime dependencies live in [config](config)
- Python logic lives in [src](src)
- the project concept lives in [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)

This keeps the repository easy to understand, easy to extend, and easy to run locally.

---

This README reflects the actual state of the repository as it exists now. The higher-level project concept remains in [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md).
