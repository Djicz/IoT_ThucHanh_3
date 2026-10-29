# Thực hành buổi 3 lập trình Python với CoAP

Bài thực hành gồm ba hệ thống Client–Server dùng CoAP qua UDP: gửi thông điệp, giám sát cảm biến và điều khiển đèn có Observe. Mã nguồn được kiểm thử trên Windows với Python **3.12.14** và **aiocoap 0.4.17**. Không cần MQTT Broker hoặc RabbitMQ.

## Thông tin sinh viên hoặc nhóm

| Nội dung | Thông tin |
|---|---|
| Họ tên thành viên | **Cần điền thông tin thật trước khi nộp** |
| Mã sinh viên | **Cần điền thông tin thật trước khi nộp** |
| Lớp / nhóm | **Cần điền thông tin thật trước khi nộp** |
| Repository GitHub | [Djicz/IoT_ThucHanh_3](https://github.com/Djicz/IoT_ThucHanh_3) |

Client bài 1 nhận thông tin thật qua bàn phím hoặc `--name` và `--student-id`. Dữ liệu `TEST001 / Sinh vien kiem thu` trong log chỉ dùng kiểm thử.

## Cấu trúc mã nguồn

```text
CoAP_Lab/
  bai1/
    coap_server_bai1.py
    coap_client_bai1.py
  bai2/
    sensor_server_bai2.py
    monitor_client_bai2.py
  bai3/
    light_server_bai3.py
    light_controller_bai3.py
    light_monitor_bai3.py
  common.py
  requirements.txt
  README.md
  evidence/                 # Log chạy thực tế và kết quả kiểm thử
  tests/verify_lab.py       # Kiểm thử tích hợp qua UDP
```

`common.py` dùng chung cấu hình, transport UDP IPv4 phù hợp Windows, xử lý timeout và đóng context. Khi nộp phải giữ file này cùng cả ba thư mục bài tập.

## Cài đặt và môi trường

Mở PowerShell tại thư mục `CoAP_Lab`. Với máy đã cài Python 3.10 trở lên:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Nếu hệ thống dùng Python Launcher, thay `python` bằng `py -3` ở lệnh tạo môi trường. Không cần kích hoạt môi trường hoặc thay đổi ExecutionPolicy; gọi thẳng `python.exe` như dưới đây.

**Trên workspace hiện tại**, môi trường đã được cài ở thư mục cha. Có thể chạy ngay từ `CoAP_Lab` bằng cách đặt biến ở **mỗi terminal**:

```powershell
$pythonExe = (Resolve-Path ..\.venv\Scripts\python.exe).Path
```

**Trên máy cài mới theo hai lệnh phía trên**, đặt biến ở mỗi terminal như sau:

```powershell
$pythonExe = (Resolve-Path .\.venv\Scripts\python.exe).Path
```

Các lệnh tiếp theo đều chạy từ `CoAP_Lab`. Mỗi chương trình hỗ trợ `--help`.

## IP cổng URI và tổ chức dữ liệu

| Bài | Thiết bị / tài nguyên | URI mặc định | Phương thức | Payload |
|---|---|---|---|---|
| 1 | Thông điệp | `coap://127.0.0.1:5683/iot/lab/message` | GET, POST | Văn bản UTF-8, Content-Format 0 |
| 2 | sensor01 / data | `coap://127.0.0.1:5683/iot/lab/sensor01/data` | GET | JSON, Content-Format 50 |
| 3 | light01 / status | `coap://127.0.0.1:5683/iot/lab/light01/status` | GET, PUT, Observe | JSON, Content-Format 50 |

`127.0.0.1` là địa chỉ loopback của `localhost`. Dùng IPv4 tường minh để tránh khác biệt phân giải IPv6 trên Windows. Cổng mặc định là **UDP 5683**. **Chạy lần lượt từng bài, dừng server bài trước bằng Ctrl+C** trước khi mở server bài tiếp theo vì cả ba dùng cùng địa chỉ/cổng. Muốn chạy đồng thời, truyền `--port 5684` hoặc `--port 5685` nhất quán cho server và các client tương ứng.

Chạy trên hai máy cùng mạng: xác định IPv4 của máy server bằng `ipconfig`, thêm `--host <IPv4-máy-server>` ở cả lệnh server và client. Máy server phải cho phép UDP cổng 5683 qua tường lửa. Server cần bind đúng địa chỉ IPv4 được gán cho máy, ví dụ `--host 192.168.1.10`.

## Bài 1 gửi nhận thông điệp

Terminal 1:

```powershell
& $pythonExe bai1/coap_server_bai1.py
```

Terminal 2:

```powershell
& $pythonExe bai1/coap_client_bai1.py
```

Client hỏi họ tên và mã sinh viên, gửi GET lấy lời chào rồi POST chuỗi `Xin chao tu CoAP Client - <mã sinh viên> - <họ tên>`. GET đầu tiên trả `2.05 Content`, POST thành công trả `2.04 Changed` và `Server da nhan thong diep`. Server in payload và thời điểm nhận có múi giờ.

Gửi nhiều lần bằng `--count 3`. Có thể truyền `--name "Họ tên thật" --student-id "Mã sinh viên thật"` để không nhập bàn phím. Server lưu thông điệp mới nhất trong RAM; GET tiếp theo trả thông điệp đã lưu. Khởi động lại server sẽ trở về lời chào ban đầu.

Log thực tế: [server](evidence/bai1_server.log), [client](evidence/bai1_client.log). Đã kiểm tra cả GET tài nguyên không tồn tại (`4.04 Not Found`), POST rỗng và UTF-8 lỗi (`4.00 Bad Request`).

## Bài 2 mô phỏng cảm biến

Terminal 1:

```powershell
& $pythonExe bai2/sensor_server_bai2.py
```

Terminal 2:

```powershell
& $pythonExe bai2/monitor_client_bai2.py
```

Server sinh dữ liệu ban đầu ngay khi khởi động, tự cập nhật sau mỗi **3 giây**, nhiệt độ trong **20–40 °C**, độ ẩm **30–80 %**. GET chỉ đọc dữ liệu mới nhất, không sinh lại dữ liệu. JSON gồm `device_id`, `temperature`, `humidity`, thêm `timestamp` có múi giờ.

Client gửi GET theo chu kỳ **3 giây** trong điều kiện phản hồi bình thường, in mã thiết bị, nhiệt độ, độ ẩm và thời điểm nhận. Nếu yêu cầu bị timeout lâu hơn chu kỳ, chương trình chờ yêu cầu đó kết thúc trước lần tiếp theo. Mặc định theo dõi đến Ctrl+C. Cảnh báo đúng hai điều kiện độc lập:

- Nhiệt độ **> 35 °C**: `CANH BAO: Nhiet do cao`.
- Độ ẩm **< 40 %**: `CANH BAO: Do am thap`.
- Nếu không vi phạm điều kiện nào: `Trang thai: Binh thuong`.

Các mở rộng đã triển khai: timestamp, nhiều cảm biến, chọn thiết bị, ghi CSV, thống kê số GET và thời gian phản hồi trung bình. Ví dụ:

```powershell
# Terminal server
& $pythonExe bai2/sensor_server_bai2.py --devices sensor01 sensor02 sensor03
# Terminal client
& $pythonExe bai2/monitor_client_bai2.py --device sensor02 --csv logs/sensor02.csv
```

Dùng `--count 3` nếu muốn tự dừng sau ba lần GET. Thống kê đếm số phản hồi CoAP thành công; client báo riêng payload JSON không hợp lệ. Log thực tế: [server](evidence/bai2_server.log), [client](evidence/bai2_client.log), [CSV](evidence/sensor_data.csv). Kiểm thử kiểm tra cả ranh giới 35 °C và 40 %, không phụ thuộc vào dữ liệu ngẫu nhiên để xác nhận cảnh báo.

## Bài 3 đèn thông minh và Observe

Mở ba terminal; chạy monitor trước khi điều khiển để thấy đầy đủ thay đổi.

Terminal 1:

```powershell
& $pythonExe bai3/light_server_bai3.py --log logs/light_changes.jsonl
```

Terminal 2:

```powershell
& $pythonExe bai3/light_monitor_bai3.py
```

Terminal 3:

```powershell
& $pythonExe bai3/light_controller_bai3.py
```

Nhập lần lượt `STATUS`, `ON`, `STATUS`, `OFF`, `EXIT`. Trạng thái ban đầu là **OFF**. `STATUS` gửi GET, `ON/OFF` gửi PUT và in mã phản hồi. Payload PUT:

```json
{"device_id": "light01", "command": "ON"}
```

Payload GET/Observe:

```json
{"device_id": "light01", "status": "ON"}
```

Server kế thừa `ObservableResource`, gọi `updated_state()` khi trạng thái thực sự đổi. Monitor chỉ gửi **một GET với Observe=0 để đăng ký**, nhận trạng thái ban đầu rồi dùng `async for` trên luồng thông báo Observe. Không có vòng lặp GET định kỳ. Mở thêm nhiều terminal monitor để cùng theo dõi. PUT `ON` khi đèn đã `ON` vẫn nhận xác nhận `2.04 Changed` nhưng không phát thông báo mới.

Monitor in mã thiết bị, trạng thái và thời điểm nhận đến Ctrl+C; khi thoát sẽ hủy Observe và đóng context. Không có timeout chờ thay đổi trạng thái vì đèn có thể đứng yên lâu; `--timeout` áp dụng lúc đăng ký ban đầu. Nếu server bị tắt đột ngột khi đèn đang đứng yên, monitor có thể vẫn chờ do chưa có gói tin mới; dùng Ctrl+C và khởi chạy lại sau khi server hoạt động.

JSON lỗi, sai thiết bị hoặc lệnh khác ON/OFF trả `4.00 Bad Request`; Content-Format khác JSON trả `4.15 Unsupported Content-Format`. Client điều khiển cũng kiểm tra lệnh bàn phím trước khi gửi. Lệnh điều khiển không phân biệt chữ hoa/thường ở giao diện nhập; payload giao thức dùng đúng ON/OFF.

Các mở rộng đã triển khai: nhiều observer, kiểm tra đầu vào, nhật ký JSON Lines, tùy chọn CON/NON cho controller. Mặc định dùng CON, thêm `--non` để gửi NON. Có thể chạy chuỗi lệnh không tương tác:

```powershell
& $pythonExe bai3/light_controller_bai3.py --commands ON STATUS OFF EXIT
& $pythonExe bai3/light_controller_bai3.py --non --commands STATUS EXIT
```

Log thực tế: [server](evidence/bai3_server.log), [controller ON](evidence/bai3_controller_ON.log), [controller OFF](evidence/bai3_controller_OFF.log), [monitor 1](evidence/bai3_monitor_1.log), [monitor 2](evidence/bai3_monitor_2.log), [NON](evidence/bai3_non.log), [nhật ký thay đổi](evidence/light_changes.jsonl).

## Kiểm thử và minh chứng kết quả

```powershell
& $pythonExe tests/verify_lab.py
```

Dừng các server đang chạy trước khi kiểm thử để giải phóng UDP 5683. Bộ kiểm thử tự chạy các chương trình server/client, gửi gói CoAP thật qua loopback, kiểm tra kết quả và lưu stdout vào `evidence/`. Mỗi lần chạy ghi lại log văn bản, nối thêm CSV và JSON Lines.

| Nhóm yêu cầu | Kết quả chạy |
|---|---|
| Bài 1 GET lời chào, POST thông tin, xác nhận, lưu thông điệp | PASS |
| Bài 1 URI sai, UTF-8 sai, POST rỗng | PASS |
| Bài 2 cập nhật và truy vấn 3 giây, JSON/Content-Format, CSV | PASS |
| Bài 2 nhiều cảm biến và các ranh giới cảnh báo | PASS |
| Bài 3 OFF ban đầu, PUT ON/OFF, GET trạng thái | PASS |
| Bài 3 hai chương trình monitor nhận Observe đồng thời | PASS |
| Bài 3 lặp lệnh giữ nguyên trạng thái không tạo thông báo | PASS |
| Bài 3 JSON, thiết bị, lệnh và Content-Format không hợp lệ | PASS |
| Bài 3 gửi NON và nhận phản hồi | PASS |
| Cả bốn client xử lý khi không có server | PASS |

Kết quả tổng hợp: [verification.txt](evidence/verification.txt). Log lỗi kết nối: [bài 1](evidence/timeout_bai1.log), [bài 2](evidence/timeout_bai2.log), [controller](evidence/timeout_controller.log), [Observe](evidence/timeout_observe.log).

Để tự thử lỗi, dừng server và chạy client với `--timeout 2`. Client thông báo lỗi và đóng tài nguyên hoặc tiếp tục vòng giám sát ở bài 2; không hiển thị traceback cho lỗi giao tiếp dự kiến. Ctrl+C dừng các chương trình chạy liên tục. Log server trong kiểm thử được đóng bằng terminate của tiến trình kiểm thử; khi chạy thủ công dùng Ctrl+C để thực hiện đóng context theo luồng bình thường.

## Đối chiếu đề và phạm vi mở rộng

Đã triển khai đầy đủ các mục Yêu cầu và Đánh giá của cả ba bài, đúng 7 chương trình và README có log minh chứng. Các mục “Gợi ý mở rộng” là tùy chọn trong đề. Bản này đã thêm lưu thông điệp gần nhất, nhiều POST, lỗi 4.04/timeout, timestamp cảm biến, nhiều cảm biến, CSV, thống kê GET, nhiều observer, kiểm tra lệnh, nhật ký trạng thái và CON/NON. Phần gợi ý mô phỏng thêm fan01/pump01 không được triển khai; bài 3 giữ thiết bị light01 theo yêu cầu chính.

## Nộp bài qua GitHub

Repository nộp bài: https://github.com/Djicz/IoT_ThucHanh_3. Bộ bài làm nằm trong thư mục `CoAP_Lab`, gồm mã nguồn, `common.py`, `requirements.txt`, `README.md`, `tests/` và `evidence/`. Không đưa môi trường `.venv` vào Git. Điền thông tin sinh viên/nhóm ở đầu README và chạy bài 1 với thông tin thật trước khi gửi URL repository cho giảng viên.

## Tài liệu tham khảo

- Đề thực hành: `Thực hành buổi 3 python coap.docx` trong thư mục workspace cha.
- [Ví dụ chính thức aiocoap](https://aiocoap.readthedocs.io/en/latest/examples.html).
- [ObservableResource và updated_state](https://aiocoap.readthedocs.io/en/latest/module/aiocoap.resource.html).
