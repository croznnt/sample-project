# -*- coding: utf-8 -*-
"""
Sinh bộ dữ liệu mẫu phục vụ tính KPI Quản trị công nghiệp.

Dữ liệu ở mức THÁNG, cho nhiều dây chuyền sản xuất, trong 2 năm.
Khi phân tích sẽ gộp (aggregate) lên mức QUÝ.

Chạy:  python generate_sample_data.py
Kết quả: data/raw/manufacturing_data.csv
"""

from __future__ import annotations

import os
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)  # cố định seed để tái lập được

# ---------------------------------------------------------------------------
# Cấu hình nhà máy giả định
# ---------------------------------------------------------------------------
YEARS = [2024, 2025]
MONTHS = list(range(1, 13))

# Mỗi dây chuyền có đặc tính khác nhau:
#   ideal_cycle_s : thời gian chu kỳ lý tưởng (giây/sp) -> quyết định năng lực
#   perf          : hệ số hiệu suất vận hành mục tiêu (Performance)
#   quality       : tỷ lệ chất lượng
#   avail         : khả năng sẵn sàng của thiết bị
#   price         : giá bán bình quân (đ/sp, quy đổi nghìn đồng)
LINES = {
    "Line-A (Dập ép)": dict(ideal_cycle_s=6.0, perf=0.92,
                            price=58.0, quality=0.985, avail=0.90),
    "Line-B (Hàn robot)": dict(ideal_cycle_s=9.5, perf=0.88,
                               price=92.0, quality=0.975, avail=0.86),
    "Line-C (Lắp ráp)": dict(ideal_cycle_s=4.2, perf=0.94,
                             price=44.0, quality=0.992, avail=0.93),
    "Line-D (Sơn & hoàn thiện)": dict(ideal_cycle_s=8.0, perf=0.85,
                                      price=70.0, quality=0.968, avail=0.83),
}

# Hệ số mùa vụ theo quý (Q4 cao điểm, Q1 thấp điểm)
QUARTER_SEASON = {1: 0.92, 2: 1.00, 3: 1.05, 4: 1.12}


def month_to_quarter(m: int) -> int:
    return (m - 1) // 3 + 1


def jitter(center: float, pct: float) -> float:
    """Trả về giá trị dao động quanh center +/- pct."""
    return center * (1 + RNG.uniform(-pct, pct))


def build() -> pd.DataFrame:
    rows = []
    for yi, year in enumerate(YEARS):
        # xu hướng cải tiến nhẹ qua từng năm (Kaizen)
        year_improve = 1 + 0.03 * yi
        for month in MONTHS:
            q = month_to_quarter(month)
            season = QUARTER_SEASON[q]
            for line, cfg in LINES.items():
                # --- Sản lượng & thời gian ---
                planned_time_h = round(jitter(600, 0.05), 1)   # giờ kế hoạch/tháng
                avail_ratio = min(0.98, cfg["avail"] * year_improve * jitter(1, 0.04))
                downtime_h = round(planned_time_h * (1 - avail_ratio), 1)
                run_time_h = planned_time_h - downtime_h

                # Năng lực lý thuyết trong thời gian chạy máy
                theoretical = run_time_h * 3600 / cfg["ideal_cycle_s"]
                # Sản lượng thực = năng lực × hệ số hiệu suất (có mùa vụ & Kaizen)
                perf_factor = min(
                    0.99,
                    cfg["perf"] * (1 + 0.02 * yi) * (0.97 + 0.06 * (season - 0.92)) *
                    jitter(1, 0.03),
                )
                total_units = int(theoretical * perf_factor)

                # --- Chất lượng ---
                q_rate = min(0.999, cfg["quality"] * year_improve * jitter(1, 0.01))
                units_scrapped = int(total_units * (1 - q_rate))
                units_reworked = int(total_units * jitter(0.012, 0.3))
                good_units = total_units - units_scrapped

                # --- Nguyên vật liệu ---
                mat_per_unit = jitter(1.15, 0.03)  # kg/sp
                material_input_kg = round(total_units * mat_per_unit, 0)
                material_scrapped_kg = round(
                    material_input_kg * jitter(0.025, 0.25), 0)

                # --- Bảo trì ---
                downtime_events = int(max(1, RNG.poisson(6) * (2 - avail_ratio)))
                repair_time_h = round(downtime_h * jitter(0.55, 0.2), 1)

                # --- Lao động ---
                operators = RNG.integers(14, 26)
                labor_hours = int(operators * jitter(176, 0.05))

                # --- Năng lượng ---
                energy_kwh = int(total_units * jitter(0.85, 0.08))

                # --- Tài chính ---
                price = jitter(cfg["price"], 0.03)
                revenue = round(good_units * price, 0)
                material_cost = round(material_input_kg * jitter(14.5, 0.05), 0)
                labor_cost = round(labor_hours * jitter(62.0, 0.05), 0)
                overhead_cost = round(revenue * jitter(0.18, 0.1), 0)
                energy_cost = round(energy_kwh * jitter(2.8, 0.05), 0)

                # --- Chuỗi cung ứng / giao hàng ---
                orders_total = int(jitter(120, 0.1))
                otd_rate = min(0.99, jitter(0.93, 0.05) * year_improve)
                orders_on_time = int(orders_total * otd_rate)
                inventory_avg_value = round(material_cost * jitter(1.4, 0.1), 0)
                cogs = material_cost + labor_cost + energy_cost + overhead_cost

                # --- An toàn ---
                safety_incidents = int(RNG.poisson(0.25))

                rows.append(dict(
                    year=year,
                    quarter=f"Q{q}",
                    month=month,
                    line=line,
                    planned_time_h=planned_time_h,
                    downtime_h=downtime_h,
                    ideal_cycle_s=cfg["ideal_cycle_s"],
                    total_units=total_units,
                    good_units=good_units,
                    units_scrapped=units_scrapped,
                    units_reworked=units_reworked,
                    material_input_kg=material_input_kg,
                    material_scrapped_kg=material_scrapped_kg,
                    downtime_events=downtime_events,
                    repair_time_h=repair_time_h,
                    labor_hours=labor_hours,
                    energy_kwh=energy_kwh,
                    revenue=revenue,
                    material_cost=material_cost,
                    labor_cost=labor_cost,
                    energy_cost=energy_cost,
                    overhead_cost=overhead_cost,
                    cogs=cogs,
                    orders_total=orders_total,
                    orders_on_time=orders_on_time,
                    inventory_avg_value=inventory_avg_value,
                    safety_incidents=safety_incidents,
                ))
    df = pd.DataFrame(rows)
    return df


def main() -> None:
    out_dir = os.path.join(os.path.dirname(__file__), "raw")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "manufacturing_data.csv")
    df = build()
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"Đã tạo {len(df)} dòng dữ liệu -> {out_path}")
    print(df.head(8).to_string(index=False))


if __name__ == "__main__":
    main()
