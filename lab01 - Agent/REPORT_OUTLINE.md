# CẤU TRÚC BÁO CÁO THỰC HÀNH TÁC TỬ THÔNG MINH (LAB 01)
**Môn học:** Trí tuệ Nhân tạo Nâng cao  
**Chủ đề:** Tác tử Phản xạ - Robot Hút Bụi - GridHunt - Lunar Lander  

---

## MỤC LỤC CHI TIẾT (REPORT OUTLINE)

### PHẦN MỞ ĐẦU
* Lời cảm ơn / Lời cam đoan
* Thông tin nhóm thực hiện & Phân công công việc

---

### CHƯƠNG 1: TỔNG QUAN VÀ ĐẶC TẢ BÀI TOÁN TÁC TỬ (PEAS)
* **1.1 GIỚI THIỆU CHUNG VỀ TÁC TỬ THÔNG MINH**
  * 1.1.1 Khái niệm tác tử (Agent) và môi trường (Environment)
  * 1.1.2 Chu trình Cảm nhận - Ra quyết định - Hành động (Percept - Think - Act)
  * 1.1.3 Phân loại tác tử: Tác tử ngẫu nhiên, Tác tử phản xạ đơn giản và Tác tử phản xạ dựa trên mô hình
* **1.2 ĐẶC TẢ PEAS CHO CÁC BÀI TOÁN THỰC HÀNH**
  * 1.2.1 Bài toán Robot hút bụi (Vacuum Cleaner)
    * Performance Measure (Độ đo hiệu năng)
    * Environment (Môi trường hoạt động)
    * Actuators (Cơ cấu tác động)
    * Sensors (Hệ thống cảm biến)
  * 1.2.2 Bài toán Thợ săn quái vật (GridHunt)
    * PEAS cho phiên bản đơn tác tử
    * PEAS cho phiên bản đa tác tử cạnh tranh
  * 1.2.3 Bài toán Tàu đổ bộ mặt trăng (Lunar Lander)
    * Không gian quan sát 8 chiều (Observation Space)
    * Không gian hành động 4 chiều rời rạc (Action Space)
    * Hàm phần thưởng và tiêu chí hạ cánh an toàn
* **1.3 PHÂN LOẠI ĐẶC TÍNH MÔI TRƯỜNG**
  * 1.3.1 Các tiêu chí phân loại (Quan sát đầy đủ/Bộ phận, Tất định/Ngẫu nhiên, Tĩnh/Động, Rời rạc/Liên tục, Đơn tác tử/Đa tác tử)
  * 1.3.2 Bảng tổng hợp so sánh đặc tính 3 môi trường thực nghiệm

---

### CHƯƠNG 2: THIẾT KẾ VÀ CÀI ĐẶT TÁC TỬ ROBOT HÚT BỤI
* **2.1 XÂY DỰNG MÔI TRƯỜNG MÔ PHỎNG (SIMULATION ENVIRONMENT)**
  * 2.1.1 Cấu trúc dữ liệu lưới phòng $n \times n$ và phân bố bụi ban đầu
  * 2.1.2 Cơ chế tạo cảm biến: Va chạm biên (`bumpers`) và cảm nhận bụi (`dirty`)
  * 2.1.3 Cập nhật trạng thái môi trường và hàm hiển thị trực quan (`display_environment`)
  * 2.1.4 Tiêu chuẩn đánh giá năng lượng và điều kiện dừng
* **2.2 CÀI ĐẶT VÀ PHÂN TÍCH CÁC MÔ HÌNH TÁC TỬ**
  * 2.2.1 Tác tử ngẫu nhiên (Simple Randomized Agent)
  * 2.2.2 Tác tử phản xạ đơn giản (Simple Reflex Agent - Luật điều kiện - hành động)
  * 2.2.3 Tác tử phản xạ dựa trên mô hình (Model-Based Reflex Agent)
    * Thiết kế trạng thái bên trong (`Internal State`: pha hoạt động, tọa độ ước tính, hướng quét)
    * Chiến lược định vị ban đầu (Localization về góc `(0, 0)`)
    * Chiến lược quét phủ kín có hệ thống (Systematic Boustrophedon Sweep)
* **2.3 THỰC NGHIỆM ĐÁNH GIÁ HIỆU NĂNG (SIMULATION STUDY)**
  * 2.3.1 Thiết lập kịch bản kiểm thử: Kích thước $5\times 5, 10\times 10, 100\times 100$ qua 100 lần chạy
  * 2.3.2 Bảng tổng hợp số liệu năng lượng tiêu thụ trung bình
  * 2.3.3 Biểu đồ so sánh và phân tích độ phức tạp thời gian/năng lượng
* **2.4 ĐÁNH GIÁ TÍNH BỀN VỮNG (ROBUSTNESS) VÀ CẢI TIẾN CẢM BIẾN NHIỄU**
  * 2.4.1 Đánh giá tác tử trong phòng chữ nhật kích thước chưa biết
  * 2.4.2 Đánh giá tác tử trong phòng có hình dạng bất quy tắc (hành lang, chữ L)
  * 2.4.3 Đánh giá tác tử trong môi trường có chướng ngại vật (Obstacles)
  * 2.4.4 Tác động của cảm biến va chạm bị nhiễu (Imperfect Bumpers)
  * 2.4.5 Cải tiến tác tử với cảm biến bụi bị nhiễu 10% (Advanced Task - Two-Pass Sweep)

---

### CHƯƠNG 3: THIẾT KẾ VÀ CÀI ĐẶT TÁC TỬ GRIDHUNT
* **3.1 BÀI TOÁN GRIDHUNT ĐƠN TÁC TỬ (SINGLE AGENT)**
  * 3.1.1 Tác tử thợ săn ngẫu nhiên (Random Hunter Baseline)
  * 3.1.2 Tác tử phản xạ dựa trên mô hình (Model-Based Hunter)
    * Khai thác hành động lắng nghe (`listen`) để thu thập vị trí quái vật
    * Lưu vết vị trí và quy hoạch hướng đi rút ngắn khoảng cách Manhattan
  * 3.1.3 Kết quả thực nghiệm trên đấu trường $10 \times 10$ và $30 \times 30$ (Tỷ lệ bắt thành công, Số bước trung bình)
  * 3.1.4 Thảo luận vai trò của hành động `teleport` (Lợi thế, rủi ro và tác động của kích thước đấu trường)
* **3.2 BÀI TOÁN GRIDHUNT ĐA TÁC TỬ (MULTI-AGENT COMPETITION)**
  * 3.2.1 Cơ chế thi đấu giữa 2 thợ săn cạnh tranh cùng một quái vật
  * 3.2.2 Thiết kế chiến lược thợ săn 1: Săn đuổi trực diện (Greedy Pursuit Hunter)
  * 3.2.3 Thiết kế chiến lược thợ săn 2: Dự đoán và đón đầu (Predictive / Interception Hunter)
  * 3.2.4 Thực nghiệm đối đầu trực tiếp trên đấu trường $20 \times 20$ và $\ge 30 \times 30$
  * 3.2.5 Đề xuất kiến trúc chuyển đổi từ cạnh tranh sang hợp tác (Cooperative Multi-Agent)

---

### CHƯƠNG 4: THIẾT KẾ VÀ CÀI ĐẶT TÁC TỬ LUNAR LANDER TRÊN GYMNASIUM
* **4.1 TỔNG QUAN MÔI TRƯỜNG ĐỔ BỘ LUNAR LANDER**
  * 4.1.1 Cấu trúc vật lý Box2D và cơ chế điều khiển 4 động cơ
  * 4.1.2 Ý nghĩa vật lý của vector quan sát 8 chiều ($x, y, v_x, v_y, \theta, \omega, \text{leg}_1, \text{leg}_2$)
* **4.2 XÂY DỰNG CÁC TÁC TỬ ĐIỀU KHIỂN HẠ CÁNH**
  * 4.2.1 Tác tử ngẫu nhiên (Random Baseline)
  * 4.2.2 Tác tử phản xạ đơn giản (Simple Reflex Agent - Kích hoạt động cơ chính theo ngưỡng vận tốc rơi)
  * 4.2.3 Tác tử phản xạ nâng cao đa tham số (Enhanced Multi-Rule Reflex Agent)
    * Luật cân bằng góc nghiêng ($\theta, \omega$) bằng động cơ phụ trái/phải
    * Luật định hướng tàu về tọa độ hạ cánh an toàn ($x = 0$)
    * Luật giảm chấn tiếp đất khi hai chân tiếp xúc bề mặt
* **4.3 THỰC NGHIỆM VÀ ĐÁNH GIÁ ĐỘ ỔN ĐỊNH**
  * 4.3.1 Đánh giá qua 100 Episode thử nghiệm: Điểm số trung bình (Mean Reward) và Độ lệch chuẩn
  * 4.3.2 Tỷ lệ hạ cánh thành công (Landing Success Rate) và biểu đồ phân phối phần thưởng
  * 4.3.3 Phân tích hạn chế cốt lõi của tác tử phản xạ luật cục bộ trong môi trường liên tục

---

### CHƯƠNG 5: TỔNG KẾT VÀ HƯỚNG PHÁT TRIỂN
* **5.1 ĐÁNH GIÁ KẾT QUẢ ĐẠT ĐƯỢC**
  * 5.1.1 Mức độ hoàn thành mục tiêu đề bài
  * 5.1.2 So sánh tổng quan hiệu năng giữa 3 nhóm bài toán
* **5.2 ƯU ĐIỂM VÀ HẠN CHẾ CỦA HỆ THỐNG**
  * 5.2.1 Ưu điểm của phương pháp tiếp cận dựa trên luật phản xạ và trạng thái
  * 5.2.2 Hạn chế khi không gian trạng thái mở rộng hoặc môi trường có tính bất định cao
* **5.3 HƯỚNG CẢI TIẾN VÀ PHÁT TRIỂN TRONG TƯƠNG LAI**
  * 5.3.1 Tích hợp thuật toán quy hoạch đường đi (BFS, DFS, A*) giải quyết vật cản
  * 5.3.2 Ứng dụng Học tăng cường (Reinforcement Learning - Q-Learning, PPO, DQN) cho môi trường liên tục

---

### TÀI LIỆU THAM KHẢO & PHỤ LỤC
* Danh mục tài liệu tham khảo (Giáo trình AIMA, Tài liệu môn học, Gymnasium Doc)
* Hướng dẫn cài đặt môi trường và chạy lại mã nguồn (Reproducibility Guide)
