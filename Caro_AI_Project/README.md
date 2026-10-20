# Caro AI Project

Ứng dụng Caro phục vụ đồ án Trí tuệ nhân tạo nâng cao. Giao diện Tuần 1 chạy
bằng Streamlit và sử dụng `MockGameEnv`; logic thắng/thua đầy đủ vẫn thuộc game
engine.

## Chạy giao diện W1-M1-03

Chạy ba lệnh sau từ thư mục gốc dự án trên PowerShell:

```powershell
py -3.13 -m venv myenv
.\myenv\Scripts\python.exe -m pip install -r requirements.txt
.\myenv\Scripts\python.exe -m streamlit run ui/app.py
```

Mở địa chỉ Streamlit in ra trong terminal, mặc định là
`http://localhost:8501`.

## Phạm vi giao diện Tuần 1

- Human vs Human hoạt động với bàn 9x9 hoặc 11x11.
- Các lựa chọn AI đã có trong giao diện nhưng chưa gọi agent.
- UI chỉ đọc `GameState` và gọi API môi trường; không chứa logic thắng/thua.
- Click ô đã có quân hiển thị lỗi và không thay đổi state.

Chạy kiểm thử:

```powershell
.\myenv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```
