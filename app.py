import os
import subprocess
import socket
import ipaddress
from urllib.parse import urlparse

from flask import Flask, request, jsonify, abort
from flask_talisman import Talisman

app = Flask(__name__)

# -------------------------
# Content-Security-Policy (嚴格、最小權限)
# 我們使用 flask-talisman 明確宣告 CSP 指令，避免檢測工具判定為 Missing/Permissive CSP
CSP = {
    # 預設拒絕所有來源（white-list 原則）
    'default-src': ["'none'"],
    # 若未做 HTML 回傳，script-src 設為 'none'；避免 inline script
    'script-src': ["'none'"],
    # 只允許從自身載入樣式（若你的 UI 需要外部 style，請在此擴充）
    'style-src': ["'self'"],
    # 圖片僅允許 self 與 data: (data: 用於 inline small images)
    'img-src': ["'self'", "data:"],
    # 連線來源（fetch/XHR/websocket）預設封鎖；若 API 需跨域連線再調整
    'connect-src': ["'none'"],
    # 阻止嵌入本站 (frame-ancestors)
    'frame-ancestors': ["'none'"],
    # 不允許 <object>、<embed>
    'object-src': ["'none'"],
    # base-uri 最小化攻擊面
    'base-uri': ["'none'"],
    # form-action 限制
    'form-action': ["'none'"],
}

# 強制 HTTPS 與 HSTS 設定：Talisman 會在 HTTPS 時自動送出 Strict-Transport-Security header
talisman = Talisman(
    app,
    content_security_policy=CSP,
    force_https=False,  # 如果你部署在可控制 HTTPS 的環境，可改為 True；False 可避免本地開發導致自動 redirect
    strict_transport_security=True,
    strict_transport_security_max_age=63072000,  # 2 years
    strict_transport_security_include_subdomains=True,
    strict_transport_security_preload=False
)

# 額外安全 header（Talisman 已處理大部分，但保留這些明確 header 以對掃描器友好）
@app.after_request
def harden_headers(response):
    # X-Content-Type-Options 防止瀏覽器 MIME-sniffing
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    # X-Frame-Options 防止 clickjacking (若 Talisman沒有設定，再設定一次)
    response.headers.setdefault("X-Frame-Options", "DENY")
    # Referrer-Policy 減少敏感資訊外洩
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    # Permissions-Policy (舊稱 Feature-Policy) — 最小權限
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=()")
    return response

# -------------------------
# 輔助：驗證 URL 並防止 SSRF（解析 hostname 並檢查 IP 是否落在私有/保留範圍）
def is_valid_url_and_not_internal(url: str) -> (bool, str):
    """
    檢查 URL 的基本格式，並解析 hostname -> IP，拒絕內網/loopback/private addresses。
    回傳 (True, normalized_url) 或 (False, reason)
    """
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"URL parse error: {e}"

    if parsed.scheme not in ("http", "https"):
        return False, "URL scheme must be http or https"

    if not parsed.hostname:
        return False, "URL missing hostname"

    hostname = parsed.hostname

    # 簡單防護：host 不該包含 suspicious characters
    if any(c.isspace() for c in hostname):
        return False, "Invalid hostname"

    # 使用 getaddrinfo 解析所有 IP，檢查是否有私有/loopback/link-local 等
    try:
        addrs = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False, "Hostname resolution failed"

    for addr in addrs:
        ip_str = addr[4][0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            return False, f"Unparseable IP: {ip_str}"

        # 如果解析到私有或 loopback 或 link-local 或 multicast 或 unspecified，拒絕
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_unspecified:
            return False, f"Resolved IP {ip_str} is private/loopback/link-local/multicast/unspecified"

    # 若一切通過，回傳 normalized URL（保留原始）
    return True, parsed.geturl()


@app.route("/", methods=["POST"])
def fetch_url():
    # API 規格：JSON body 包含 url；維持 jsonify 回傳
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON with {\"url\": \"https://...\"}"}), 400

    url = request.json.get("url")
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    # 驗證 URL 並阻止 SSRF / 私有網段存取
    ok, detail = is_valid_url_and_not_internal(url)
    if not ok:
        return jsonify({"error": "Invalid or disallowed URL", "reason": detail}), 400

    # 按你的限制，**保留**使用 subprocess.run([...]) 的呼叫方式（不使用 shell=True）
    cmd = ["curl_chrome110", url]

    try:
        # capture_output=True, text=True, timeout：限制外部命令執行時間，避免被利用做 DoS
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # 將 stdout/stderr/returncode 以 JSON 回傳（保持 API 規格）
        payload = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

        # HTTP status code: 200 無論 returncode（若你希望非 0 時回 500 可改），但為了明確區分我們採用 200 + JSON returncode
        return jsonify(payload), 200

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout fetching URL"}), 504
    except Exception as e:
        # 保留 exception message（必要時可隱藏敏感資訊）
        return jsonify({"error": "Internal error", "detail": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # 在開發階段你可能會用 debug，但生產環境應該關閉 debug
    app.run(host="0.0.0.0", port=port, debug=False)
