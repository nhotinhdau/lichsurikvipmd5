import json
import logging
import ssl
import os
from urllib.request import urlopen, Request
from flask import Flask, jsonify
import threading
import time

# ===== Logging =====
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ===== Config =====
HOST = "0.0.0.0"
POLL_INTERVAL = 5   # 5 giây kiểm tra phiên mới
ssl._create_default_https_context = ssl._create_unverified_context
API_URL = "https://jakpotgwab.geightdors.net/glms/v1/notify/taixiu?platform_id=rik&gid=vgmn_101"

app = Flask(__name__)

# ===== Biến cache =====
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


def fetch_and_update():
    """Gọi API gốc và cập nhật cache nếu có phiên mới"""
    global last_sid, latest_result
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
            for game in reversed(data["data"]):  # lấy phiên mới nhất
                if game.get("cmd") == 7006:
                    sid = game.get("sid")
                    d1, d2, d3 = game.get("d1"), game.get("d2"), game.get("d3")
                    if sid and None not in (d1, d2, d3):
                        if sid != last_sid:  # chỉ update khi có phiên mới
                            last_sid = sid
                            ket_qua, total = get_tai_xiu(d1, d2, d3)
                            latest_result = {
                                "Phien": sid,
                                "Xuc_xac_1": d1,
                                "Xuc_xac_2": d2,
                                "Xuc_xac_3": d3,
                                "Tong": total,
                                "Ket_qua": ket_qua,
                                "id": "djtuancon"
                            }
                            logger.info(f"[TX] Cập nhật phiên {sid} - Tổng: {total}, KQ: {ket_qua}")
                        return  # nếu đã xử lý thì dừng
    except Exception as e:
        logger.error(f"Lỗi khi fetch API: {e}")


def poll_api():
    """Luôn chạy nền để check phiên mới"""
    while True:
        fetch_and_update()
        time.sleep(POLL_INTERVAL)


@app.route("/api/taixiu", methods=["GET"])
def api_taixiu():
    return jsonify(latest_result)


if __name__ == "__main__":
    logger.info("Khởi động API Tài Xỉu (cache + update khi có phiên mới)...")
    threading.Thread(target=poll_api, daemon=True).start()
    port = int(os.environ.get("PORT", 8000))
    app.run(host=HOST, port=port)
