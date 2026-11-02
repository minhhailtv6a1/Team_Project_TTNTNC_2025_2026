# PHÂN CÔNG VIẾT BÁO CÁO ĐỒ ÁN AI CARO

## 1. Nguyên tắc phân công

- Việc phân công bám theo cấu trúc 7 chương trong `Cau_truc_bao_cao_do_an_AI_Caro.md` và quyền sở hữu công việc kỹ thuật của từng thành viên.
- Mỗi chương chỉ giao cho **một người viết chính và chịu trách nhiệm toàn bộ**; không chia một chương thành các mục nhỏ cho nhiều người.
- Người phụ trách chương chịu trách nhiệm viết đầy đủ nội dung, chuẩn hóa thuật ngữ, hình/bảng, trích dẫn và chỉnh sửa theo góp ý.
- Với nội dung có liên quan đến phần kỹ thuật của thành viên khác, người sở hữu kỹ thuật chỉ cung cấp số liệu, hình ảnh, kết quả chạy hoặc giải thích đầu vào. Người được giao chương vẫn là người tổng hợp và viết hoàn chỉnh chương đó.
- Khối lượng được chia theo độ dài và độ khó của chương, không chia đều chỉ theo số lượng chương.

## 2. Bảng phân công theo chương

| Thành viên | Chương phụ trách trọn vẹn | Cơ sở phân công | Sản phẩm phải bàn giao |
| --- | --- | --- | --- |
| **Trương Văn Thiện**<br>MSSV: `3123410356` | **Chương 1. Tổng quan về đề tài**<br>**Chương 3. Phân tích bài toán và thiết kế hệ thống**<br>**Chương 5. Thực nghiệm và đánh giá** | Thiện phụ trách kiến trúc tổng thể, Contract `caro-v2`, môi trường tương tác, luồng dữ liệu, logger, tournament runner và tổ chức thực nghiệm. Ba chương này tạo thành một mạch thống nhất từ xác định bài toán, thiết kế hệ thống đến đánh giá kết quả. | Chương 1 nêu đúng mục tiêu, phạm vi và sản phẩm; Chương 3 có mô hình hóa, kiến trúc, contract, hạ tầng thực nghiệm và chiến lược kiểm thử; Chương 5 có cấu hình thí nghiệm, giao thức, bảng số liệu, biểu đồ và phần trả lời các câu hỏi nghiên cứu. |
| **Lê Thị Trúc Ly**<br>MSSV: `3123410210` | **Chương 2. Cơ sở lý thuyết liên quan**<br>**Chương 4. Phương pháp đề xuất và cài đặt** | Ly phụ trách lõi game, luật Caro, Board/RuleEngine, Heuristic và Minimax kết hợp Alpha-Beta. Đây là các nội dung chiếm phần lớn nền tảng thuật toán ở Chương 2 và phần cài đặt cốt lõi ở Chương 4, nên giao trọn hai chương giúp lý thuyết và hiện thực nhất quán. | Chương 2 trình bày luật, mô hình trò chơi, heuristic, Minimax/Alpha-Beta, MCTS và tiêu chí đánh giá; Chương 4 mô tả đầy đủ engine và các agent bằng giả mã, lưu đồ hoặc đoạn mã tiêu biểu, đồng thời giải thích các quyết định tối ưu và giới hạn hiện tại. |
| **Trần Hồ Minh Hải**<br>MSSV: `3123410092` | **Chương 6. Xây dựng ứng dụng minh họa**<br>**Chương 7. Kết luận và hướng phát triển** | Hải phụ trách UI, API, MCTS, Neural AI và kiến trúc mạng học sâu. Chương 6 khớp trực tiếp với phần giao diện/tích hợp; Chương 7 phù hợp để tổng kết sản phẩm hoàn chỉnh và đề xuất các hướng mở rộng như cải tiến MCTS, tích hợp Neural AI, self-play và triển khai ứng dụng. | Chương 6 có kiến trúc UI, luồng tích hợp với engine, mô tả chức năng, ảnh chụp giao diện và kết quả kiểm thử; Chương 7 đối chiếu kết quả với mục tiêu, nêu hạn chế và đề xuất lộ trình phát triển khả thi. |

## 3. Nguồn đầu vào bắt buộc giữa các thành viên

Phần này chỉ quy định việc cung cấp tư liệu; **không làm thay đổi người chịu trách nhiệm viết trọn chương**.

| Người cung cấp | Người nhận | Tư liệu cần cung cấp |
| --- | --- | --- |
| **Trần Hồ Minh Hải** | **Lê Thị Trúc Ly** | Mô tả chính xác thuật toán MCTS/UCT, tham số ngân sách, kết quả kiểm thử MCTS và thông tin Neural AI để Ly tích hợp thống nhất vào Chương 2 và Chương 4. |
| **Lê Thị Trúc Ly** | **Trương Văn Thiện** | Kết quả kiểm thử engine, luật thắng, Heuristic, Minimax/Alpha-Beta, số node và thời gian chạy để Thiện tổng hợp trong Chương 5. |
| **Trần Hồ Minh Hải** | **Trương Văn Thiện** | Kết quả MCTS, ảnh giao diện và số liệu kiểm thử tích hợp để Thiện sử dụng trong Chương 5 khi cần. |
| **Trương Văn Thiện** | **Lê Thị Trúc Ly** | Đặc tả Contract `caro-v2`, schema dữ liệu/log, cấu hình tournament và quy ước metric để nội dung Chương 2 và Chương 4 đúng với hệ thống thực tế. |
| **Trương Văn Thiện** và **Lê Thị Trúc Ly** | **Trần Hồ Minh Hải** | Danh sách kết quả đã hoàn thành, hạn chế đã xác nhận và đề xuất kỹ thuật để Hải tổng hợp Chương 7. |

## 4. Phân công các phần ngoài chương

| Phần báo cáo | Người chịu trách nhiệm |
| --- | --- |
| Bìa, thông tin nhóm, lời cảm ơn và nhận xét của giảng viên | **Trương Văn Thiện** tổng hợp |
| Mục lục, danh mục hình, danh mục bảng và danh mục từ viết tắt | **Trần Hồ Minh Hải** cập nhật sau khi ghép bản thảo |
| Tài liệu tham khảo và kiểm tra trích dẫn | **Lê Thị Trúc Ly** tổng hợp; mỗi người phải gửi đủ nguồn đã dùng trong chương của mình |
| Phụ lục mã nguồn, cấu hình chạy và bảng số liệu chi tiết | **Trương Văn Thiện** tổng hợp từ tư liệu của cả nhóm |
| Ghép bản cuối, kiểm tra đánh số chương/mục/hình/bảng và thống nhất định dạng | **Trương Văn Thiện** chủ trì; cả nhóm cùng kiểm tra chéo |

## 5. Quy ước bàn giao

1. Mỗi thành viên nộp bản thảo theo đúng tên và thứ tự chương đã được giao; không tự ý sửa nội dung chương của người khác.
2. Mỗi chương phải có đủ nội dung theo cấu trúc báo cáo hiện hành, không bỏ mục nếu chưa có sự thống nhất của nhóm.
3. Hình, bảng và số liệu phải ghi rõ nguồn tạo, cấu hình chạy và thời điểm lấy kết quả để có thể tái lập.
4. Thuật ngữ chung phải thống nhất: bàn cờ $11 \times 11$, Contract `caro-v2`, Random Agent, Heuristic Agent, Minimax/Alpha-Beta và MCTS/UCT.
5. Trước khi ghép bản cuối, mỗi chương được một thành viên không phụ trách chương đó đọc chéo để phát hiện sai số liệu, sai thuật ngữ hoặc trùng lặp nội dung.

## 6. Tóm tắt phân công

- **Trương Văn Thiện:** Chương **1, 3, 5**.
- **Lê Thị Trúc Ly:** Chương **2, 4**.
- **Trần Hồ Minh Hải:** Chương **6, 7**.

Như vậy, cả 7 chương đều có đúng một người chịu trách nhiệm trọn vẹn, đồng thời nội dung được giao sát nhất với phần công việc kỹ thuật của từng thành viên.
