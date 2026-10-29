# Thực hành buổi 3 lập trình Python với giao thức CoAP

## 1. Thông tin nhóm thực hiện

| STT | Họ và tên | Mã sinh viên |
|---|---|---|
| 1 | Lê Huy Đức | B23DCCN169 |
| 2 | Trương Khánh Hợp | B23DCCN351 |

Repository nộp bài: [Djicz/IoT_ThucHanh_3](https://github.com/Djicz/IoT_ThucHanh_3).

## 2. Cấu trúc thư mục

```text
IoT_ThucHanh_3/
|
|-- bai1/
|   |-- coap_server_bai1.py
|   |-- coap_client_bai1.py
|
|-- bai2/
|   |-- sensor_server_bai2.py
|   |-- monitor_client_bai2.py
|
|-- bai3/
|   |-- light_server_bai3.py
|   |-- light_controller_bai3.py
|   |-- light_monitor_bai3.py
|
|-- README.md
```

Mỗi file Python là một chương trình chạy độc lập. Minh chứng chạy chương trình được ghi ở mục 7 của README.

## 3. Phiên bản Python và thư viện sử dụng

- Python 3.12.14, đã chạy thử trên Windows.
- Thư viện ngoài: aiocoap 0.4.17.
- Các thư viện chuẩn dùng trong mã nguồn gồm `asyncio`, `argparse`, `json`, `datetime`, `random`, `time`, `math`, `csv`, `pathlib`, `contextlib`; không cần cài thêm.
- Giao thức CoAP qua UDP, cổng mặc định 5683. Không cần MQTT Broker hoặc RabbitMQ.

## 4. Cách cài đặt môi trường

Cài Python 3.10 trở lên, chọn thêm Python vào PATH khi cài trên Windows. Tải hoặc clone repository, mở terminal tại thư mục `CoAP_Lab` rồi chạy:

```powershell
python --version
python -m pip install aiocoap==0.4.17
```

Nếu máy dùng Python Launcher, có thể thay `python` bằng `py -3` trong các lệnh cài đặt và chạy. Nếu dùng môi trường ảo, chọn Python của môi trường đã cài aiocoap.

## 5. Cách chạy từng chương trình

Tất cả lệnh dưới đây thực hiện từ thư mục `CoAP_Lab`. Mỗi terminal phải dùng cùng môi trường Python đã cài aiocoap. Chạy lần lượt từng bài và nhấn **Ctrl+C** để dừng server bài trước, vì cả ba server đều dùng UDP cổng 5683.

### Bài 1 gửi và nhận thông điệp CoAP

Terminal 1 chạy server:

```powershell
python bai1/coap_server_bai1.py
```

Terminal 2 chạy client:

```powershell
python bai1/coap_client_bai1.py
```

Nhập họ tên và mã sinh viên khi được hỏi. Client thực hiện GET để nhận lời chào, sau đó POST thông điệp chứa nội dung chào mừng, mã sinh viên và họ tên. Server hiển thị thông điệp, thời điểm nhận và trả xác nhận.

Ví dụ chạy bằng thông tin thành viên nhóm:

```powershell
python bai1/coap_client_bai1.py --name "Lê Huy Đức" --student-id B23DCCN169
python bai1/coap_client_bai1.py --name "Trương Khánh Hợp" --student-id B23DCCN351
```

### Bài 2 mô phỏng cảm biến nhiệt độ và độ ẩm

Terminal 1 chạy server:

```powershell
python bai2/sensor_server_bai2.py
```

Terminal 2 chạy client giám sát:

```powershell
python bai2/monitor_client_bai2.py
```

Server tự cập nhật nhiệt độ và độ ẩm mỗi **3 giây**. Nhiệt độ ngẫu nhiên trong khoảng 20–40 °C, độ ẩm trong khoảng 30–80 %. Client GET dữ liệu JSON mỗi **3 giây**, hiển thị mã thiết bị, nhiệt độ, độ ẩm và thời điểm nhận. Nhiệt độ **> 35 °C** hiển thị `CANH BAO: Nhiet do cao`; độ ẩm **< 40 %** hiển thị `CANH BAO: Do am thap`. Hai điều kiện được kiểm tra độc lập. Nhấn **Ctrl+C** để kết thúc giám sát.

### Bài 3 giám sát và điều khiển đèn thông minh bằng CoAP Observe

Terminal 1 chạy server:

```powershell
python bai3/light_server_bai3.py
```

Terminal 2 chạy client giám sát trước khi điều khiển:

```powershell
python bai3/light_monitor_bai3.py
```

Terminal 3 chạy client điều khiển:

```powershell
python bai3/light_controller_bai3.py
```

Nhập lệnh tại terminal điều khiển:

| Lệnh | Chức năng |
|---|---|
| ON | Gửi PUT bật đèn |
| OFF | Gửi PUT tắt đèn |
| STATUS | Gửi GET lấy trạng thái hiện tại |
| EXIT | Kết thúc client điều khiển |

Đèn khởi tạo ở trạng thái **OFF**. Thử lần lượt `STATUS`, `ON`, `STATUS`, `OFF`, `EXIT`. Client giám sát đăng ký **CoAP Observe**, nhận trạng thái ban đầu và các thông báo khi trạng thái thực sự thay đổi; không sử dụng GET định kỳ. Có thể chạy đồng thời nhiều client giám sát. Nhấn **Ctrl+C** để dừng giám sát và server.

## 6. Địa chỉ IP cổng và URI tài nguyên CoAP

| Bài | Địa chỉ IP | Cổng UDP | URI | Phương thức |
|---|---|---|---|---|
| 1 | 127.0.0.1 | 5683 | `coap://127.0.0.1:5683/iot/lab/message` | GET, POST |
| 2 | 127.0.0.1 | 5683 | `coap://127.0.0.1:5683/iot/lab/sensor01/data` | GET |
| 3 | 127.0.0.1 | 5683 | `coap://127.0.0.1:5683/iot/lab/light01/status` | GET, PUT, Observe |

`127.0.0.1` là địa chỉ IPv4 loopback tương ứng với `localhost` trong đề. Khi server và client chạy trên hai máy, thêm `--host <IPv4 máy server>` vào cả lệnh server và các lệnh client, đồng thời cho phép UDP cổng 5683 qua tường lửa máy server. Có thể đổi cổng bằng `--port`, nhưng server và client phải dùng cùng cổng. Các client dùng `--timeout 5` mặc định để giới hạn thời gian chờ phản hồi ban đầu; bài 2 tiếp tục thử ở các chu kỳ sau khi gặp lỗi.

Bài 1 dùng payload văn bản UTF-8. Bài 2 và bài 3 dùng JSON với **Content-Format 50 (application/json)**. Payload PUT điều khiển đèn:

```json
{"device_id": "light01", "command": "ON"}
```

Payload trạng thái GET/Observe:

```json
{"device_id": "light01", "status": "ON"}
```

## 7. Kết quả đạt được và log minh chứng

Các log dưới đây trích từ lần chạy thực tế trên Windows bằng Python 3.12.14, aiocoap 0.4.17, qua UDP tại `127.0.0.1:5683`.

### Bài 1

Server khởi tạo thành công; client GET nhận lời chào với mã **2.05 Content**, POST thông tin sinh viên nhận mã **2.04 Changed**. Server hiển thị payload và thời điểm nhận. Đã chạy client với thông tin của cả hai thành viên.

Client của Lê Huy Đức:

```text
Sending GET request...
URI: coap://127.0.0.1:5683/iot/lab/message
Code: 2.05 Content
Payload: Xin chao tu CoAP Server
Sending POST request...
Payload: Xin chao tu CoAP Client - B23DCCN169 - Lê Huy Đức
Code: 2.04 Changed
Payload: Server da nhan thong diep
```

Trích log server nhận thông điệp của Trương Khánh Hợp:

```text
POST request received:
Payload: Xin chao tu CoAP Client - B23DCCN351 - Trương Khánh Hợp
Time: 2026-10-29T14:22:32+07:00
```

### Bài 2

Server trả dữ liệu mới nhất bằng JSON đúng Content-Format. Client truy vấn và nhận dữ liệu cách nhau 3 giây, phân tích và hiển thị đúng các trường, phát cảnh báo theo giá trị đo.

```text
Code: 2.05 Content
Payload: {"device_id": "sensor01", "temperature": 36.9, "humidity": 44.4, "timestamp": "2026-10-29T14:22:32+07:00"}
[2026-10-29T14:22:32+07:00] Received sensor data
Device: sensor01
Temperature: 36.9 C
Humidity: 44.4 %
CANH BAO: Nhiet do cao
------------------------------
Code: 2.05 Content
Payload: {"device_id": "sensor01", "temperature": 26.0, "humidity": 59.8, "timestamp": "2026-10-29T14:22:35+07:00"}
[2026-10-29T14:22:35+07:00] Received sensor data
Device: sensor01
Temperature: 26.0 C
Humidity: 59.8 %
Trang thai: Binh thuong
------------------------------
```

Kiểm tra thêm các ranh giới cảnh báo: 35 °C và 40 % không cảnh báo; 35.1 °C phát cảnh báo nhiệt độ cao; 39.9 % phát cảnh báo độ ẩm thấp; nếu cùng vi phạm sẽ hiển thị cả hai cảnh báo.

### Bài 3

Controller GET/PUT thành công, đèn chuyển **OFF → ON → OFF**. Hai client giám sát cùng đăng ký Observe và nhận được thông báo. Gửi lại lệnh giữ nguyên trạng thái không tạo thông báo mới.

Trích log controller bật đèn và truy vấn trạng thái:

```text
Sending PUT request...
Code: 2.04 Changed
Payload: {"device_id": "light01", "status": "ON"}
Da bat den light01
Sending GET request...
Code: 2.05 Content
Payload: {"device_id": "light01", "status": "ON"}
```

Log client giám sát:

```text
Registering CoAP Observe...
[2026-10-29T14:22:39+07:00] Initial State
Device: light01
Status: OFF
Observe registration successful
[2026-10-29T14:22:40+07:00] State Updated
Device: light01
Status: ON
[2026-10-29T14:22:40+07:00] State Updated
Device: light01
Status: OFF
```

### Xử lý lỗi

Đã kiểm tra URI không tồn tại trả **4.04 Not Found**; POST rỗng hoặc sai UTF-8 trả **4.00 Bad Request**; PUT đèn có JSON, mã thiết bị hoặc lệnh sai trả **4.00 Bad Request**; sai Content-Format trả **4.15 Unsupported Content-Format**. Client điều khiển báo lỗi nếu nhập lệnh ngoài ON/OFF/STATUS/EXIT. Cả bốn client xử lý được lỗi giao tiếp khi server không hoạt động.

Trích log client giám sát khi không có server:

```text
Loi ket noi/timeout: NetworkError: Network error: NetworkError
GET requests: 1; responses: 0; average response: 0.0000 s
```
