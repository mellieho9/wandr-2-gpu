import logging
import uuid
from flask import Blueprint, request, jsonify

from services.processing_pipeline import ProcessingPipeline
from utils.job_store import JobStore

logger = logging.getLogger(__name__)
processing_bp = Blueprint("processing", __name__)

# Initialize services
job_store = JobStore()
pipeline = ProcessingPipeline(job_store)


@processing_bp.route("/process", methods=["POST"])
def process_video():
    """
    Submit video processing job

    Request body:
    {
        "url": "https://tiktok.com/...",
        "schema": {
            "title": "string",
            "summary": "string",
            "tags": "array"
        },
        "prompt": "Extract cooking recipe details..."
    }
    """
    data = request.json

    if not data or "url" not in data:
        logger.warning("Process request received without URL")
        return jsonify({"error": "Missing video URL"}), 400

    job_id = str(uuid.uuid4())
    logger.info(f"New job created: {job_id} for URL: {data['url']}")

    # Store job
    job_store.create_job(
        job_id,
        {
            "url": data["url"],
            "schema": data.get("schema", {}),
            "prompt": data.get("prompt", ""),
            "status": "queued",
        },
    )

    # Process asynchronously
    pipeline.process_async(
        job_id, data["url"], data.get("schema", {}), data.get("prompt", "")
    )

    return jsonify(
        {"job_id": job_id, "status": "queued", "message": "Video processing started"}
    ), 202


@processing_bp.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    """Get job status"""
    job = job_store.get_job(job_id)

    if not job:
        logger.warning(f"Status request for unknown job: {job_id}")
        return jsonify({"error": "Job not found"}), 404

    logger.debug(f"Status request for job {job_id}: {job['status']}")

    return jsonify(
        {
            "job_id": job_id,
            "status": job["status"],
            "progress": job.get("progress", {}),
            "error": job.get("error"),
        }
    )


@processing_bp.route("/result/<job_id>", methods=["GET"])
def get_result(job_id):
    """Get processed result"""
    job = job_store.get_job(job_id)

    if not job:
        logger.warning(f"Result request for unknown job: {job_id}")
        return jsonify({"error": "Job not found"}), 404

    if job["status"] != "completed":
        logger.debug(f"Result request for incomplete job {job_id}: {job['status']}")
        return jsonify({"error": "Job not completed", "status": job["status"]}), 400

    logger.info(f"Returning result for job {job_id}")

    return jsonify(
        {"job_id": job_id, "status": "completed", "result": job.get("result", {})}
    )
