import json
import logging
import ssl
import os
import time
import threading
from urllib.request import urlopen, Request
from flask import Flask, jsonify

# ===== Logging =====
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ===== Config =====
HOST = "0.0.0.0"
POLL_INTERVAL = 3   # gọi API mỗi 3 giây
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

last_sid = None


def get_tai_xiu(d1, d2, d3):
    total = d1 + d2 + d3
    return ("Xỉu" if total <= 10 else "Tài"), total


def poll_api():
    """Luôn chạy nền để fetch phiên mới nhất"""
    global latest_result, last_sid
    while True:
        try:
            req = Request(API_URL, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json,text/plain,*/*"
            })
            with urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            if data.get("status") == "OK" and isinstance(data.get("data"), list):
                # lấy phiên có sid lớn nhất
                games = [g for g in data["data"] if g.get("cmd") == 7006 and g.get("sid")]
                if games:
                    game = max(games, key=lambda g: g["sid"])  # phiên mới nhất
                    sid = game.get("sid")
                    d1, d2, d3 = game.get("d1"), game.get("d2"), game.get("d3")

                    if sid != last_sid:
                        # nếu sang phiên mới → update luôn (dù dice chưa có)
                        last_sid = sid
                        latest_result = {
                            "Phien": sid,
                            "Xuc_xac_1": d1 or 0,
                            "Xuc_xac_2": d2 or 0,
                            "Xuc_xac_3": d3 or 0,
                            "Tong": (d1 + d2 + d3) if None not in (d1, d2, d3) else 0,
                            "Ket_qua": get_tai_xiu(d1, d2, d3)[0] if None not in (d1, d2, d3) else "Đang chờ",
                            "id": "cskhtoollxk"
                        }
                        logger.info(f"[TX] Sang phiên mới: {sid}")

                    else:
                        # cùng phiên cũ nhưng dice đã ra → update lại
                        if None not in (d1, d2, d3):
                            ket_qua, total = get_tai_xiu(d1, d2, d3)
                            latest_result = {
                                "Phien": sid,
                                "Xuc_xac_1": d1,
                                "Xuc_xac_2": d2,
                                "Xuc_xac_3": d3,
                                "Tong": total,
                                "Ket_qua": ket_qua,
                                "id": "cskhtoollxk"
                            }
                            logger.info(f"[TX] Phiên {sid} đủ dice: {ket_qua}")

        except Exception as e:
            logger.error(f"Lỗi khi fetch API: {e}")

        time.sleep(POLL_INTERVAL)


@app.route("/api/taixiu", methods=["GET"])
def api_taixiu():
    return jsonify(latest_result)


if __name__ == "__main__":
    logger.info("Khởi động API server...")
    threading.Thread(target=poll_api, daemon=True).start()
    port = int(os.environ.get("PORT", 8000))
    app.run(host=HOST, port=port)
