# -*- coding: utf-8 -*-
"""
Hàm tính các chỉ số KPI từ dữ liệu đã gộp (tổng theo quý / dây chuyền).

Tất cả hàm nhận một dict/Series đã CỘNG DỒN các cột thô và trả về
giá trị KPI. Nhờ cộng dồn trước rồi mới tính tỷ lệ, các chỉ số dạng
tỷ lệ được tính đúng theo trọng số sản lượng (không lấy trung bình cộng
các tỷ lệ tháng).
"""

from __future__ import annotations


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def compute_kpis(agg: dict) -> dict:
    """Nhận tổng các cột thô, trả về dict {kpi_key: value}."""
    planned = agg["planned_time_h"]
    downtime = agg["downtime_h"]
    run_time = planned - downtime
    total = agg["total_units"]
    good = agg["good_units"]
    scrapped = agg["units_scrapped"]
    reworked = agg["units_reworked"]
    ideal_cycle = agg["ideal_cycle_s"]  # trung bình có trọng số (xem data_loader)

    # --- OEE ---
    availability = _safe_div(run_time, planned) * 100
    # Performance = (sản lượng thực × chu kỳ lý tưởng) / thời gian chạy
    performance = _safe_div(total * ideal_cycle, run_time * 3600) * 100
    performance = min(performance, 100.0)
    quality = _safe_div(good, total) * 100
    oee = availability / 100 * performance / 100 * quality / 100 * 100

    # --- Chất lượng ---
    fpy = _safe_div(total - scrapped - reworked, total) * 100
    scrap_rate = _safe_div(agg["material_scrapped_kg"], agg["material_input_kg"]) * 100
    defect_rate = _safe_div(scrapped, total) * 100

    # --- Bảo trì ---
    events = agg["downtime_events"]
    mtbf = _safe_div(run_time, events)       # giờ vận hành / số lần hỏng
    mttr = _safe_div(agg["repair_time_h"], events)

    # --- Năng suất ---
    labor_productivity = _safe_div(total, agg["labor_hours"])
    energy_per_unit = _safe_div(agg["energy_kwh"], total)

    # --- Tài chính ---
    revenue = agg["revenue"]
    cogs = agg["cogs"]
    gross_margin = _safe_div(revenue - cogs, revenue) * 100
    cost_per_unit = _safe_div(cogs, good)

    # --- Chuỗi cung ứng ---
    otd = _safe_div(agg["orders_on_time"], agg["orders_total"]) * 100
    # Vòng quay tồn kho quy năm: (COGS kỳ / tồn kho bình quân) × (4 quý)
    inventory_turnover = _safe_div(cogs, agg["inventory_avg_value"]) * agg.get("_quarters_factor", 4)

    return {
        "oee": oee,
        "availability": availability,
        "performance": performance,
        "quality": quality,
        "fpy": fpy,
        "scrap_rate": scrap_rate,
        "defect_rate": defect_rate,
        "mtbf": mtbf,
        "mttr": mttr,
        "labor_productivity": labor_productivity,
        "energy_per_unit": energy_per_unit,
        "gross_margin": gross_margin,
        "cost_per_unit": cost_per_unit,
        "otd": otd,
        "inventory_turnover": inventory_turnover,
        "safety_incidents": agg["safety_incidents"],
    }
