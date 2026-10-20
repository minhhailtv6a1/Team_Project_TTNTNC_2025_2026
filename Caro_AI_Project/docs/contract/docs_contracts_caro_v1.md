# Đặc tả Hợp đồng API Trò chơi Caro (Gomoku) \- Phiên bản 1 (caro-v1)

Tài liệu này định nghĩa các cấu trúc dữ liệu và giao diện API cốt lõi (Contract) cho trò chơi Caro. Contract này đóng vai trò là "nguồn sự thật duy nhất" (Single Source of Truth) giúp các nhóm làm Giao diện (UI) và Thuật toán AI (Engine/Agents) làm việc độc lập mà không cần phải đoán ý nhau.

## 1\. Quy ước chung

* **Không gian trạng thái:** Bàn cờ được biểu diễn dưới dạng ma trận 2 chiều (Mảng của các mảng). Tọa độ được quy ước là (row, col) (dòng, cột), bắt đầu từ chỉ số 0\. Dòng chạy từ trên xuống dưới, cột chạy từ trái sang phải.  
* **Kích thước bàn cờ mặc định:** Bàn cờ chuẩn là 9x9 hoặc 11x11, được cấu hình thông qua GameConfig.  
* **Luật thắng:** Trò chơi sử dụng luật **chặn 2 đầu**. Cụ thể, một người chơi thắng khi có đúng 5 quân cờ liên tiếp theo chiều ngang, dọc, hoặc chéo, và không bị đối phương chặn ở cả hai đầu của chuỗi 5 quân đó. Việc xác minh tính đúng đắn của luật này do Engine nội bộ xử lý, API bên ngoài chỉ cần nhận kết quả thông qua StepResult.

## **2\. Định nghĩa các thực thể (Entities)**

### **2.1. Người chơi (Player)**

Sử dụng Enum Player để đại diện cho trạng thái của mỗi ô trên bàn cờ và lượt đi hiện tại.

* Player.X (Giá trị: 1): Người chơi đi trước. Thường được biểu diễn bằng ký hiệu 'X'.  
* Player.O (Giá trị: \-1): Người chơi đi sau. Thường được biểu diễn bằng ký hiệu 'O'.  
* Player.EMPTY (Giá trị: 0): Ô trống trên bàn cờ.

### **2.2. Cấu hình trò chơi (GameConfig)**

Dùng để khởi tạo môi trường, cho phép linh hoạt thay đổi kích thước bàn cờ.

* board\_size (int): 11 Kích thước bàn cờ.  
* win\_length (int): 5 Số quân liên tiếp cần để thắng 

### **2.3. Trạng thái ván đấu (GameState)**

Đây là cấu trúc dữ liệu quan trọng nhất, lưu trữ toàn bộ tình trạng của bàn cờ tại một thời điểm.

* board (List\[List\[int\]\]): Ma trận 2 chiều kích thước board\_size x board\_size, chứa các giá trị của Enum Player (1, \-1, hoặc 0).  
* current\_player (Player): Xác định người chơi sẽ thực hiện nước đi tiếp theo.

### **2.4. Kết quả của một nước đi (StepResult)**

Cấu trúc này được trả về sau mỗi lần một người chơi thực hiện thành công một nước đi.

* next\_state (GameState): Trạng thái bàn cờ mới sau khi thực hiện nước đi. Đây phải là một bản sao độc lập (clone) để tránh lỗi tham chiếu khi AI thực hiện duyệt cây (như trong MCTS).  
* reward (float): Phần thưởng (theo góc nhìn của người vừa thực hiện nước đi). Có thể dùng các giá trị chuẩn: 1.0 (Thắng), \-1.0 (Thua), 0.0 (Chưa kết thúc hoặc Hòa).  
* done (bool): True nếu ván đấu đã kết thúc (có người thắng hoặc hòa/hết bàn cờ), ngược lại là False.  
* winner (Optional\[Player\]): Trả về Player.X hoặc Player.O nếu có người thắng. Nếu ván đấu hòa hoặc chưa kết thúc, giá trị này là None.

### **2.5. Xử lý lỗi (InvalidActionError)**

Một Exception chuyên biệt có tên InvalidActionError sẽ được ném ra (raise) ngay lập tức nếu một nước đi vi phạm quy tắc cơ bản:

* Đánh ra ngoài phạm vi bàn cờ (Tọa độ âm hoặc vượt quá board\_size \- 1).  
* Đánh vào ô đã có quân cờ (Giá trị khác Player.EMPTY).  
* *Lưu ý:* Khi Exception này được ném ra, GameState (Bàn cờ và lượt đi) **phải được giữ nguyên vẹn**, không có bất kỳ thay đổi nào.

## **3\. Giao diện Môi trường (GameEnv API)**

Lớp CaroEnv cung cấp các phương thức tiêu chuẩn để tương tác với ván đấu.

* reset() \-\> GameState: Khởi tạo lại một ván đấu mới, bàn cờ trống hoàn toàn. Lượt đi được đặt về Player.X.  
* legal\_actions() \-\> List\[Tuple\[int, int\]\]: Trả về một danh sách chứa tọa độ (row, col) của tất cả các ô còn trống trên bàn cờ hiện tại.  
* step(action: Tuple\[int, int\]) \-\> StepResult: Nhận tọa độ nước đi, cập nhật bàn cờ, đảo lượt đi, và trả về kết quả (next\_state, reward, done, winner). Nếu action không hợp lệ, ném ra InvalidActionError.  
* clone\_env(): Trả về một bản sao hoàn toàn độc lập (deep copy) của Môi trường hiện tại. Tính năng này **bắt buộc** phải có để các thuật toán AI như Minimax và MCTS có thể giả lập các nhánh nước đi trong tương lai mà không làm hỏng trạng thái của ván cờ chính.  
* is\_terminal() \-\> bool: Kiểm tra xem trạng thái hiện tại đã là trạng thái kết thúc chưa (có người thắng hoặc hòa).  
* render(): Phương thức tiện ích để in trạng thái bàn cờ ra console, hỗ trợ quá trình debug trực quan.

---

**Hướng dẫn cho UI Team (M1):** Bạn có thể sử dụng file tests/fixtures/caro\_v1\_cases.json làm mock data để render giao diện mà không cần chờ Engine Team code xong. **Hướng dẫn cho Engine Team (M2):** Hãy bám sát định nghĩa của GameState và kiểu trả về của step(). Hàm kiểm tra luật thắng của bạn (chặn 2 đầu) sẽ được tích hợp vào trong phương thức step() này.