const express = require("express");
const axios = require("axios");

const app = express();
const PORT = process.env.PORT || 3000;

let latestResult = {
  Phien: 0,
  Xuc_xac_1: 0,
  Xuc_xac_2: 0,
  Xuc_xac_3: 0,
  Tong: 0,
  Ket_qua: "Chưa có"
};

// Biến để chống spam log
let lastLoggedPhien = null;

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

    // Nếu API không hợp lệ thì giữ nguyên phiên hiện tại
    if (!resp.data || resp.data.status !== "OK" || !Array.isArray(resp.data.data)) {
      if (latestResult.Phien && lastLoggedPhien !== latestResult.Phien) {
        console.log("⏸ API chưa có dữ liệu, giữ nguyên phiên:", latestResult.Phien);
        lastLoggedPhien = latestResult.Phien;
      }
      return;
    }

    // tìm phiên có cmd = 7006
    const game = resp.data.data.find(g => g.cmd === 7006);
    if (game && game.d1 != null && game.d2 != null && game.d3 != null) {
      const total = game.d1 + game.d2 + game.d3;
      const ket_qua = getTaiXiu(game.d1, game.d2, game.d3);

      // chỉ log khi có phiên mới
      if (game.sid !== latestResult.Phien) {
        latestResult = {
          Phien: game.sid,
          Xuc_xac_1: game.d1,
          Xuc_xac_2: game.d2,
          Xuc_xac_3: game.d3,
          Tong: total,
          Ket_qua: ket_qua
        };
        console.log(`[TX] ✅ Phiên ${game.sid} - Tổng: ${total}, KQ: ${ket_qua}`);
        lastLoggedPhien = game.sid;
      }
    } else {
      if (latestResult.Phien && lastLoggedPhien !== latestResult.Phien) {
        console.log("⏸ Không có kết quả mới, giữ nguyên phiên:", latestResult.Phien);
        lastLoggedPhien = latestResult.Phien;
      }
    }
  } catch (err) {
    console.error("❌ Lỗi khi lấy dữ liệu API:", err.message);
  }
}

// Poll API mỗi 5 giây
setInterval(pollApi, 5000);

// Endpoint API
app.get("/api/taixiu", (req, res) => {
  res.json(latestResult);
});

// Fix Not Found khi load root
app.get("/", (req, res) => {
  res.send("✅ API TaiXiu đang chạy! Endpoints: /api/taixiu");
});

// Start server
app.listen(PORT, () => {
  console.log(`✅ Server chạy trên cổng ${PORT}`);
});
