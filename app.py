import subprocess
import os
from flask import Flask, request, Response

app = Flask(__name__)


@app.route("/", methods=["GET"])
def fetch_url():
    url = request.args.get("url")
    if not url:
        return Response("Missing 'url' parameter", status=400, mimetype='text/plain')

    # 使用 curl_chrome110 執行抓取
    cmd = ["curl_chrome110", url]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            # 成功，回傳 HTML 內容
            return Response(result.stdout, status=200, mimetype='text/html')
        else:
            # 失敗，回傳錯誤訊息
            error_msg = f"Error fetching URL: {result.stderr}"
            return Response(error_msg, status=500, mimetype='text/plain')
    except subprocess.TimeoutExpired:
        return Response("Timeout fetching URL", status=504, mimetype='text/plain')
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500, mimetype='text/plain')


if __name__ == "__main__":
    print("Starting Flask app...")
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
