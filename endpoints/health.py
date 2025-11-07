from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    from services.processing_pipeline import ProcessingPipeline
    
    pipeline = ProcessingPipeline()
    
    return jsonify({
        'status': 'healthy',
        'gpu_available': pipeline.gpu_available(),
        'service': 'wandr-gpu'
    })
