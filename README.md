# Gala Assistant Dashboard

This project provides a Streamlit dashboard for Alfred, an assistant that answers questions about gala guests using a local dataset and can also use web and weather tools. The dashboard is the user-facing application; the agent runs behind it to generate answers.

## Dashboard

The dashboard is implemented in [src/dashboard.py](src/dashboard.py). It provides:

- A chat interface with suggested prompts and a conversation history.
- A guest context summary and an operational trace of questions and answers.
- Access to the guest dataset, web search, webpage reading, and weather information through the assistant.

The agent orchestration and local Ollama model are defined in [src/app.py](src/app.py). You normally do not launch that file directly: Streamlit loads it when the dashboard starts.

## Requirements

- Python 3.10 or later.
- [Ollama](https://ollama.com/download) installed and running locally.
- The `qwen2.5` model downloaded through Ollama.
- The guest dataset at [data/gala-invitees.parquet](data/gala-invitees.parquet), sourced from the public [Hugging Face AI Agents Course](https://huggingface.co/learn/agents-course).

No API key or `.env` file is required by the current implementation.

## Run the dashboard on Windows

Run these commands from the repository root in PowerShell.

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents script activation, you can run the setup script instead (after installing Ollama):

```powershell
powershell -ExecutionPolicy Bypass -File .\config\setup_env.ps1
```

### 2. Install the project and development dependencies

Install the project from `pyproject.toml` (including pytest for local checks):

```powershell
python -m pip install -e ".[dev]"
```

The setup script above already installs the project and its development dependencies.

### 3. Start Ollama and download the model

Make sure the Ollama service is running, then download the model:

```powershell
ollama pull qwen2.5
```

If Ollama is not already running as a service, start it in a separate terminal:

```powershell
ollama serve
```

The setup script also runs `ollama pull qwen2.5`.

### 4. Launch the dashboard

```powershell
streamlit run .\src\dashboard.py
```

Streamlit prints a local URL in the terminal (usually `http://localhost:8501`) and opens the dashboard in your browser. Keep the terminal and Ollama running while using the app.

## Project structure

```text
RAG UseCase/
├── config/
│   └── setup_env.ps1
├── data/
│   └── gala-invitees.parquet
├── src/
│   ├── agent/
│   │   ├── prompts.py
│   │   ├── retriever.py
│   │   └── tools.py
│   ├── app.py
│   └── dashboard.py
├── tests/
│   ├── test_agent_guards.py
│   ├── test_retriever.py
│   └── test_tools.py
├── docs/
│   └── PROJECT_OVERVIEW.md
├── README.md
└── pyproject.toml
```

## How it works

- [src/dashboard.py](src/dashboard.py) renders the Streamlit interface and passes chat messages to Alfred.
- [src/app.py](src/app.py) builds the LangGraph workflow and connects it to the local `qwen2.5` model through Ollama.
- [src/agent/retriever.py](src/agent/retriever.py) loads the parquet guest data and retrieves relevant guest information.
- [src/agent/prompts.py](src/agent/prompts.py) defines the assistant's response instructions.
- [src/agent/tools.py](src/agent/tools.py) provides weather, web search, and webpage-reading tools.

The project setup helper is [config/setup_env.ps1](config/setup_env.ps1). For a concise description of the current release, see [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md).

## Dataset attribution

The guest dataset is public course material from the [Hugging Face AI Agents Course](https://huggingface.co/learn/agents-course); it is not presented here as fictional or independently created. Public availability does not by itself establish permission to redistribute or relicense it, so check the course's applicable license and attribution terms before republishing the dataset or deploying it in a public demo.

## Run tests

With the development dependencies installed, run the local, network-independent tests from the repository root:

```powershell
python -m pytest
```
