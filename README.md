# 📝 Meeting Report Generation Solution 

![Python](https://img.shields.io/badge/Python-3.11-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-Production-green) ![Docker](https://img.shields.io/badge/Docker-Compose-blue) ![Celery](https://img.shields.io/badge/Celery-Async-orange) ![Redis](https://img.shields.io/badge/Redis-Cache-red)

A full-stack solution for generating **structured meeting reports** from audio recordings using **FastAPI**, **Celery**, **Redis**, and **LLMs**.

---

## 🚀 Features

- ⚡ **Asynchronous & scalable** task handling  
- 🗣️ **Parallel transcription & diarization**  
- 📝 **Structured conversation & summary generation**  
- 📄 **Automated PDF report export**  
- 🌐 **Distributed architecture** powered by Redis  
- 🤖 **LLM-powered summarization** with Ollama  
- 📊 **Real-time monitoring** via Flower  

---

## 🏗️ Architecture Overview

### 1️⃣ FastAPI Endpoint
- Accepts audio uploads and validates formats  
- Submits tasks to **Celery** for asynchronous processing  
- Provides endpoints to:
  - Check task status
  - Retrieve results
  - Export reports (PDF/Markdown)  

### 2️⃣ Celery Workers
Processes audio in **three phases**:

1. **Transcription** – Converts speech to text  
2. **Diarization** – Identifies speakers and segments audio  
3. **Conversation Mapping** – Merges transcription & speaker info into structured multi-turn conversations  

### 3️⃣ Summarization Agent
- Uses **Ollama LLM** to generate:
  - 📝 Concise summary  
  - ✅ Actions to take  
  - 🎯 Decisions made  
  - 📌 Topics discussed  

### 4️⃣ Report Generation
- Automatically produces a **PDF report** from structured summary for end users  


## 📊 Workflow

<img src="images/workflow.png" alt="Workflow Diagram" style="border:2px solid black;" width="600"/>

---

## 💻 Tech Stack

![FastAPI](https://img.shields.io/badge/FastAPI-HTTP_API-green) ![Celery](https://img.shields.io/badge/Celery-Tasks-orange) ![Redis](https://img.shields.io/badge/Redis-Cache-red) ![Ollama](https://img.shields.io/badge/Ollama-LLM-purple) ![Pyannote](https://img.shields.io/badge/Pyannote-Diarization-blue) ![Librosa](https://img.shields.io/badge/Librosa-Audio-yellow)

---

## 📂 Project Structure

```
.
├── alembic/                 # Database migrations
├── app/                     # Main application package
│   ├── api/                 # API endpoints
        ├── summarize.py          # summarization endpoint
        └── ..
│   ├── core/                # Core functionality (config, security)
│   ├── db/                  # Database session and base
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
        ├── langchain.py          # langchain pydantic schemas
        └── ..
│   ├── services/            # Business logic
        ├── transcribe/           # transcription task
│       ├── diarize/              # diarization task
│       ├── conversation/         # conversation creation task
│       ├── summarize/            # summarization task
│       ├── cache.py              # cache store logic
│       ├── celery_worker.py      # celery worker logic
│       └── ..
│   └── utils/               # Utility functions
├── docker-compose.yml       # Docker Compose for production
├── docker-compose.dev.yml   # Docker Compose for development
├── Dockerfile               # Docker configuration for app
├── celery.dockerfile        # Docker configuration for celery worker
├── alambic.ini              # Alembic configuration
├── main.py                  # Application entry point
├── pyproject.toml           # Project dependencies and metadata
├── start.sh                 # Production startup script
└── start-dev.sh             # Development startup script
```

## How to Run

1. Start the services using Docker Compose:
```bash
docker-compose up --build
```
2. To run integration tests:
```bash
pytest -v 
```

## API Documentation

Once the application is running, you can access:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔑 API Endpoints

### Summarization

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/summarize/query` | Upload audio file for summarization |
| GET    | `/summarize/get_result` | Check task status |
| GET    | `/summarize/export/pdf` | Export result as PDF |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/health` | Health check endpoint |

---

## ⚙️ Configuration

Configure the application via environment variables (e.g., in a `.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `HF_TOKEN` | JWT secret key | `supersecretkey` |
| `DIARIZATION_MODEL` | Diarization model | `pyannote/speaker-diarization-3.1` |
| `WHISPER_SIZE` | Whisper model size | `small` |
| `SAMPLE_RATE` | Audio sample rate | `16000` |
| `MODEL_NAME` | LLM model name | `qwen3:1.7b` |
| `OLLAMA_URL` | Ollama service URL | `http://ollama:11434` |
| `REDIS_HOST` | Redis host | `redis` |
| `REDIS_PORT` | Redis port | `6379` |
| `REDIS_CACHE_DB` | Redis cache DB index | `0` |
| `REDIS_BROKER_DB` | Redis broker DB index | `1` |
| `OUTPUT_FOLDER` | Folder to store generated PDFs | `./output` |


---

### 📝 Ending Note

This solution is designed to be **production-ready, modular, and scalable**, with clear separation between API, services, and background tasks. It demonstrates end-to-end processing of meeting audio files—from **upload** to **structured summary** to **PDF report export**—making it a strong showcase of full-stack AI engineering skills for real-world applications.

