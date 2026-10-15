# -*- coding: utf-8 -*-
"""
Định nghĩa danh mục KPI, đơn vị, mục tiêu và ngưỡng đánh giá.

Mỗi KPI có:
  - label      : tên hiển thị tiếng Việt
  - unit       : đơn vị
  - fmt        : định dạng hiển thị ('pct', 'num', 'money', 'ratio', ...)
  - higher_is_better : True nếu càng cao càng tốt
  - target     : ngưỡng mục tiêu (Tốt)
  - warn       : ngưỡng cảnh báo (Trung bình)
  - group      : nhóm KPI
"""

# Trạng thái đánh giá
GOOD = "Đạt"
WARN = "Cảnh báo"
BAD = "Chưa đạt"

STATUS_COLOR = {
    GOOD: "#16a34a",   # xanh
    WARN: "#d97706",   # cam
    BAD: "#dc2626",    # đỏ
}

KPI_DEFS = {
    # --- OEE ---
    "oee": dict(label="OEE (Hiệu suất thiết bị tổng thể)", unit="%", fmt="pct",
                higher_is_better=True, target=75, warn=60, group="OEE"),
    "availability": dict(label="Availability (Khả năng sẵn sàng)", unit="%", fmt="pct",
                         higher_is_better=True, target=90, warn=80, group="OEE"),
    "performance": dict(label="Performance (Hiệu suất vận hành)", unit="%", fmt="pct",
                        higher_is_better=True, target=95, warn=85, group="OEE"),
    "quality": dict(label="Quality (Tỷ lệ chất lượng)", unit="%", fmt="pct",
                    higher_is_better=True, target=99, warn=97, group="OEE"),

    # --- Chất lượng ---
    "fpy": dict(label="First Pass Yield (Tỷ lệ đạt lần đầu)", unit="%", fmt="pct",
                higher_is_better=True, target=97, warn=93, group="Chất lượng"),
    "scrap_rate": dict(label="Scrap Rate (Tỷ lệ phế liệu NVL)", unit="%", fmt="pct",
                       higher_is_better=False, target=3, warn=5, group="Chất lượng"),
    "defect_rate": dict(label="Defect Rate (Tỷ lệ lỗi sản phẩm)", unit="%", fmt="pct",
                        higher_is_better=False, target=1.5, warn=3, group="Chất lượng"),

    # --- Bảo trì ---
    "mtbf": dict(label="MTBF (Thời gian trung bình giữa các lần hỏng)", unit="giờ",
                 fmt="num", higher_is_better=True, target=80, warn=50, group="Bảo trì"),
    "mttr": dict(label="MTTR (Thời gian sửa chữa trung bình)", unit="giờ",
                 fmt="num", higher_is_better=False, target=4, warn=8, group="Bảo trì"),

    # --- Năng suất ---
    "labor_productivity": dict(label="Năng suất lao động", unit="sp/giờ công",
                               fmt="num", higher_is_better=True, target=80, warn=65,
                               group="Năng suất"),
    "energy_per_unit": dict(label="Tiêu hao năng lượng/sp", unit="kWh/sp",
                            fmt="num3", higher_is_better=False, target=0.85, warn=1.0,
                            group="Năng suất"),

    # --- Tài chính ---
    "gross_margin": dict(label="Biên lợi nhuận gộp", unit="%", fmt="pct",
                         higher_is_better=True, target=25, warn=15, group="Tài chính"),
    "cost_per_unit": dict(label="Chi phí/sản phẩm", unit="đ/sp", fmt="money",
                          higher_is_better=False, target=40, warn=55, group="Tài chính"),

    # --- Chuỗi cung ứng ---
    "otd": dict(label="On-Time Delivery (Giao hàng đúng hạn)", unit="%", fmt="pct",
                higher_is_better=True, target=95, warn=90, group="Chuỗi cung ứng"),
    "inventory_turnover": dict(label="Vòng quay tồn kho (năm)", unit="lần", fmt="num",
                               higher_is_better=True, target=8, warn=5,
                               group="Chuỗi cung ứng"),

    # --- An toàn ---
    "safety_incidents": dict(label="Số sự cố an toàn", unit="vụ", fmt="int",
                             higher_is_better=False, target=0, warn=2, group="An toàn"),
}

GROUPS = ["OEE", "Chất lượng", "Bảo trì", "Năng suất", "Tài chính",
          "Chuỗi cung ứng", "An toàn"]


def evaluate(key: str, value: float) -> str:
    """Trả về trạng thái GOOD/WARN/BAD cho một giá trị KPI."""
    d = KPI_DEFS[key]
    if value is None:
        return BAD
    if d["higher_is_better"]:
        if value >= d["target"]:
            return GOOD
        if value >= d["warn"]:
            return WARN
        return BAD
    else:  # càng thấp càng tốt
        if value <= d["target"]:
            return GOOD
        if value <= d["warn"]:
            return WARN
        return BAD


def format_value(key: str, value: float) -> str:
    """Định dạng hiển thị giá trị theo loại KPI."""
    if value is None:
        return "–"
    fmt = KPI_DEFS[key]["fmt"]
    if fmt == "pct":
        return f"{value:.1f}%"
    if fmt == "int":
        return f"{int(round(value))}"
    if fmt == "num":
        return f"{value:,.1f}"
    if fmt == "num3":
        return f"{value:.3f}"
    if fmt == "money":
        return f"{value:,.1f}"
    return f"{value:,.2f}"
