# Kết quả cá nhân — Ly

## 1. Tic-Tac-Toe: PMCS và UCB1

N là tổng số mô phỏng. Mỗi cấu hình đo trên 30 seed (0–29); thi đấu với Random dùng seed 42, 100 ván mỗi vai. Thời gian trung bình/nước chỉ tính thời gian agent chọn nước.

### Độ ổn định trên bốn trạng thái

Mỗi ô ghi **nước phổ biến nhất / tỷ lệ chọn (%) / thời gian trung bình (ms)**. Chỉ số nước đi từ 0 đến 8.

| Trạng thái | PMCS-10 | PMCS-100 | PMCS-1000 | UCB1-10 | UCB1-100 |
|---|---|---|---|---|---|
| T1: X sắp thắng | 8 / 33,3 / 0,768 | 8 / 100 / 5,387 | 8 / 100 / 54,241 | 6 / 33,3 / 1,015 | 8 / 100 / 7,413 |
| T2: X cần hòa | 7 / 46,7 / 0,797 | 7 / 90 / 7,643 | 7 / 100 / 64,583 | 7 / 43,3 / 0,959 | 7 / 96,7 / 9,990 |
| T3: Bất lợi | 4 / 33,3 / 1,071 | 4 / 90 / 6,690 | 4 / 100 / 65,800 | 4 / 50 / 1,268 | 4 / 100 / 12,975 |
| T4: Bàn rỗng | 0 / 23,3 / 3,165 | 4 / 33,3 / 20,657 | 4 / 86,7 / 154,297 | 4 / 20 / 3,576 | 4 / 43,3 / 24,456 |

Tỷ lệ chọn nước phổ biến nhất phản ánh độ ổn định, không đồng nghĩa tỷ lệ tối ưu. T1 có nhiều nước thắng tối ưu; T3 thua ở mọi nước khi đối thủ chơi tối ưu; T4 có giá trị minimax hòa ở mọi nước mở đầu.

### Thi đấu với Random

Thắng/hòa/thua tính từ góc nhìn agent được đánh giá.

| Agent | Vai | Thắng | Hòa | Thua | TB/nước (ms) |
|---|---|---:|---:|---:|---:|
| PMCS-10 | X | 94 | 2 | 4 | 1,123 |
| PMCS-10 | O | 74 | 8 | 18 | 1,348 |
| PMCS-100 | X | 97 | 3 | 0 | 9,487 |
| PMCS-100 | O | 90 | 6 | 4 | 8,095 |
| UCB1-10 | X | 94 | 4 | 2 | 1,373 |
| UCB1-10 | O | 70 | 12 | 18 | 1,616 |
| UCB1-100 | X | 99 | 1 | 0 | 15,052 |
| UCB1-100 | O | 87 | 6 | 7 | 12,465 |

PMCS cấp ngân sách đều cho các nước. UCB1 ưu tiên utility trung bình cao (exploitation), đồng thời thử thêm các nước ít được thăm (exploration). UCB1 trong bài chỉ mở cây ở độ sâu 1.

## 2. Connect 4

Số liệu hiện dùng luật dự phòng trong `connect4_search.py` của Thiện, do chưa có `connect4_core.py` của Hải.

### Kết quả tích hợp chính

| Thí nghiệm | Kết quả |
|---|---|
| Random vs Random, 6×7, 1.000 ván | Bên đi trước thắng 572; hòa 2; bên đi sau thắng 426 |
| Alpha-Beta vs Random, 4×4, 10 ván làm +1 | 7 thắng / 3 hòa / 0 thua; 951,818 ms/nước AB |
| Alpha-Beta vs Random, 4×4, 10 ván làm −1 | 9 thắng / 1 hòa / 0 thua; 614,209 ms/nước AB |
| Full Alpha-Beta bàn rỗng 4×4, ordering off | 62.889 nút; 4,949 s; giá trị 0 |
| Full Alpha-Beta bàn rỗng 4×4, centre-first | 155.968 nút; 11,744 s; giá trị 0 |
| Heuristic cutoff 2 vs 4, 6×7 | Cutoff 2 thắng ở cả hai lượt đổi vai |

### PMCS trên năm trạng thái 6×7

Mỗi ô ghi **cột chọn / thời gian (s)**, seed 42. Cột đánh số từ 0.

| Trạng thái | N=10 | N=100 | N=1000 |
|---|---|---|---|
| Thắng ngang | 3 / 0,035 | 3 / 0,363 | 3 / 3,123 |
| Thắng dọc | 2 / 0,034 | 2 / 0,349 | 2 / 2,479 |
| Chặn thua ngang | 3 / 0,018 | 3 / 0,213 | 3 / 2,243 |
| Thắng chéo | 3 / 0,011 | 3 / 0,091 | 3 / 1,095 |
| Bàn rỗng | 5 / 0,053 | 1 / 0,499 | 3 / 4,586 |

PMCS có kiểm tra thắng ngay trước khi chọn kết quả cuối; thành công ở các thế thắng ngay không chỉ đến từ ước lượng rollout. Các bảng chi tiết về heuristic và kích thước bàn nằm trong notebook Connect 4.

## 3. Nhận xét

1. Tăng N giúp quyết định ổn định hơn trong các phép đo này nhưng tăng thời gian: ở T2, PMCS chọn đúng nước hòa từ 46,7% lên 100% khi N tăng từ 10 lên 1000.
2. UCB1-100 đạt 96,7% chọn nước hòa ở T2, nhưng kết quả đấu Random thay đổi theo vai; chưa đủ cơ sở kết luận UCB1 luôn mạnh hơn PMCS.
3. Move ordering không luôn giảm số nút: centre-first duyệt nhiều hơn thứ tự tự nhiên trên bàn rỗng 4×4. Tăng cutoff cũng không bảo đảm thắng đối thủ dùng cutoff thấp hơn.
4. Random rollout đánh giá đối thủ ngẫu nhiên, nên có thể bỏ sót phản ứng chiến thuật tốt nhất. Tăng số mô phỏng giảm nhiễu nhưng không thay đổi mô hình đối thủ.
5. Full search chỉ dùng cho bàn nhỏ hoặc cuối ván; bàn chuẩn 6×7 cần cutoff hoặc Monte Carlo. Các kết quả Connect 4 cần được đối chiếu lại khi nhận core chính thức; thời gian phụ thuộc máy và tải nền.
