# Project Structure

## Directory Layout

```
wandr-gpu/
├── app.py                      # Flask app entry point - registers blueprints
├── endpoints/                  # Flask Blueprint endpoints (route handlers)
│   ├── __init__.py
│   ├── health.py               # Health check endpoint
│   └── processing.py           # Video processing endpoints (process, status, result)
├── services/                   # GPU-accelerated business logic
│   ├── __init__.py
│   ├── video_downloader.py     # Download videos from TikTok/Instagram (yt-dlp)
│   ├── whisper_gpu.py          # Local Whisper model with GPU acceleration
│   ├── ocr_service.py          # GPU frame extraction + Google Vision OCR
│   └── processing_pipeline.py # Orchestrates full processing workflow
├── utils/
│   ├── __init__.py
│   └── job_store.py            # In-memory or Redis-backed job storage
├── Dockerfile                  # NVIDIA CUDA base image
├── requirements.txt            # GPU-enabled Python dependencies
├── cloud-run-config.yaml       # L4 GPU Cloud Run configuration
├── .env.example                # Environment variable template
├── .gitignore
└── .kiro/
    └── steering/               # Project documentation
        ├── product.md
        ├── structure.md
        └── tech.md
```

## Architecture Patterns

### Blueprint Pattern

Flask endpoints are organized into Blueprints for modularity:

- `health_bp`: Health check endpoint (`/health`)
- `processing_bp`: Video processing endpoints (`/process`, `/status/<job_id>`, `/result/<job_id>`)

Each blueprint is registered in `app.py`.

### Service Layer Pattern

Business logic is encapsulated in service classes with clear interfaces:

- **VideoDownloader**: Downloads videos using yt-dlp
- **WhisperGPU**: GPU-accelerated audio transcription
- **OCRService**: GPU frame extraction + Google Vision text detection
- **ProcessingPipeline**: Orchestrates the full workflow

### Async Job Processing

- API endpoints return immediately with job ID
- Processing happens in background threads
- Job status stored in JobStore (in-memory or Redis)
- Clients poll `/status/{job_id}` for updates

## Pipeline Flow

```
1. Download (yt-dlp)
   ↓
2. Transcribe (Whisper GPU)
   ↓
3. Extract Text (OpenCV GPU + Google Vision)
   ↓
4. Return Results
   ↓
5. Cleanup (remove temp files)
```

Each stage updates job status: `queued` → `downloading` → `transcribing` → `extracting_text` → `completed` or `failed`

## Key Conventions

- **Error Handling**: Pipeline catches exceptions and updates job status to 'failed' with error message
- **Temporary Files**: Videos stored in `/tmp/videos` with job_id as filename, cleaned up after processing
- **GPU Detection**: All services check `torch.cuda.is_available()` and fallback to CPU if needed
- **Job Storage**: In-memory dict for local dev, Redis for production multi-instance deployments
- **Logging**: Print statements for now (can be upgraded to structured logging)

## Development Workflow

### Local Development

```bash
# Setup
cd wandr-gpu
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run (requires CUDA GPU)
python app.py

# Test
curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -d '{"url": "https://tiktok.com/..."}'
```

### Deployment

```bash
# Build with NVIDIA CUDA base
gcloud builds submit --tag gcr.io/$PROJECT_ID/wandr-gpu

# Deploy with L4 GPU
gcloud run deploy wandr-gpu \
  --image gcr.io/$PROJECT_ID/wandr-gpu \
  --region us-central1 \
  --gpu 1 \
  --gpu-type nvidia-l4 \
  --memory 16Gi \
  --cpu 4 \
  --timeout 600 \
  --allow-unauthenticated
```
