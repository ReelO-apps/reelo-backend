import os
import uuid
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

jobs = {}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/upload', methods=['POST'])
def upload_script():
    data = request.get_json()
    if not data or 'script' not in data:
        return jsonify({"error": "No script provided"}), 400

    script_text = data['script']
    word_count = len(script_text.split())
    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "id": job_id,
        "status": "queued",
        "word_count": word_count,
        "created_at": time.time(),
        "result_url": None
    }

    return jsonify({"job_id": job_id, "word_count": word_count, "status": "queued"}), 201

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
