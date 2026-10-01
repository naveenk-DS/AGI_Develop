# 🧠 NAVIX — Personal AI Operating System

> **A local-first, voice-enabled, agentic AI assistant built from scratch with Python, FastAPI, Ollama, RAG, Qdrant, LangChain, LangGraph, automation, memory, and a real-time HUD.**

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black)](https://ollama.com/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-red)](https://qdrant.tech/)
[![LangChain](https://img.shields.io/badge/LangChain-LLM%20Framework-green)](https://www.langchain.com/)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker)](https://www.docker.com/)
[![CUDA](https://img.shields.io/badge/CUDA-12.1-76B900?logo=nvidia)](https://developer.nvidia.com/cuda-toolkit)

---

## 📌 Overview

**NAVIX** is a local-first personal AI operating system designed to combine conversational AI, voice interaction, retrieval-augmented generation, personal memory, automation, and computer interaction into one unified assistant.

Instead of treating an LLM as only a chatbot, NAVIX provides an orchestration layer around local AI models and multiple tools.

The system can:

* 🎙️ Listen to voice commands
* 🔊 Respond using speech
* 🧠 Run local LLM inference through Ollama
* 📚 Answer questions using RAG
* 🔎 Search documents through vector retrieval
* 🧩 Classify user intent and route tasks
* 💻 Automate desktop workflows
* 🌐 Automate browser workflows
* 👁️ Support vision-related workflows
* 🤖 Execute agent-based tasks
* 🧠 Maintain personal memory and context
* ⏰ Create reminders and daily plans
* 📰 Provide scheduled information/briefings
* 💬 Integrate with WhatsApp services
* 🖥️ Display activity through a browser-based HUD
* 📊 Expose a FastAPI backend
* 💾 Persist vector data with Qdrant
* 🐳 Run through Docker Compose
* 🩺 Monitor application health
* 🔄 Run background learning/watch processes

The project is intended as an **AI engineering / agentic systems project**, demonstrating how multiple AI components can be combined into a practical local assistant.

---

# ✨ Core Features

## 🎙️ 1. Voice-First Interaction

NAVIX provides a voice conversation pipeline:

```text
Microphone
    ↓
Speech Recognition
    ↓
Command / Intent Detection
    ↓
AI Reasoning / Tool Routing
    ↓
LLM / RAG / Automation
    ↓
Text Response
    ↓
Text-to-Speech
    ↓
Speaker
```

The voice engine contains:

* Speech input
* Wake-word listener
* Voice activity flow
* Text-to-speech
* Conversational loop
* Voice authentication
* Conversation state
* Graceful fallback responses

The main voice engine is implemented in:

```text
navix/services/voice/NAVIX_AI.py
```

NAVIX currently uses Ollama for local model communication and is configured around the `qwen2.5:7b` model by default.

---

# 🧠 2. Local LLM Inference

NAVIX uses **Ollama** for local LLM inference.

The core LLM layer is implemented using:

```text
LangChain
    ↓
langchain-ollama
    ↓
Ollama
    ↓
Local LLM
```

Default conversational model:

```text
qwen2.5:7b
```

Default embedding model:

```text
nomic-embed-text
```

A separate personality model configuration is also supported:

```text
navix-personality
```

The LLM configuration is centralized in:

```text
core/llm.py
```

This architecture keeps model communication local and allows the project to be adapted to different Ollama models.

---

# 📚 3. Retrieval-Augmented Generation

NAVIX includes a complete RAG pipeline using:

* Qdrant
* Ollama embeddings
* LangChain
* Recursive text splitting
* Similarity retrieval
* Context injection
* Local LLM generation

Architecture:

```text
Documents
    ↓
Text Extraction
    ↓
Chunking
    ↓
Ollama Embeddings
    ↓
Qdrant Vector Database
    ↓
Similarity Search
    ↓
Relevant Context
    ↓
Prompt
    ↓
Local LLM
    ↓
Answer
```

The RAG implementation is located in:

```text
core/rag_chain.py
```

Documents are split into chunks before indexing.

Current configuration:

```text
Chunk size:    400
Chunk overlap: 50
Retrieval K:   3
Distance:      Cosine
Vector size:   768
```

The system is instructed to avoid fabricating answers when the requested information is not present in the retrieved documents.

---

# 🤖 4. Intent-Based Agent Routing

NAVIX does not send every request directly to the LLM.

User commands are first classified and routed based on intent.

Example:

```text
User Command
     │
     ▼
Intent Classifier
     │
     ├── PC
     │
     ├── Browser
     │
     ├── Vision
     │
     ├── Automation
     │
     ├── Code
     │
     ├── RAG
     │
     └── Chat
```

For example:

```text
"Open Chrome and search for AI jobs"
        ↓
browser / automation
        ↓
Autonomous workflow
```

```text
"What is in my project documentation?"
        ↓
RAG
        ↓
Qdrant retrieval
        ↓
LLM answer
```

```text
"Write a Python script for this"
        ↓
code
        ↓
Code generation workflow
```

This routing layer is implemented inside the NAVIX voice conversation engine.

---

# 💻 5. Desktop Automation

NAVIX includes computer interaction capabilities for tasks involving:

* Desktop applications
* Mouse interaction
* Keyboard interaction
* Screen interaction
* Workflow execution
* Autonomous computer tasks

Relevant components include:

```text
navix/automation/
navix/routers/desktop_routes.py
```

The project uses tools such as:

* PyAutoGUI
* Playwright
* Computer/desktop workflow controllers

The goal is to allow natural-language commands to be translated into executable workflows.

---

# 🌐 6. Browser Automation

NAVIX includes browser automation capabilities through Playwright.

Example conceptual workflow:

```text
User:
"Open the browser and search for Python AI jobs"

        ↓

Intent Detection

        ↓

Browser Workflow

        ↓

Playwright

        ↓

Website Interaction

        ↓

Result

        ↓

NAVIX Voice Response
```

Playwright Chromium is also installed as part of the Docker build.

---

# 🧩 7. Agent System

The project contains dedicated agent routes and automation components.

Relevant areas include:

```text
navix/routers/agent.py
navix/routers/agent_routes.py
navix/automation/
core/
```

The architecture is designed around tool selection and task execution rather than simple prompt → response interaction.

This makes NAVIX closer to an **agentic AI application** than a conventional chatbot.

---

# 🧠 8. Personal Memory

NAVIX contains a personal memory subsystem.

The system can maintain contextual information that can be used to make future interactions more relevant.

Memory-related components include:

```text
navix/services/memory/
navix/routers/memory_routes.py
```

The voice system also retrieves personal context before processing certain commands.

Conceptually:

```text
User
 ↓
Current Command
 ↓
Personal Memory
 ↓
Context Construction
 ↓
LLM
 ↓
Context-Aware Response
```

---

# 🔐 9. Voice Authentication

NAVIX includes PIN-based authentication for voice interaction.

The authentication flow can require a PIN before allowing the assistant to continue.

Relevant component:

```text
navix/services/voice/pin_auth.py
```

The system can also lock the assistant again through voice commands such as:

```text
"Lock NAVIX"
```

and return to a sleeping state.

---

# ⏰ 10. Reminders & Daily Planning

NAVIX includes personal productivity functionality.

Supported concepts include:

* Daily planning
* Saving daily plans
* Previous-day plan retrieval
* Reminders
* Daily reflection
* Scheduled background jobs

Example:

```text
"Remind me to apply for AI jobs at 6 PM"
```

NAVIX parses the reminder request and schedules it through its reminder subsystem.

---

# 📰 11. Information Briefings

NAVIX can provide scheduled information briefings.

For example, the startup flow can retrieve headlines and summarize them through the local model.

The architecture allows information retrieval to be combined with the conversational voice interface.

---

# 🖥️ 12. Real-Time HUD

NAVIX includes a browser-based HUD:

```text
navix_hud_ui/
```

The launcher starts a local HUD server on:

```text
http://localhost:5500
```

The HUD can reflect assistant states such as:

```text
sleeping
    ↓
listening
    ↓
thinking
    ↓
working
    ↓
talking
```

The backend also exposes HUD-related routes so the interface can receive assistant state and conversation updates.

---

# ⚡ 13. FastAPI Backend

NAVIX is built around FastAPI.

Main backend:

```text
navix/main.py
```

The API includes multiple routers covering areas such as:

* RAG
* Chat
* Summary
* Configuration
* Licensing
* Dashboard
* Agents
* Backups
* Templates
* Sessions
* Streaming
* Webhooks
* Analytics
* Settings
* Voice
* Browser
* Desktop
* Memory
* HUD
* WhatsApp

Basic health endpoint:

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

A basic chat endpoint is also available:

```http
POST /chat
```

---

# 🏗️ Architecture

High-level architecture:

```text
                         ┌──────────────────────┐
                         │       USER           │
                         └──────────┬───────────┘
                                    │
                         Voice / Text / UI
                                    │
                                    ▼
                     ┌───────────────────────────┐
                     │          NAVIX            │
                     │   AI Operating System     │
                     └─────────────┬─────────────┘
                                   │
                  ┌────────────────┼─────────────────┐
                  │                │                 │
                  ▼                ▼                 ▼
             Voice Layer      FastAPI API       HUD / UI
                  │                │                 │
                  └────────────────┼─────────────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │ Intent Classifier │
                         └─────────┬─────────┘
                                   │
        ┌──────────────┬───────────┼───────────┬──────────────┐
        │              │           │           │              │
        ▼              ▼           ▼           ▼              ▼
      Chat            RAG        Code      Automation      Agents
        │              │           │           │              │
        │              ▼           │           ├── Browser    │
        │          ┌────────┐      │           ├── Desktop    │
        │          │ Qdrant │      │           └── Vision     │
        │          └────┬───┘      │
        │               │          │
        └───────────────┼──────────┘
                        ▼
                 ┌──────────────┐
                 │    Ollama    │
                 │  Local LLMs  │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ AI Response  │
                 └──────┬───────┘
                        │
                  Text / Voice
                        │
                        ▼
                     USER
```

---

# 🔄 Startup Architecture

The main launcher is:

```text
navix_start.py
```

Startup sequence:

```text
Start NAVIX
    │
    ├── Start FastAPI backend
    │       └── localhost:8001
    │
    ├── Start HUD
    │       └── localhost:5500
    │
    ├── Start system tray
    │
    ├── Start async NAVIX engine
    │
    ├── Start WhatsApp background service
    │
    ├── Authenticate user
    │
    ├── Initialize memory / onboarding
    │
    ├── Warm up Ollama
    │
    └── Start voice interaction
```

The launcher currently starts the local API on port `8001` and the HUD on port `5500`.

---

# 🧱 Project Structure

```text
AGI_Develop/
│
├── .github/
│   └── workflows/
│
├── artifacts/
│
├── config/
│
├── core/
│   ├── llm.py
│   ├── rag_chain.py
│   ├── graph/
│   ├── emotion/
│   └── ...
│
├── installer/
│
├── navix/
│   ├── automation/
│   │
│   ├── config/
│   │
│   ├── db/
│   │
│   ├── middleware/
│   │
│   ├── routers/
│   │
│   ├── services/
│   │   ├── ai/
│   │   ├── memory/
│   │   ├── utilities/
│   │   └── voice/
│   │
│   └── main.py
│
├── navix_hud_ui/
│
├── scripts/
│
├── screenshots/
│
├── tests/
│
├── watch/
│
├── Dockerfile
├── docker-compose.yml
├── START_NAVIX.bat
├── navix_start.py
├── navix_tray.py
├── pyproject.toml
├── uv.lock
├── .env
└── README.md
```

---

# 🛠️ Technology Stack

| Category           | Technology                     |
| ------------------ | ------------------------------ |
| Language           | Python 3.12                    |
| API                | FastAPI                        |
| ASGI Server        | Uvicorn                        |
| LLM Runtime        | Ollama                         |
| LLM Framework      | LangChain                      |
| Agent Workflow     | LangGraph                      |
| Vector Database    | Qdrant                         |
| Embeddings         | Ollama / `nomic-embed-text`    |
| ML                 | PyTorch                        |
| Transformers       | Hugging Face Transformers      |
| Speech-to-Text     | Faster Whisper / Whisper       |
| Text-to-Speech     | Edge TTS / Pyttsx3 / Kokoro    |
| Voice Input        | PyAudio / SoundDevice          |
| Browser Automation | Playwright                     |
| Desktop Automation | PyAutoGUI                      |
| Database           | PostgreSQL / SQLite components |
| ORM                | SQLAlchemy                     |
| Scheduling         | APScheduler                    |
| Validation         | Pydantic                       |
| Logging            | Loguru                         |
| Containers         | Docker                         |
| GPU                | NVIDIA CUDA 12.1               |
| Dependency Manager | uv                             |

The current `pyproject.toml` targets Python `>=3.12,<3.13` and includes the project's AI, voice, web, database, vector-search, and automation dependencies.

---

# 💻 Requirements

## Minimum Development Requirements

Recommended:

```text
Python 3.12
Git
Ollama
Qdrant
FFmpeg
Microphone
Speakers
```

For GPU acceleration:

```text
NVIDIA GPU
CUDA-compatible environment
```

The project currently pins:

```text
torch==2.5.1
torchvision==0.20.1
torchaudio==2.5.1
```

and configures the PyTorch CUDA 12.1 package index.

---

# 🚀 Installation

## 1. Clone the repository

```bash
git clone https://github.com/naveenk-DS/AGI_Develop.git
cd AGI_Develop
```

---

## 2. Install `uv`

If `uv` is not already installed:

```bash
pip install uv
```

Verify:

```bash
uv --version
```

---

## 3. Create the environment

```bash
uv sync
```

This installs the Python dependencies defined in `pyproject.toml`.

---

# 🧠 Configure Ollama

Install Ollama and make sure the Ollama server is running.

Default endpoint:

```text
http://127.0.0.1:11434
```

Pull the default conversational model:

```bash
ollama pull qwen2.5:7b
```

Pull the embedding model:

```bash
ollama pull nomic-embed-text
```

For vision workflows, the default configuration references:

```text
llava:7b
```

You can pull it with:

```bash
ollama pull llava:7b
```

The model names and Ollama endpoint are configurable through the NAVIX settings.

---

# 🗄️ Start Qdrant

NAVIX uses Qdrant for vector storage.

Default configuration:

```text
Host: 127.0.0.1
Port: 6333
Collection: documents
```

The RAG layer automatically creates the `documents` collection if it does not already exist.

---

# 🔐 Environment Configuration

Create a:

```text
.env
```

file in the project root.

Example:

```env
ENVIRONMENT=development
DEBUG=true

OLLAMA_URL=http://127.0.0.1:11434
NAVIX_MODEL=qwen2.5:7b
VISION_MODEL=llava:7b

QDRANT_HOST=127.0.0.1
QDRANT_PORT=6333
```

Add any additional credentials required by optional integrations.

### Important

Never commit:

```text
.env
```

or API keys, passwords, tokens, private credentials, or production secrets to GitHub.

---

# ▶️ Running NAVIX

## Option 1 — Python

Run:

```bash
uv run python navix_start.py
```

This starts the NAVIX launcher.

The launcher:

* Starts the FastAPI server
* Starts the HUD
* Starts the system tray
* Starts the NAVIX async engine
* Starts background services
* Initializes the voice system

The current launcher uses:

```text
FastAPI: http://localhost:8001
HUD:     http://localhost:5500
```

The exact runtime behavior is implemented in `navix_start.py`.

---

# 🪟 Windows Startup

A Windows batch launcher is also included:

```text
START_NAVIX.bat
```

Run:

```text
START_NAVIX.bat
```

### Note

The existing batch file contains machine-specific Windows paths for Qdrant and the project directory.

You should update those paths for your own machine before using it.

---

# 🐳 Docker

NAVIX includes Docker support.

Build:

```bash
docker compose build
```

Start:

```bash
docker compose up
```

Or:

```bash
docker compose up -d
```

The Docker Compose setup contains three major services:

```text
NAVIX
Qdrant
Ollama
```

with persistent volumes for:

```text
Qdrant data
Ollama models
```

and GPU reservation configured for NVIDIA hardware.

---

# 🐳 Docker Architecture

```text
                 Docker Network
                       │
        ┌──────────────┼───────────────┐
        │              │               │
        ▼              ▼               ▼
   ┌─────────┐    ┌─────────┐    ┌─────────┐
   │  NAVIX  │───▶│ Qdrant  │    │ Ollama  │
   │ FastAPI │    │ Vector  │    │   LLM   │
   └────┬────┘    │   DB    │    └────┬────┘
        │         └─────────┘         │
        └─────────────────────────────┘
```

The Docker image is based on:

```text
Ubuntu 22.04
CUDA 12.1.1
Python 3.12
```

and installs Playwright Chromium during the image build.

---

# 📡 API

Once the backend is running:

```text
http://localhost:8001
```

Health check:

```http
GET /health
```

Example:

```bash
curl http://localhost:8001/health
```

Response:

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

# 💬 Chat API

Example:

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Hello NAVIX\"}"
```

Example response:

```json
{
  "reply": "Hello Naveen!"
}
```

---

# 📚 RAG Workflow

A typical document workflow looks like:

```text
Document
   ↓
Extract Text
   ↓
Split into Chunks
   ↓
Generate Embeddings
   ↓
Store in Qdrant
   ↓
User Question
   ↓
Similarity Search
   ↓
Top 3 Relevant Chunks
   ↓
Prompt Construction
   ↓
Ollama
   ↓
Answer
```

Example:

```text
User:
"What does my project documentation say about deployment?"

NAVIX:
     ↓
RAG intent
     ↓
Qdrant search
     ↓
Relevant documents
     ↓
Qwen 2.5
     ↓
Grounded answer
```

---

# 🎙️ Voice Conversation Flow

```text
                    ┌─────────────┐
                    │ Microphone  │
                    └──────┬──────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Speech Listener │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Intent Classifier│
                  └────────┬────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
             RAG          Agent        Chat
              │            │            │
              └────────────┼────────────┘
                           ▼
                     ┌──────────┐
                     │ Ollama   │
                     └────┬─────┘
                          │
                          ▼
                    ┌───────────┐
                    │ Response  │
                    └─────┬─────┘
                          │
                          ▼
                    Text-to-Speech
                          │
                          ▼
                       Speaker
```

---

# 🧠 Model Strategy

NAVIX separates different AI responsibilities instead of forcing one model to handle every task.

```text
                    NAVIX AI
                       │
        ┌──────────────┼───────────────┐
        │              │               │
        ▼              ▼               ▼
   Conversational     RAG          Vision
      LLM             LLM           Model
        │              │               │
        ▼              ▼               ▼
  qwen2.5:7b      Qdrant + LLM     llava:7b
```

This makes the system easier to extend with specialized models.

---

# 🧪 Testing

The repository contains:

```text
tests/
```

Development dependencies include:

```text
pytest
pytest-asyncio
httpx
```

Run tests with:

```bash
uv run pytest
```

For a more verbose run:

```bash
uv run pytest -v
```

---

# 📊 Observability & Logging

NAVIX uses **Loguru** for centralized logging.

Logs are written to:

```text
logs/navix_core.log
```

The logging configuration includes:

* Timestamp
* Log level
* Module
* Function
* Line number
* Message

Log rotation is configured at:

```text
50 MB
```

with retention of:

```text
10 days
```

The application also starts a background health monitor.

---

# 🔄 Background Services

The FastAPI lifespan initializes several background systems.

These include:

```text
Database initialization
        ↓
File watcher
        ↓
Scheduled backups
        ↓
Continual learning watcher
        ↓
MCP tool registration
        ↓
AI model preloading
        ↓
Health monitoring
```

The scheduler currently includes a daily backup job, while the application also starts model preloading and health monitoring during startup.

---

# 🔧 Configuration

Main configuration:

```text
navix/config/settings.py
```

Current core settings include:

```python
app_name = "NAVIX AI Operating System"
environment = "development"
debug = True

ollama_url = "http://127.0.0.1:11434"
navix_model = "qwen2.5:7b"
vision_model = "llava:7b"

qdrant_host = "127.0.0.1"
qdrant_port = 6333
```

Environment variables can override configuration through `.env`.

---

# 🔒 Security Considerations

NAVIX is primarily designed as a local development project.

Before exposing it to a network or production environment, review:

* API authentication
* API keys
* CORS configuration
* Rate limiting
* Voice authentication
* Browser automation permissions
* Desktop automation permissions
* `.env` secrets
* Database credentials
* Webhook security
* File access permissions
* Ollama network exposure

Do **not** expose a local automation agent directly to the public internet without adding appropriate authentication and authorization controls.

---

# ⚠️ Current Development Status

NAVIX is an **active development project**.

The repository contains many integrated subsystems, but not every subsystem should be considered production-ready.

Some components depend on:

* Local hardware
* NVIDIA GPU support
* Ollama models
* Qdrant
* Audio devices
* Browser installation
* OS-specific automation
* Environment-specific configuration

Therefore, functionality may vary depending on the machine and configuration.

---

# 🧭 Roadmap

Potential future improvements:

### AI / LLM

* [ ] Model abstraction layer
* [ ] More local model support
* [ ] Better model routing
* [ ] Structured tool calling
* [ ] Improved agent planning
* [ ] Model performance benchmarking
* [ ] Quantized model support
* [ ] Local inference optimization

### RAG

* [ ] Hybrid BM25 + vector retrieval
* [ ] Reranking
* [ ] Metadata filtering
* [ ] Document versioning
* [ ] Retrieval evaluation
* [ ] Citation-aware answers

### Agents

* [ ] More autonomous workflows
* [ ] Better planning/execution separation
* [ ] Tool permission system
* [ ] Workflow observability
* [ ] Agent evaluation framework

### Voice

* [ ] Streaming speech recognition
* [ ] Lower-latency TTS
* [ ] Better interruption handling
* [ ] Multilingual conversation
* [ ] Voice emotion awareness

### Security

* [ ] Stronger authentication
* [ ] Role-based permissions
* [ ] Tool-level authorization
* [ ] Secure remote access
* [ ] Secret management

### UI

* [ ] More advanced HUD visualization
* [ ] Agent execution timeline
* [ ] RAG visualization
* [ ] Memory browser
* [ ] System health dashboard

---

# 🧑‍💻 Development Philosophy

NAVIX is built around several principles:

### Local First

Use local models and local infrastructure whenever practical.

### Modular AI

Separate:

```text
LLM
RAG
Memory
Agents
Voice
Automation
API
UI
```

so individual components can evolve independently.

### Tool-Oriented Intelligence

An AI assistant becomes more useful when it can interact with tools and systems instead of only generating text.

### Observable Systems

AI workflows should be inspectable through logs, state transitions, health monitoring, and API responses.

### Practical AI Engineering

The objective is not simply to demonstrate an LLM.

The objective is to combine:

```text
Models
+
Data
+
Retrieval
+
Tools
+
Memory
+
Automation
+
APIs
+
User Interface
```

into a usable AI system.

---

# 📖 Learning / Engineering Concepts Demonstrated

This repository demonstrates practical implementation of:

* Large Language Models
* Local LLM inference
* Prompt engineering
* Embeddings
* Vector databases
* RAG
* Semantic search
* Intent classification
* Agent routing
* LangChain
* LangGraph
* FastAPI
* Async Python
* Background workers
* Voice AI
* Speech recognition
* Text-to-speech
* Browser automation
* Desktop automation
* Personal memory
* AI orchestration
* Docker
* GPU acceleration
* API design
* Logging
* Health monitoring
* Scheduled tasks
* Database integration

---

# 🏆 Project Highlights

NAVIX demonstrates how a local AI assistant can move beyond a basic chatbot architecture.

Instead of:

```text
User → Prompt → LLM → Response
```

NAVIX aims for:

```text
User
 ↓
Voice / UI
 ↓
Context + Memory
 ↓
Intent Detection
 ↓
Planner / Router
 ↓
 ┌───────────────┬───────────────┬───────────────┐
 │               │               │               │
 RAG            Agents        Automation        Chat
 │               │               │               │
 └───────────────┴───────────────┴───────────────┘
                         ↓
                    Local Models
                         ↓
                   Tool Execution
                         ↓
                    AI Response
```

This architecture provides a foundation for experimenting with more advanced agentic AI systems.

---

# 🤝 Contributing

Contributions, suggestions, bug reports, and improvements are welcome.

### Basic workflow

```bash
git clone https://github.com/naveenk-DS/AGI_Develop.git

cd AGI_Develop

uv sync

uv run pytest
```

Create a branch:

```bash
git checkout -b feature/my-feature
```

Make your changes, test them, and open a pull request.

---

# 🐛 Reporting Issues

When reporting an issue, include:

```text
Operating System
Python Version
GPU
CUDA Version
Ollama Version
Model Name
Qdrant Version
Error Message
Relevant Logs
Steps to Reproduce
```

This makes debugging significantly easier.

---

# 📄 License

See the repository for the applicable license information.

---

# 👨‍💻 Author

## Naveen K

AI / ML & GenAI Engineer

Focused on:

```text
Artificial Intelligence
Machine Learning
Generative AI
LLMs
RAG
AI Agents
Model Optimization
Computer Vision
NLP
FastAPI
Local AI
AI Automation
```

GitHub:

**https://github.com/naveenk-DS**

Project:

**https://github.com/naveenk-DS/AGI_Develop**

---

# ⭐ If You Find This Project Interesting

If NAVIX is useful for learning, experimentation, or AI engineering research, consider:

* ⭐ Starring the repository
* 🐛 Opening an issue
* 💡 Suggesting improvements
* 🔧 Contributing code
* 📚 Sharing ideas around local-first AI systems

---

## 🚀 NAVIX

> **From local LLM inference to voice, memory, RAG, agents, and computer automation — one AI operating system.**
