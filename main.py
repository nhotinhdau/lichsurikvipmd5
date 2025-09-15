import json
import logging
import ssl
import os
from urllib.request import urlopen, Request
from flask import Flask, jsonify

# ===== Logging =====
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ===== Config =====
HOST = "0.0.0.0"
ssl._create_default_https_context = ssl._create_unverified_context
API_URL = "https://jakpotgwab.geightdors.net/glms/v1/notify/taixiu?platform_id=rik&gid=vgmn_101"

app = Flask(__name__)


def fetch_latest():
    """Gọi API gốc và lấy phiên mới nhất"""
    try:
        req = Request(API_URL, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json,text/plain,*/*"
        })
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("status") == "OK" and isinstance(data.get("data"), list):
            # duyệt ngược để lấy phiên mới nhất
            for game in reversed(data["data"]):
                if game.get("cmd") == 7006:
                    sid = game.get("sid")
                    d1, d2, d3 = game.get("d1"), game.get("d2"), game.get("d3")
                    if sid and None not in (d1, d2, d3):
                        total = d1 + d2 + d3
                        ket_qua = "Xỉu" if total <= 10 else "Tài"
                        return {
                            "Phien": sid,
                            "Xuc_xac_1": d1,
                            "Xuc_xac_2": d2,
                            "Xuc_xac_3": d3,
                            "Tong": total,
                            "Ket_qua": ket_qua,
                            "id": "djtuancon"
                        }
    except Exception as e:
        logger.error(f"Lỗi khi fetch API: {e}")

    # fallback nếu không có kết quả hợp lệ
    return {
        "Phien": 0,
        "Xuc_xac_1": 0,
        "Xuc_xac_2": 0,
        "Xuc_xac_3": 0,
        "Tong": 0,
        "Ket_qua": "Chưa có",
        "id": "cskhtoollxk"
    }


@app.route("/api/taixiu", methods=["GET"])
def api_taixiu():
    result = fetch_latest()
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Server chạy trên port {port}")
    app.run(host=HOST, port=port)
