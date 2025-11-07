# Technology Stack

## Core Framework

### Backend

- **Runtime**: Python 3.11
- **Web Framework**: Flask with Gunicorn WSGI server
- **Deployment**: Google Cloud Run with NVIDIA L4 GPU
- **Job Storage**: In-memory dict (local) or Redis (production)

### GPU Acceleration

- **CUDA**: 12.1 with cuDNN 8
- **PyTorch**: 2.1.0 with CUDA support
- **Whisper**: faster-whisper (GPU-optimized Whisper implementation)

## Key Libraries

### Video Processing

- `yt-dlp` - Video downloader for TikTok and Instagram
- `opencv-python-headless` - Video frame extraction (GPU-accelerated)
- `ffmpeg-python` - Audio extraction from video

### Machine Learning

- `torch` - PyTorch for GPU operations
- `torchaudio` - Audio processing utilities
- `faster-whisper` - GPU-accelerated Whisper transcription

### OCR

- `google-cloud-vision` - Google Vision API for text detection

### Web & Utilities

- `Flask` - Web framework
- `gunicorn` - Production WSGI server
- `redis` - Redis client for job storage (production)
- `python-dotenv` - Environment configuration

## System Dependencies

- `ffmpeg` - Audio/video processing
- `CUDA 12.1` - GPU runtime
- `cuDNN 8` - Deep learning GPU acceleration

## Environment Configuration

Required environment variables in `.env`:

```bash
# Flask
PORT=8080
FLASK_ENV=production

# GPU Models
WHISPER_MODEL=base  # Options: tiny, base, small, medium, large

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Redis (optional, for production)
REDIS_HOST=
REDIS_PORT=6379

# Logging
LOG_LEVEL=INFO
```

## Docker Configuration

### Base Image

`nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04`

### GPU Resources

- **GPU Type**: nvidia-l4
- **GPU Count**: 1
- **Memory**: 16Gi
- **CPU**: 4 cores
- **Timeout**: 600 seconds

### Container Configuration

```yaml
resources:
  limits:
    memory: 16Gi
    cpu: "4"
    nvidia.com/gpu: "1"
```

## Common Commands

### Local Development

```bash
# Setup virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Flask development server
python app.py

# Test GPU availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Deployment

```bash
# Build Docker image
gcloud builds submit --tag gcr.io/$PROJECT_ID/wandr-gpu

# Deploy to Cloud Run with GPU
gcloud run deploy wandr-gpu \
  --image gcr.io/$PROJECT_ID/wandr-gpu \
  --region us-central1 \
  --gpu 1 \
  --gpu-type nvidia-l4 \
  --memory 16Gi \
  --cpu 4 \
  --timeout 600 \
  --allow-unauthenticated

# View logs
gcloud run logs read wandr-gpu --region=us-central1

# Check service status
gcloud run services describe wandr-gpu --region=us-central1
```

### Testing

```bash
# Health check
curl http://localhost:8080/health

# Submit job
curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -d '{"url": "https://tiktok.com/..."}'

# Check status
curl http://localhost:8080/status/{job_id}

# Get result
curl http://localhost:8080/result/{job_id}
```

## GPU Optimization

### Whisper Model Selection

Trade-off between speed and accuracy:

- `tiny` - Fastest, lowest accuracy (~32x realtime on L4)
- `base` - Good balance (~16x realtime on L4) **[Default]**
- `small` - Better accuracy (~8x realtime on L4)
- `medium` - High accuracy (~4x realtime on L4)
- `large` - Best accuracy (~2x realtime on L4)

### Frame Sampling

OCR extracts 1 frame every 30 frames by default. Adjust in `ocr_service.py`:

```python
ocr_text = self.ocr.extract_text(video_path, sample_rate=30)
```

Lower sample_rate = more frames = slower but more text captured

### Memory Management

- Models loaded once at service startup (cached in memory)
- Temporary video files cleaned up after processing
- GPU memory automatically managed by PyTorch

## Performance Benchmarks

### NVIDIA L4 vs CPU

| Operation        | CPU Time | L4 GPU Time | Speedup |
| ---------------- | -------- | ----------- | ------- |
| Whisper (base)   | 120s     | 12s         | 10x     |
| Frame extraction | 40s      | 2s          | 20x     |
| End-to-end       | 8-10 min | 1-2 min     | 5-8x    |

### Cost Comparison

- **API-based** (Whisper API): $0.006/min of audio
- **GPU-based** (L4 on Cloud Run): ~$0.50/hour (includes idle time)
- **Break-even**: ~8 hours of audio per hour of runtime

For high-volume processing, GPU is significantly cheaper.
