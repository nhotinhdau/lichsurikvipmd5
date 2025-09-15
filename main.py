import json
import threading
import time
import logging
import ssl
from urllib.request import urlopen, Request
from flask import Flask, jsonify
import os

# ===== Logging =====
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ===== Config =====
HOST = "0.0.0.0"
POLL_INTERVAL = 3   # gọi API mỗi 3 giây
RETRY_DELAY = 5

lock = threading.Lock()

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

# Bỏ verify SSL để tránh lỗi chứng chỉ
ssl._create_default_https_context = ssl._create_unverified_context


# ===== Helper =====
def get_tai_xiu(d1, d2, d3):
    total = d1 + d2 + d3
    return "Xỉu" if total <= 10 else "Tài"


def update_result(result):
    with lock:
        latest_result.clear()
        latest_result.update(result)


# ===== Poll API =====
def poll_api():
    global last_sid
    url = "https://jakpotgwab.geightdors.net/glms/v1/notify/taixiu?platform_id=rik&gid=vgmn_101"

    while True:
        try:
            req = Request(url, headers={"User-Agent": "Python-Proxy/1.0"})
            with urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            if data.get("status") == "OK" and isinstance(data.get("data"), list):
                for game in data["data"]:
                    if game.get("cmd") == 7006:
                        sid = game.get("sid")
                        d1, d2, d3 = game.get("d1"), game.get("d2"), game.get("d3")

                        # Nếu có phiên mới
                        if sid and sid != last_sid:
                            last_sid = sid
                            if None not in (d1, d2, d3):  # Có kết quả xúc xắc
                                total = d1 + d2 + d3
                                ket_qua = get_tai_xiu(d1, d2, d3)
                                result = {
                                    "Phien": sid,
                                    "Xuc_xac_1": d1,
                                    "Xuc_xac_2": d2,
                                    "Xuc_xac_3": d3,
                                    "Tong": total,
                                    "Ket_qua": ket_qua,
                                    "id": "cskhtoollxk"
                                }
                            else:  # Phiên mới nhưng chưa ra xúc xắc
                                result = {
                                    "Phien": sid,
                                    "Xuc_xac_1": 0,
                                    "Xuc_xac_2": 0,
                                    "Xuc_xac_3": 0,
                                    "Tong": 0,
                                    "Ket_qua": "Chưa có",
                                    "id": "cskhtoollxk"
                                }
                            update_result(result)
                            logger.info(f"[TX] Cập nhật phiên {sid}")

        except Exception as e:
            logger.error(f"Lỗi khi lấy dữ liệu API: {e}")
            time.sleep(RETRY_DELAY)

        time.sleep(POLL_INTERVAL)


# ===== Flask API =====
app = Flask(__name__)


@app.route("/api/taixiu", methods=["GET"])
def get_taixiu():
    with lock:
        return jsonify(latest_result)


# ===== Main =====
if __name__ == "__main__":
    logger.info("Khởi động hệ thống API Tài Xỉu...")
    thread = threading.Thread(target=poll_api, daemon=True)
    thread.start()
    logger.info("Đã bắt đầu polling dữ liệu.")
    port = int(os.environ.get("PORT", 8000))  # Render sẽ gán PORT
    logger.info(f"Server chạy trên port {port}")
    app.run(host=HOST, port=port)
