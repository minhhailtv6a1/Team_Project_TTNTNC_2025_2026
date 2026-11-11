# Kết quả cá nhân — Thiện

## Protocol

- Seed mặc định: `42`; đồng hồ dùng `time.perf_counter()`.
- Node counter được tạo mới cho từng lần search. Thời gian là thời gian của một lần gọi search, không gồm render bảng/Matplotlib hoặc kiểm tra hậu nghiệm tập nước đi tối ưu.
- `Tổng thời gian` ở các trận đấu là tổng mọi lần agent chọn nước; `TB/nước agent = tổng thời gian / số nước agent`, **không** phải tổng thời gian chia số ván.
- Số mili-giây thay đổi theo máy và tải nền; node/value/move mới là các chỉ số tái lập chính.

## Tic-Tac-Toe — Minimax và Alpha-Beta

|Trạng thái|Minimax: move/value/nodes/ms|Alpha-Beta: move/value/nodes/ms|
|---|---:|---:|
|T1 X sắp thắng|2 / 1 / 190 / 9.494|2 / 1 / 61 / 3.156|
|T2 X cần hòa|7 / 0 / 206 / 10.616|7 / 0 / 101 / 4.982|
|T3 bất lợi|1 / -1 / 941 / 46.387|1 / -1 / 238 / 11.843|
|T4 bàn rỗng|0 / 0 / 549,946 / 26,517.475|0 / 0 / 18,297 / 1,008.932|

Khẳng định đã chạy: hai thuật toán luôn cùng giá trị **và cùng tập nước đi tối ưu**. Các tập tương ứng T1 `(2,6,8)`, T2 `(7,)`, T3 `(1,3,4,5,6,7)`, T4 `(0..8)`; vì vậy không ép hai thuật toán phải chọn cùng chỉ số khi có hòa.

### Alpha-Beta: ordering off/on

|Trạng thái|Off nodes/ms|On (giữa→góc→cạnh) nodes/ms|Thay đổi node|
|---|---:|---:|---:|
|T1|61 / 3.205|44 / 2.280|-27.9%|
|T2|101 / 5.995|149 / 7.576|+47.5%|
|T3|238 / 12.048|51 / 2.394|-78.6%|
|T4|18,297 / 875.534|7,275 / 363.398|-60.2%|

Ordering tĩnh không bảo đảm luôn tốt: T2 tăng node. Tuy vậy ở bàn rỗng và T3 nó giảm đáng kể vì nước tốt được duyệt sớm, tạo cận alpha/beta để cắt nhánh.

## Tic-Tac-Toe — heuristic Alpha-Beta

|Trạng thái|Full: move/value/nodes/ms|cutoff 2: move/value/nodes/ms|cutoff 4: move/value/nodes/ms|
|---|---:|---:|---:|
|T1|2 / 1 / 44 / 1.090|8 / 1 / 14 / 1.037|2 / 1 / 36 / 1.843|
|T2|7 / 0 / 149 / 3.293|7 / -0.13 / 26 / 2.007|7 / -0.05 / 120 / 7.140|
|T3|4 / -1 / 51 / 2.617|4 / -0.23 / 17 / 2.390|4 / -1 / 35 / 2.935|
|T4|4 / 0 / 7,275 / 429.053|4 / 0.11 / 26 / 5.629|4 / 0.05 / 283 / 58.420|

Trên bộ T1–T4 này, tất cả nước cutoff đều thuộc tập nước tối ưu của full search. Tuy nhiên giá trị heuristic ở cutoff khác utility cuối ván (ví dụ T2/T4), nên đây không phải bảo đảm tổng quát về chất lượng.

|Agent|Vai|Thắng/Hòa/Thua|Nước agent|Tổng thời gian (s)|TB/nước agent (ms)|
|---|---|---:|---:|---:|---:|
|Heuristic AB cutoff=2|X|96 / 4 / 0|328|1.5233|4.6443|
|Heuristic AB cutoff=2|O|89 / 11 / 0|322|1.1211|3.4816|
|Heuristic AB cutoff=4|X|96 / 4 / 0|378|11.7614|31.1149|
|Heuristic AB cutoff=4|O|83 / 17 / 0|351|8.7444|24.9128|

## Connect 4 search

`connect4_search.py` cài Alpha-Beta exact (chỉ dùng full search cho 4×4), ordering tâm bàn, heuristic cửa sổ 4 ô và cutoff. `evaluate` dành ±1 cho terminal và chuẩn hóa non-terminal bằng `tanh`, nên luôn thuộc `[-1, 1]`.

Các test thủ công trong `tests/test_connect4_search.py`: thắng ngay, chặn thua, thắng ngang, thắng dọc, thắng chéo được đỡ quân, và ưu tiên tâm bàn. Test cũng kiểm tra range heuristic, schema metrics, callable agents và không mutate input.

|Thí nghiệm|Cấu hình|Move/value|Nodes|Thời gian (ms)|
|---|---|---:|---:|---:|
|Full Alpha-Beta bàn rỗng 4×4|ordering off|0 / 0|62,889|1,937.713|
|Full Alpha-Beta bàn rỗng 4×4|ordering centre-first|1 / 0|155,968|5,324.759|
|Heuristic AB bàn rỗng 6×7|cutoff=2|3 / -0.045|24|14.274|
|Heuristic AB bàn rỗng 6×7|cutoff=4|3 / -0.030|234|96.404|
|Heuristic AB bàn rỗng 6×7|cutoff=6|3 / -0.033|1,458|541.534|

Ở đúng bàn rỗng 4×4 này, centre-first tệ hơn thứ tự cột tự nhiên; đó là kết quả hợp lệ của static ordering, không phải lỗi correctness. Vì game tree 6×7 có branching factor gần 7 và độ sâu tối đa 42, không dùng full Alpha-Beta ở 6×7; cutoff/heuristic là bắt buộc để thời gian phản hồi thực tế.

## Kiểm thử

```text
python -m pytest tests/test_connect4_search.py -q
7 passed
```

Hai notebook đã chạy từ kernel mới bằng `jupyter nbconvert --to notebook --execute --inplace ...` và không có traceback.
