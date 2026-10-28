# Caro AI Project

Ứng dụng Caro phục vụ đồ án Trí tuệ nhân tạo nâng cao. UI được xây dựng bằng
Streamlit và hiện tập trung phát triển bàn cờ 11x11.

## Yêu cầu môi trường

| Thành phần | Yêu cầu |
| --- | --- |
| Hệ điều hành | Windows 10 hoặc Windows 11 |
| Python | Phiên bản 3.13 |
| Kết nối mạng | Cần thiết trong lần đầu cài dependencies |

Tất cả lệnh bên dưới cần được chạy bằng PowerShell tại thư mục gốc của dự án,
nơi chứa `README.md` và `requirements.txt`.

## Setup lần đầu

Kiểm tra Python 3.13 đã được cài đặt:

```powershell
py -3.13 --version
```

Tạo virtual environment riêng cho dự án:

```powershell
py -3.13 -m venv myenv
```

Cập nhật pip và cài dependencies:

```powershell
.\myenv\Scripts\python.exe -m pip install --upgrade pip
.\myenv\Scripts\python.exe -m pip install -r requirements.txt
```

Không cần kích hoạt virtual environment vì các lệnh trong README gọi trực tiếp
Python bên trong thư mục `myenv`.

## Chạy UI

Khởi động Streamlit:

```powershell
.\myenv\Scripts\python.exe -m streamlit run ui/app.py
```

Sau khi server khởi động, trình duyệt thường tự mở. Nếu trình duyệt không tự
mở, truy cập địa chỉ:

```text
http://localhost:8501
```

Nhấn `Ctrl+C` trong PowerShell để dừng server.

Từ lần chạy tiếp theo, nếu thư mục `myenv` vẫn còn và `requirements.txt` không
thay đổi, chỉ cần chạy lại lệnh khởi động Streamlit.

### Chạy bằng port khác

Nếu port 8501 đang được sử dụng, có thể chọn port khác:

```powershell
.\myenv\Scripts\python.exe -m streamlit run ui/app.py --server.port 8502
```

Sau đó truy cập `http://localhost:8502`.

## Xử lý lỗi thường gặp

| Lỗi | Cách xử lý |
| --- | --- |
| Không nhận lệnh `py` | Cài Python 3.13 và bật tùy chọn thêm Python vào PATH |
| Báo thiếu package | Chạy lại lệnh cài `requirements.txt` bằng Python trong `myenv` |
| Port 8501 đang được sử dụng | Chạy UI bằng một port khác như hướng dẫn phía trên |
| UI chưa cập nhật sau khi sửa code | Tải lại trang hoặc dừng server rồi khởi động lại |

## Chạy kiểm thử

```powershell
.\myenv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

## Phạm vi hiện tại

- 11x11 là module bàn cờ chính và là kích thước duy nhất được hiển thị, phát
  triển và kiểm thử.
- 9x9 đang tạm ngưng. Kiến trúc vẫn đọc `board_size` từ `GameConfig` để có thể
  mở rộng trong tương lai.
- Chế độ Human vs Human chạy trực tiếp với `CaroEnv` theo contract `caro-v2`.
- Các lựa chọn AI đã có trên UI nhưng chưa kết nối với agent.
- UI đọc `GameState` và gọi API của môi trường, không tự xử lý logic thắng thua.
