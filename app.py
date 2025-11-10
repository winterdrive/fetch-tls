import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def fetch_url():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing url parameter"}), 400

    # 使用 curl_chrome110 執行抓取
    cmd = ["curl_chrome110", url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return jsonify({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout fetching URL"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500
