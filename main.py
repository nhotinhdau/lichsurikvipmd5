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

# Cache phiên mới nhất
latest_result = {
    "Phien": 0,
    "Xuc_xac_1": 0,
    "Xuc_xac_2": 0,
    "Xuc_xac_3": 0,
    "Tong": 0,
    "Ket_qua": "Chưa có",
    "id": "cskhtoollxk"
}


def get_tai_xiu(d1, d2, d3):
    total = d1 + d2 + d3
    return ("Xỉu" if total <= 10 else "Tài"), total


def fetch_latest():
    """Lấy phiên mới nhất từ API gốc và update cache nếu có"""
    global latest_result
    try:
        req = Request(API_URL, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*"
        })
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("status") == "OK" and isinstance(data.get("data"), list):
            game = data["data"][-1]  # lấy phiên mới nhất

            if game.get("cmd") == 7006:
                sid = game.get("sid")
                d1, d2, d3 = game.get("d1"), game.get("d2"), game.get("d3")

                if sid:
                    if None not in (d1, d2, d3):
                        ket_qua, total = get_tai_xiu(d1, d2, d3)
                    else:
                        ket_qua, total = "Đang chờ", 0

                    # chỉ update nếu là phiên mới
                    if sid != latest_result["Phien"]:
                        latest_result = {
                            "Phien": sid,
                            "Xuc_xac_1": d1 or 0,
                            "Xuc_xac_2": d2 or 0,
                            "Xuc_xac_3": d3 or 0,
                            "Tong": total,
                            "Ket_qua": ket_qua,
                            "id": "cskhtoollxk"
                        }
                        logger.info(f"Cập nhật phiên mới: {sid} - {ket_qua}")
    except Exception as e:
        logger.error(f"Lỗi khi fetch API: {e}")

    return latest_result  # luôn trả về cache (dù có lỗi hay không)


@app.route("/api/taixiu", methods=["GET"])
def api_taixiu():
    return jsonify(fetch_latest())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host=HOST, port=port)
