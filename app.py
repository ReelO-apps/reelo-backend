import os
import uuid
import time
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Legacy job store (used by /upload and /status/<job_id>)
jobs = {}

# Story store (used by /api/stories/* routes)
stories = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utcnow_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Existing / legacy endpoints
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# New story-management endpoints (Flutter client API)
# ---------------------------------------------------------------------------

@app.route('/api/stories/upload-script', methods=['POST'])
def api_upload_script():
    """
    Accept a script via JSON body {"script": "..."} or multipart file upload.
    Creates a story record and returns its metadata.
    """
    try:
        script_text = None

        # Prefer JSON body
        if request.is_json:
            data = request.get_json(silent=True) or {}
            script_text = data.get("script")

        # Fall back to multipart file upload
        if script_text is None and "script" in request.files:
            script_file = request.files["script"]
            script_text = script_file.read().decode("utf-8")

        # Fall back to plain form field
        if script_text is None and request.form.get("script"):
            script_text = request.form.get("script")

        if not script_text or not script_text.strip():
            return jsonify({"error": "No script provided"}), 400

        story_id = str(uuid.uuid4())
        now = _utcnow_iso()
        word_count = len(script_text.split())

        stories[story_id] = {
            "story_id": story_id,
            "script": script_text,
            "word_count": word_count,
            "chapters": [],
            "status": "uploaded",
            "created_at": now,
            "updated_at": now,
        }

        return jsonify({
            "story_id": story_id,
            "status": "uploaded",
            "word_count": word_count,
            "created_at": now,
        }), 201

    except Exception as exc:
        return jsonify({"error": f"Internal server error: {str(exc)}"}), 500


@app.route('/api/stories/<story_id>/generate-chapters', methods=['POST'])
def api_generate_chapters(story_id):
    """
    Trigger chapter generation for an existing story.
    Returns a job_id that can be used to poll progress.
    """
    story = stories.get(story_id)
    if not story:
        return jsonify({"error": "Story not found"}), 404

    if story["status"] == "processing":
        return jsonify({"error": "Story is already being processed"}), 400

    job_id = str(uuid.uuid4())
    now = _utcnow_iso()

    # Update story status
    story["status"] = "processing"
    story["updated_at"] = now

    # Record a job entry so /status/<job_id> also works
    jobs[job_id] = {
        "id": job_id,
        "story_id": story_id,
        "status": "processing",
        "progress": 0,
        "created_at": time.time(),
        "result_url": None,
    }

    # TODO: Dispatch to RunPod or background worker here

    return jsonify({
        "story_id": story_id,
        "job_id": job_id,
        "status": "processing",
        "progress": 0,
    }), 202


@app.route('/api/stories/<story_id>', methods=['GET'])
def api_get_story(story_id):
    """
    Return the full story object including script, metadata, and chapters.
    """
    story = stories.get(story_id)
    if not story:
        return jsonify({"error": "Story not found"}), 404

    return jsonify(story), 200


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

