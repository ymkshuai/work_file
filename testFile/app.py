import os
from datetime import datetime

from flask import Flask, request, jsonify

app = Flask(__name__)

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "request_log.txt")


def save_request_info():
    """将请求信息追加写入 txt 文件"""
    lines = []
    lines.append("=" * 60)
    lines.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"方法: {request.method}")
    lines.append(f"路径: {request.path}")
    lines.append(f"URL: {request.url}")
    lines.append(f"来源IP: {request.remote_addr}")
    lines.append(f"Headers:")
    for k, v in request.headers.items():
        lines.append(f"  {k}: {v}")
    lines.append(f"Query参数 (args):")
    for k, v in request.args.items():
        lines.append(f"  {k}: {v}")
    lines.append(f"表单参数 (form):")
    for k, v in request.form.items():
        lines.append(f"  {k}: {v}")
    lines.append(f"请求体 (raw data):")
    raw = request.get_data(as_text=True)
    lines.append(f"  {raw if raw else '(空)'}")
    lines.append(f"JSON体:")
    try:
        json_data = request.get_json(silent=True)
        lines.append(f"  {json_data if json_data else '(无)'}")
    except Exception:
        lines.append("  (解析失败)")
    lines.append(f"Cookies:")
    for k, v in request.cookies.items():
        lines.append(f"  {k}: {v}")
    lines.append("=" * 60)
    lines.append("")

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
            f.flush()
    except Exception as e:
        print(f"写入文件失败: {e}")


@app.route("/", methods=["GET", "POST"])
@app.route("/<path:subpath>", methods=["GET", "POST"])
def handle_request(subpath=""):
    save_request_info()
    return jsonify({
        "code": 200,
        "message": "请求已记录",
        "method": request.method,
        "path": request.path,
    })


if __name__ == "__main__":
    print(f"日志文件位置: {LOG_FILE}")
    app.run(host="0.0.0.0", port=10003, debug=True)
