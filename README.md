# A Gala to Remember

This repository is the foundation for an agentic Retrieval-Augmented Generation (RAG) project built around a fictional but realistic gala-planning scenario.

The goal is to create an assistant named Alfred that can plan, support, and answer questions during an extravagant event. Alfred must be able to retrieve up-to-date information about guests, weather, and event logistics, while also making useful recommendations and handling unexpected situations.

## How this project was done

### 1. Define the use case

The project starts from a concrete business scenario:

- A host wants to organize a world-class gala
- The assistant must support planning, guest relations, and live event operations
- The assistant cannot rely only on general model knowledge, because event details are unique and time-sensitive

This is why the project is built around an agentic RAG approach instead of a simple question-answer bot.

### 2. Use an agentic approach

Instead of blindly answering from a single static prompt, Alfred is treated as an agent that can decide when to:

- Search party information
- Retrieve guest-specific data
- Check live or external weather context
- Answer questions based on the most relevant facts
- Use tools when needed

This matches the idea that an agent should not be limited to a single document pipeline. It should be able to choose the best available tool or workflow for each request.

### 3. Build a custom retrieval layer

The guest dataset is the project’s information foundation. Each guest record contains:

- Name
- Relation to host
- Description / biography
- Email address

A retrieval component is needed so Alfred can search this dataset efficiently and provide highly relevant information, rather than guessing from model memory.

### 4. Use RAG for domain-specific knowledge

Large language models are trained on broad information, but they do not automatically know the details of your own event or the exact relationships between invitees. RAG solves this by:

- Storing structured event data
- Retrieving relevant records for a query
- Passing those records into the language model as context
- Letting the model produce answers grounded in the retrieved information

This is especially important for guest stories, contact information, and personalized event recommendations.

### 5. Separate responsibilities into modules

The project is organized so that different concerns live in different files:

- `tools.py`: auxiliary tools used by the agent
- `retriever.py`: retrieval logic and dataset access
- `app.py`: orchestration for the full agent workflow

This keeps the design modular and easy to extend later.

## Project goal

The final application is intended to support Alfred in several ways:

- Planning and preparing the gala
- Answering guest-related questions
- Recalling notable details about attendees
- Using retrieval for personalized information
- Monitoring event needs in real time
- Supporting smooth event execution with relevant knowledge

## Core concept

The central idea is simple:

A great host does not just throw a party. A great host understands the people attending, the timing of the event, and the practical details required for a smooth experience. Alfred acts as that intelligent event assistant.

## Expected future development

This initial version is only the foundation. The next steps will be to:

- create the retrieval logic
- add tool functions for queries, guests, and weather
- connect the components inside the main app
- refine the agent’s behavior for real-time event support

## Professional project foundation

The repository has a clean project structure that is intentionally simple and easy to work with.

### Core structure

- `src/gala_agent/` — main Python package for the application
- `src/gala_agent/core/` — configuration and service settings
- `src/gala_agent/retrieval/` — retrieval logic for guest and event knowledge
- `src/gala_agent/tools/` — custom tool functions for Alfred
- `data/` — datasets and event knowledge assets
- `tests/` — validation and regression tests
- `docs/` — architecture and project documentation
- `scripts/` — optional local automation

### Quick environment setup

The project is designed to run in a lightweight local virtual environment, without Docker or extra build complexity.

This version uses a local Ollama model instead of a paid external API, so the setup is transparent and does not require a secret key in the repository.

1. Create the environment:
   `python -m venv .venv`
2. Activate it:
   `.venv\Scripts\Activate.ps1`
3. Install the dependencies:
   `python -m pip install --upgrade pip`
   `python -m pip install -r requirements.txt`
4. Install the local LLM model:
   `ollama pull qwen2.5`
5. Run the app:
   `python app.py`

A PowerShell helper script is also included at [setup_env.ps1](setup_env.ps1) to automate this setup.

This keeps the environment professional, stable, and easy to manage without unnecessary tooling or paid API dependencies.

---

This README records the implementation approach used for the project. The project description and agent purpose are documented in the companion file [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md).
