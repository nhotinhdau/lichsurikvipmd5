const express = require("express");
const axios = require("axios");

const app = express();
const PORT = process.env.PORT || 3000;

// Biến lưu kết quả mới nhất
let latestResult = {
  Phien: 0,
  Xuc_xac_1: 0,
  Xuc_xac_2: 0,
  Xuc_xac_3: 0,
  Tong: 0,
  Ket_qua: "Chưa có"
};

let lastSid = null;

// Hàm tính Tài/Xỉu
function getTaiXiu(d1, d2, d3) {
  const total = d1 + d2 + d3;
  return total <= 10 ? "Xỉu" : "Tài";
}

// Hàm gọi API
async function pollApi() {
  const url =
    "https://jakpotgwab.geightdors.net/glms/v1/notify/taixiu?platform_id=rik&gid=vgmn_101";

  try {
    const resp = await axios.get(url, {
      headers: { "User-Agent": "Node-Proxy/1.0" },
      timeout: 10000
    });

    if (resp.data.status === "OK" && Array.isArray(resp.data.data)) {
      for (const game of resp.data.data) {
        if (game.cmd === 7006) {
          const sid = game.sid;
          const d1 = game.d1,
            d2 = game.d2,
            d3 = game.d3;

          if (sid && sid !== lastSid && d1 != null && d2 != null && d3 != null) {
            lastSid = sid;
            const total = d1 + d2 + d3;
            const ket_qua = getTaiXiu(d1, d2, d3);

            latestResult = {
              Phien: sid,
              Xuc_xac_1: d1,
              Xuc_xac_2: d2,
              Xuc_xac_3: d3,
              Tong: total,
              Ket_qua: ket_qua
            };

            console.log(`[TX] Phiên ${sid} - Tổng: ${total}, KQ: ${ket_qua}`);
          }
        }
      }
    }
  } catch (err) {
    console.error("Lỗi khi lấy dữ liệu API:", err.message);
  }
}

// Poll API mỗi 5 giây
setInterval(pollApi, 5000);

// Endpoint API
app.get("/api/taixiu", (req, res) => {
  res.json(latestResult);
});

// Start server
app.listen(PORT, () => {
  console.log(`✅ Server chạy trên cổng ${PORT}`);
});
