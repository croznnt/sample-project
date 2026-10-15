# -*- coding: utf-8 -*-
"""
Nạp dữ liệu thô và gộp (aggregate) lên mức quý / dây chuyền để tính KPI.
"""

from __future__ import annotations

import os
import pandas as pd

from .kpi import compute_kpis
from . import targets

# Các cột cần CỘNG DỒN khi gộp
SUM_COLS = [
    "planned_time_h", "downtime_h", "total_units", "good_units",
    "units_scrapped", "units_reworked", "material_input_kg",
    "material_scrapped_kg", "downtime_events", "repair_time_h",
    "labor_hours", "energy_kwh", "revenue", "material_cost",
    "labor_cost", "energy_cost", "overhead_cost", "cogs",
    "orders_total", "orders_on_time", "inventory_avg_value",
    "safety_incidents",
]

DEFAULT_CSV = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data", "raw", "manufacturing_data.csv",
)


def load_data(path: str | None = None) -> pd.DataFrame:
    """Đọc file CSV dữ liệu thô."""
    path = path or DEFAULT_CSV
    df = pd.read_csv(path)
    df["period"] = df["year"].astype(str) + " " + df["quarter"]
    return df


def aggregate(df: pd.DataFrame) -> dict:
    """Gộp một DataFrame con thành dict cột thô + tính sẵn các giá trị phụ."""
    agg = {c: float(df[c].sum()) for c in SUM_COLS}
    # Chu kỳ lý tưởng: trung bình có trọng số theo sản lượng
    if df["total_units"].sum() > 0:
        agg["ideal_cycle_s"] = float(
            (df["ideal_cycle_s"] * df["total_units"]).sum() / df["total_units"].sum()
        )
    else:
        agg["ideal_cycle_s"] = float(df["ideal_cycle_s"].mean())
    # Hệ số quy năm cho vòng quay tồn kho = 12 / số tháng trong kỳ
    n_months = df["month"].nunique() * max(1, df["year"].nunique())
    agg["_quarters_factor"] = 12 / n_months if n_months else 4
    return agg


def kpis_for(df: pd.DataFrame) -> dict:
    """Tính toàn bộ KPI cho một DataFrame con."""
    return compute_kpis(aggregate(df))


def quarterly_table(df: pd.DataFrame, lines: list[str] | None = None) -> pd.DataFrame:
    """
    Bảng KPI theo từng kỳ (năm + quý).
    Trả về DataFrame: mỗi dòng là một kỳ, mỗi cột là một KPI.
    """
    if lines:
        df = df[df["line"].isin(lines)]
    rows = []
    for period, sub in df.groupby("period", sort=True):
        k = kpis_for(sub)
        k["period"] = period
        k["total_units"] = int(sub["total_units"].sum())
        k["revenue"] = float(sub["revenue"].sum())
        rows.append(k)
    out = pd.DataFrame(rows).set_index("period").sort_index()
    return out


def status_table(kpi_table: pd.DataFrame) -> pd.DataFrame:
    """Chuyển bảng giá trị KPI thành bảng trạng thái Đạt/Cảnh báo/Chưa đạt."""
    data = {}
    for key in targets.KPI_DEFS:
        if key in kpi_table.columns:
            data[key] = kpi_table[key].apply(lambda v: targets.evaluate(key, v))
    return pd.DataFrame(data, index=kpi_table.index)
