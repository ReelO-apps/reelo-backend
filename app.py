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
@app.route('/extract-identity', methods=['POST'])
def extract_identity():
    if "images" not in request.files:
        return jsonify({"error": "images field is required"}), 400

    files = request.files.getlist("images")
    if len(files) == 0:
        return jsonify({"error": "at least one image is required"}), 400

    # TODO: Replace with real embedding model
    embedding_dim = 512
    dummy_embedding = [0.0] * embedding_dim

    return jsonify({
        "embedding": dummy_embedding,
        "dimensions": embedding_dim
    })


@app.route('/generate-teaser', methods=['POST'])
def generate_teaser():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "JSON body required"}), 400

    required = ["storyId", "chapterId", "choiceId", "sceneSpec", "shotSequence"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # TODO: Replace with real video generation + stitching
    import uuid
    fake_id = str(uuid.uuid4())
    fake_url = f"https://example.com/videos/{fake_id}.mp4"

    shots_used = len(data["shotSequence"].get("shots", []))
    duration = data["shotSequence"].get("totalDurationSeconds", 0)

    return jsonify({
        "videoUrl": fake_url,
        "durationSeconds": duration,
        "shotsUsed": shots_used,
        "identityLocked": bool(data["sceneSpec"].get("identityToken"))
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
