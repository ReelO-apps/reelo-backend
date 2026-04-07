from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/upload', methods=['POST'])
def upload_script():
    data = request.json
    script_text = data.get('script', '')
    return jsonify({"job_id": "job_123", "status": "queued"}), 200

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
