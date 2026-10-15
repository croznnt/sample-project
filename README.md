# 🏭 Dashboard KPI Quản trị công nghiệp (Streamlit)

Bộ dữ liệu mẫu + ứng dụng **Streamlit** giúp **tính, hiển thị và đánh giá KPI
sản xuất theo từng quý** cho một nhà máy giả định gồm 4 dây chuyền.

Phù hợp cho **giảng dạy / đồ án môn Quản trị công nghiệp**: sinh viên có thể
chạy ngay, xem cách KPI được tính và tự mở rộng thêm chỉ số.

---

## Mục lục
1. [Cấu trúc thư mục](#1-cấu-trúc-thư-mục)
2. [Cài đặt & chạy](#2-cài-đặt--chạy)
3. [Hướng dẫn sử dụng giao diện](#3-hướng-dẫn-sử-dụng-giao-diện)
4. [Bộ dữ liệu mẫu](#4-bộ-dữ-liệu-mẫu)
5. [Các KPI & công thức](#5-các-kpi--công-thức)
6. [Tùy chỉnh nhanh](#6-tùy-chỉnh-nhanh)
7. [Hướng phát triển](#7-hướng-phát-triển)
8. [Xử lý sự cố thường gặp](#8-xử-lý-sự-cố-thường-gặp)

---

## 1. Cấu trúc thư mục

```
streamlit_dashboard/
├── app.py                         # Ứng dụng Streamlit (giao diện chính, 5 tab)
├── requirements.txt               # Thư viện cần cài
├── README.md                      # Tài liệu này
├── .streamlit/
│   └── config.toml                # Giao diện / theme / tắt usage stats
├── data/
│   ├── generate_sample_data.py    # Script sinh dữ liệu mẫu (seed cố định → tái lập)
│   └── raw/
│       └── manufacturing_data.csv # Dữ liệu mẫu (96 dòng: 2 năm × 12 tháng × 4 line)
└── src/
    ├── __init__.py
    ├── targets.py                 # Danh mục KPI, mục tiêu & ngưỡng đánh giá
    ├── kpi.py                     # Công thức tính KPI
    └── data_loader.py             # Nạp dữ liệu, gộp theo quý, chấm trạng thái
```

**Vai trò từng lớp** (tách bạch dữ liệu – logic – giao diện):

| Lớp | File | Nhiệm vụ |
|-----|------|----------|
| Dữ liệu | `data/` | Sinh và lưu dữ liệu thô |
| Logic | `src/kpi.py`, `src/targets.py`, `src/data_loader.py` | Tính KPI, định nghĩa mục tiêu, gộp theo quý |
| Giao diện | `app.py` | Hiển thị, lọc, vẽ biểu đồ, đánh giá |

> Nhờ tách lớp, bạn có thể dùng lại `src/` để tính KPI trong notebook, script
> khác hoặc API mà không cần Streamlit.

---

## 2. Cài đặt & chạy

Yêu cầu: **Python 3.9+**.

```bash
# 1) Vào thư mục dự án
cd streamlit_dashboard

# 2) (Khuyến nghị) tạo môi trường ảo
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3) Cài thư viện
pip install -r requirements.txt

# 4) (Tùy chọn) sinh lại dữ liệu mẫu
python data/generate_sample_data.py

# 5) Chạy ứng dụng
streamlit run app.py
```

Trình duyệt tự mở tại `http://localhost:8501`. Dừng app bằng **Ctrl + C**.

> ⚠️ Hãy chạy lệnh `streamlit run` **từ bên trong thư mục `streamlit_dashboard`**
> để app đọc đúng file `.streamlit/config.toml` và tìm thấy dữ liệu.

---

## 3. Hướng dẫn sử dụng giao diện

**Thanh bên (sidebar):**
- *Dây chuyền sản xuất* — chọn một hoặc nhiều dây chuyền để lọc.
- *Quý phân tích* — chọn quý để xem thẻ điểm và so sánh dây chuyền.

**5 tab chính:**

| Tab | Công dụng |
|-----|-----------|
| 📊 **Thẻ điểm quý** | Toàn bộ KPI của quý đã chọn, có badge 🟢 Đạt / 🟠 Cảnh báo / 🔴 Chưa đạt và mức tăng/giảm so với quý trước |
| 📈 **Xu hướng theo quý** | Biểu đồ cột qua các quý, kèm đường *mục tiêu* và *ngưỡng cảnh báo* |
| 🏭 **So sánh dây chuyền** | Đối chiếu các dây chuyền trong cùng một quý theo 1 chỉ số |
| 📋 **Bảng đánh giá** | Bảng KPI tô màu theo trạng thái; tải xuống CSV |
| 🗃️ **Dữ liệu gốc** | Xem & tải dữ liệu thô theo tháng |

**Ý nghĩa màu đánh giá:** 🟢 đạt mục tiêu · 🟠 trong khoảng cảnh báo · 🔴 dưới ngưỡng.

---

## 4. Bộ dữ liệu mẫu

Mức chi tiết: **tháng × dây chuyền** (gộp lên **quý** khi phân tích).
4 dây chuyền: *Dập ép, Hàn robot, Lắp ráp, Sơn & hoàn thiện*.
Dữ liệu có **mùa vụ** (Q4 cao điểm) và **xu hướng cải tiến** qua từng năm (Kaizen).

| Cột | Ý nghĩa |
|-----|---------|
| `year`, `quarter`, `month`, `line` | Kỳ và dây chuyền |
| `planned_time_h`, `downtime_h` | Thời gian kế hoạch / dừng máy (giờ) |
| `ideal_cycle_s` | Chu kỳ lý tưởng (giây/sp) |
| `total_units`, `good_units`, `units_scrapped`, `units_reworked` | Sản lượng & chất lượng |
| `material_input_kg`, `material_scrapped_kg` | Nguyên vật liệu |
| `downtime_events`, `repair_time_h` | Dữ liệu bảo trì (MTBF/MTTR) |
| `labor_hours`, `energy_kwh` | Lao động & năng lượng |
| `revenue`, `material_cost`, `labor_cost`, `energy_cost`, `overhead_cost`, `cogs` | Tài chính |
| `orders_total`, `orders_on_time` | Giao hàng đúng hạn |
| `inventory_avg_value` | Tồn kho bình quân |
| `safety_incidents` | Sự cố an toàn |

---

## 5. Các KPI & công thức

| Nhóm | KPI | Công thức tóm tắt |
|------|-----|-------------------|
| **OEE** | Availability | (Kế hoạch − Dừng máy) / Kế hoạch |
| | Performance | (SL thực × Chu kỳ lý tưởng) / Thời gian chạy |
| | Quality | SL đạt / Tổng SL |
| | **OEE** | Availability × Performance × Quality |
| **Chất lượng** | First Pass Yield | (Tổng − Phế − Tái chế) / Tổng |
| | Scrap Rate | NVL phế / NVL đầu vào |
| | Defect Rate | SL phế / Tổng SL |
| **Bảo trì** | MTBF | Giờ vận hành / Số lần hỏng |
| | MTTR | Giờ sửa chữa / Số lần hỏng |
| **Năng suất** | NS lao động | Tổng SL / Giờ công |
| | Năng lượng/sp | kWh / Tổng SL |
| **Tài chính** | Biên LN gộp | (Doanh thu − COGS) / Doanh thu |
| | Chi phí/sp | COGS / SL đạt |
| **Chuỗi cung ứng** | On-Time Delivery | Đơn đúng hạn / Tổng đơn |
| | Vòng quay tồn kho | COGS kỳ / Tồn kho bình quân × hệ số quy năm |
| **An toàn** | Sự cố an toàn | Tổng số vụ |

Chi tiết trong [`src/kpi.py`](src/kpi.py); mục tiêu & ngưỡng trong [`src/targets.py`](src/targets.py).

> **Lưu ý quan trọng:** các tỷ lệ được tính bằng cách **cộng dồn số liệu thô rồi
> mới chia** (theo trọng số sản lượng), *không* lấy trung bình cộng các tỷ lệ
> tháng — cho kết quả quý chính xác hơn.

---

## 6. Tùy chỉnh nhanh

**Đổi mục tiêu / ngưỡng đánh giá** → sửa `target` và `warn` trong
[`src/targets.py`](src/targets.py):
```python
"oee": dict(label="OEE ...", unit="%", fmt="pct",
            higher_is_better=True, target=75, warn=60, group="OEE"),
```

**Thêm một KPI mới** (3 bước):
1. Thêm công thức trong `compute_kpis()` ở [`src/kpi.py`](src/kpi.py).
2. Khai báo định nghĩa + mục tiêu trong `KPI_DEFS` ở [`src/targets.py`](src/targets.py).
3. Xong — app tự động hiển thị KPI mới ở mọi tab.

**Dùng dữ liệu thật** → thay file `data/raw/manufacturing_data.csv` bằng dữ liệu
của bạn (giữ đúng tên cột), hoặc sửa đường dẫn `DEFAULT_CSV` trong
[`src/data_loader.py`](src/data_loader.py).

**Đổi giao diện / màu** → sửa `.streamlit/config.toml` và bảng màu `PALETTE`,
`STATUS_COLOR` trong `app.py` / `targets.py`.

---

## 7. Hướng phát triển

Gợi ý mở rộng theo mức độ tăng dần — dùng làm ý tưởng cho đồ án:

**Mức cơ bản**
- [ ] Thêm bộ lọc theo **năm** và **khoảng thời gian** (từ quý → đến quý).
- [ ] Thêm KPI mới: Takt time, Cycle time thực tế, Tỷ lệ tồn kho WIP, Giá trị hao hụt.
- [ ] Xuất **báo cáo PDF/Excel** cho từng quý (dùng `reportlab` / `openpyxl`).
- [ ] Thêm trang **nhập liệu thủ công** (form Streamlit) để ghi thêm số liệu tháng mới.

**Mức trung bình**
- [ ] Kết nối **cơ sở dữ liệu** (SQLite/PostgreSQL) thay cho CSV, dùng `SQLAlchemy`.
- [ ] **Cảnh báo tự động**: gửi email/Slack khi KPI xuống dưới ngưỡng đỏ.
- [ ] **So sánh mục tiêu vs thực tế** dạng biểu đồ gauge, thêm cột chênh lệch %.
- [ ] Phân quyền người dùng (xem / chỉnh) bằng `streamlit-authenticator`.
- [ ] Thêm **KPI tùy biến** qua giao diện (người dùng tự định nghĩa công thức).

**Mức nâng cao**
- [ ] **Dự báo** KPI quý tới bằng mô hình chuỗi thời gian (Prophet / ARIMA / hồi quy).
- [ ] Phân tích **nguyên nhân gốc** downtime (Pareto, biểu đồ xương cá).
- [ ] Tích hợp dữ liệu **thời gian thực** từ máy (MQTT / OPC-UA / API MES).
- [ ] **Triển khai online**: Streamlit Community Cloud, Docker, hoặc nội bộ công ty.
- [ ] Mô phỏng **what-if**: thay đổi đầu vào để xem KPI thay đổi thế nào.

**Gợi ý triển khai nhanh lên Streamlit Cloud**
1. Đẩy thư mục này lên một repo GitHub.
2. Vào [share.streamlit.io](https://share.streamlit.io), chọn repo và file `app.py`.
3. Streamlit tự cài theo `requirements.txt` và cấp link công khai.

---

## 8. Xử lý sự cố thường gặp

| Hiện tượng | Nguyên nhân / cách xử lý |
|------------|--------------------------|
| `ModuleNotFoundError: streamlit` | Chưa cài thư viện → chạy `pip install -r requirements.txt` |
| `FileNotFoundError: manufacturing_data.csv` | Chạy sai thư mục → `cd streamlit_dashboard` rồi chạy lại; hoặc chạy `python data/generate_sample_data.py` |
| Dòng *"Collecting usage statistics..."* | **Không phải lỗi** — chỉ là thông báo. Đã tắt sẵn trong `.streamlit/config.toml` |
| App không mở trình duyệt | Mở thủ công `http://localhost:8501` |
| Cổng 8501 bị chiếm | Chạy `streamlit run app.py --server.port 8600` |

---

*Dự án mẫu phục vụ học tập môn Quản trị công nghiệp. Mọi số liệu là giả định.*
