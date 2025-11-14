# Product Overview

Wandr GPU is a lean, GPU-accelerated video processing service built for the Google Cloud Run NVIDIA L4 challenge. It processes social media videos (TikTok, Instagram Reels) through a GPU-powered pipeline to extract transcriptions and on-screen text.

## Core Workflow

1. Client submits video URL with schema via POST request
2. Service downloads video and assigns job ID
3. GPU-accelerated Whisper transcribes audio
4. GPU-accelerated frame extraction + Google Vision OCR extracts on-screen text
5. Gemini AI (via Google ADK) generates structured summary matching schema
6. Client polls for status and retrieves results

## Key Features

- **GPU-Accelerated Transcription**: Local Whisper model on NVIDIA L4 (no API costs)
- **Fast Frame Processing**: Parallel GPU operations for video frame extraction
- **AI-Powered Summarization**: Gemini AI generates structured data matching custom schemas
- **Multi-Platform Support**: TikTok and Instagram Reels
- **Async Job Processing**: Non-blocking API with job status tracking
- **Scalable Architecture**: Cloud Run with auto-scaling

## API Endpoints

### POST /process

Submit video processing job

**Request:**

```json
{
  "url": "https://tiktok.com/...",
  "schema": {},
  "prompt": ""
}
```

**Response:**

```json
{
  "job_id": "uuid",
  "status": "queued",
  "message": "Video processing started"
}
```

### GET /status/{job_id}

Check job processing status

**Response:**

```json
{
  "job_id": "uuid",
  "status": "summarizing",
  "progress": { "step": 4, "total": 4 }
}
```

### GET /result/{job_id}

Retrieve processed content (when status is "completed")

**Response:**

```json
{
  "job_id": "uuid",
  "status": "completed",
  "result": {
    "transcription": "Full audio transcription...",
    "ocr_text": "Extracted on-screen text...",
    "description": "Original video description from platform",
    "structured_data": {
      "title": "...",
      "tags": ["..."],
      "summary": "..."
    }
  }
}
```

### GET /health

Health check and GPU availability

**Response:**

```json
{
  "status": "healthy",
  "gpu_available": true,
  "service": "wandr-gpu"
}
```

## Performance Targets

With NVIDIA L4:

- Whisper transcription: ~10x faster than CPU
- Batch frame processing: ~20x faster
- End-to-end: 1-2 minutes per video vs 8-10 minutes on CPU

## Use Cases

- Content creators extracting and organizing video content
- Social media monitoring with structured data extraction
- Accessibility (adding captions to videos)
- Content moderation pipelines with AI-powered categorization
- Video search and indexing with custom metadata schemas
- Automated knowledge base creation from video content
