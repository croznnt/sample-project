# -*- coding: utf-8 -*-
"""
Dashboard KPI Quản trị công nghiệp – hiển thị & đánh giá theo từng QUÝ.

Chạy:  streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import targets
from src.data_loader import (
    load_data, quarterly_table, status_table, kpis_for,
)
from src.targets import (
    KPI_DEFS, GROUPS, STATUS_COLOR, GOOD, WARN, BAD,
    evaluate, format_value,
)

# ---------------------------------------------------------------------------
# Thiết lập trang
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="KPI Quản trị công nghiệp",
    page_icon="🏭",
    layout="wide",
)

PALETTE = ["#2563eb", "#16a34a", "#d97706", "#9333ea", "#0891b2", "#dc2626"]


@st.cache_data
def get_data() -> pd.DataFrame:
    return load_data()


df = get_data()
all_lines = sorted(df["line"].unique())
all_periods = sorted(df["period"].unique())

# ---------------------------------------------------------------------------
# Sidebar – bộ lọc
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Bộ lọc")
    sel_lines = st.multiselect(
        "Dây chuyền sản xuất", all_lines, default=all_lines,
    )
    if not sel_lines:
        st.warning("Hãy chọn ít nhất một dây chuyền.")
        st.stop()

    fdf = df[df["line"].isin(sel_lines)]
    periods = sorted(fdf["period"].unique())
    sel_quarter = st.selectbox(
        "Quý phân tích (thẻ điểm)", periods, index=len(periods) - 1,
    )
    st.divider()
    st.caption(
        "Nguồn: `data/raw/manufacturing_data.csv`\n\n"
        f"- {len(all_lines)} dây chuyền\n"
        f"- {len(all_periods)} quý ({all_periods[0]} → {all_periods[-1]})\n"
        f"- {len(df)} bản ghi theo tháng"
    )

# Bảng KPI theo quý cho các dây chuyền đã chọn
qt = quarterly_table(df, lines=sel_lines)
st_tbl = status_table(qt)

# ---------------------------------------------------------------------------
# Tiêu đề
# ---------------------------------------------------------------------------
st.title("🏭 Dashboard KPI Quản trị công nghiệp")
st.markdown(
    "Theo dõi và **đánh giá hiệu quả sản xuất theo từng quý** trên các nhóm chỉ số: "
    "OEE, Chất lượng, Bảo trì, Năng suất, Tài chính, Chuỗi cung ứng và An toàn."
)

tab_card, tab_trend, tab_line, tab_table, tab_raw = st.tabs(
    ["📊 Thẻ điểm quý", "📈 Xu hướng theo quý", "🏭 So sánh dây chuyền",
     "📋 Bảng đánh giá", "🗃️ Dữ liệu gốc"]
)


# ===========================================================================
# TAB 1 – THẺ ĐIỂM QUÝ
# ===========================================================================
def badge(status: str) -> str:
    return (f"<span style='background:{STATUS_COLOR[status]};color:#fff;"
            f"padding:2px 10px;border-radius:12px;font-size:0.8rem;"
            f"font-weight:600'>{status}</span>")


with tab_card:
    idx = list(qt.index).index(sel_quarter)
    cur = qt.loc[sel_quarter]
    prev = qt.iloc[idx - 1] if idx > 0 else None

    # Tóm tắt trạng thái
    statuses = st_tbl.loc[sel_quarter]
    n_good = int((statuses == GOOD).sum())
    n_warn = int((statuses == WARN).sum())
    n_bad = int((statuses == BAD).sum())

    st.subheader(f"Thẻ điểm KPI – {sel_quarter}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sản lượng (sp)", f"{int(cur['total_units']):,}")
    c2.metric("✅ Đạt", n_good)
    c3.metric("⚠️ Cảnh báo", n_warn)
    c4.metric("❌ Chưa đạt", n_bad)
    st.divider()

    for group in GROUPS:
        keys = [k for k, d in KPI_DEFS.items() if d["group"] == group]
        keys = [k for k in keys if k in qt.columns]
        if not keys:
            continue
        st.markdown(f"#### {group}")
        cols = st.columns(len(keys))
        for col, key in zip(cols, keys):
            val = cur[key]
            status = evaluate(key, val)
            delta = None
            if prev is not None:
                diff = val - prev[key]
                d = KPI_DEFS[key]
                sign = "normal" if d["higher_is_better"] else "inverse"
                delta = f"{diff:+.1f}"
                col.metric(
                    KPI_DEFS[key]["label"].split(" (")[0],
                    format_value(key, val),
                    delta=delta, delta_color=sign,
                )
            else:
                col.metric(
                    KPI_DEFS[key]["label"].split(" (")[0],
                    format_value(key, val),
                )
            col.markdown(badge(status), unsafe_allow_html=True)
            col.caption(
                f"Mục tiêu: {format_value(key, KPI_DEFS[key]['target'])}"
            )
        st.divider()


# ===========================================================================
# TAB 2 – XU HƯỚNG THEO QUÝ
# ===========================================================================
def trend_chart(key: str) -> go.Figure:
    d = KPI_DEFS[key]
    fig = go.Figure()
    fig.add_bar(
        x=qt.index, y=qt[key],
        marker_color=[STATUS_COLOR[evaluate(key, v)] for v in qt[key]],
        name=d["label"], text=[format_value(key, v) for v in qt[key]],
        textposition="outside",
    )
    # Đường mục tiêu
    fig.add_hline(
        y=d["target"], line_dash="dash", line_color="#16a34a",
        annotation_text=f"Mục tiêu {format_value(key, d['target'])}",
        annotation_position="top left",
    )
    fig.add_hline(
        y=d["warn"], line_dash="dot", line_color="#d97706",
        annotation_text=f"Ngưỡng {format_value(key, d['warn'])}",
        annotation_position="bottom left",
    )
    fig.update_layout(
        title=d["label"], height=360,
        margin=dict(l=10, r=10, t=50, b=10),
        plot_bgcolor="white", showlegend=False,
        yaxis_title=d["unit"],
    )
    return fig


with tab_trend:
    st.subheader("Xu hướng KPI qua các quý")
    all_keys = [k for k in KPI_DEFS if k in qt.columns]
    default_keys = ["oee", "fpy", "otd", "gross_margin"]
    sel_keys = st.multiselect(
        "Chọn KPI để xem xu hướng",
        options=all_keys,
        default=default_keys,
        format_func=lambda k: KPI_DEFS[k]["label"],
    )
    cols = st.columns(2)
    for i, key in enumerate(sel_keys):
        cols[i % 2].plotly_chart(trend_chart(key), width="stretch")


# ===========================================================================
# TAB 3 – SO SÁNH DÂY CHUYỀN
# ===========================================================================
with tab_line:
    st.subheader(f"So sánh dây chuyền – {sel_quarter}")
    year, q = sel_quarter.split(" ")
    sub = df[(df["period"] == sel_quarter) & (df["line"].isin(sel_lines))]

    comp_key = st.selectbox(
        "Chỉ số so sánh",
        [k for k in KPI_DEFS if k in qt.columns],
        format_func=lambda k: KPI_DEFS[k]["label"],
    )
    rows = []
    for line in sel_lines:
        ldf = sub[sub["line"] == line]
        if ldf.empty:
            continue
        val = kpis_for(ldf)[comp_key]
        rows.append((line, val, evaluate(comp_key, val)))
    comp = pd.DataFrame(rows, columns=["line", "value", "status"])

    fig = go.Figure()
    fig.add_bar(
        x=comp["line"], y=comp["value"],
        marker_color=[STATUS_COLOR[s] for s in comp["status"]],
        text=[format_value(comp_key, v) for v in comp["value"]],
        textposition="outside",
    )
    d = KPI_DEFS[comp_key]
    fig.add_hline(y=d["target"], line_dash="dash", line_color="#16a34a",
                  annotation_text="Mục tiêu")
    fig.update_layout(
        title=f"{d['label']} theo dây chuyền ({sel_quarter})",
        height=420, plot_bgcolor="white", showlegend=False,
        yaxis_title=d["unit"], margin=dict(l=10, r=10, t=50, b=10),
    )
    st.plotly_chart(fig, width="stretch")


# ===========================================================================
# TAB 4 – BẢNG ĐÁNH GIÁ
# ===========================================================================
with tab_table:
    st.subheader("Bảng KPI & đánh giá theo quý")
    show = qt[[k for k in KPI_DEFS if k in qt.columns]].copy()
    show.columns = [KPI_DEFS[k]["label"] for k in show.columns]

    def color_status(col_name):
        # map cột -> key
        key = next(k for k in KPI_DEFS if KPI_DEFS[k]["label"] == col_name)
        return [
            f"background-color:{STATUS_COLOR[evaluate(key, v)]}20;"
            f"color:{STATUS_COLOR[evaluate(key, v)]};font-weight:600"
            for v in qt[key]
        ]

    styler = show.style
    for col in show.columns:
        styler = styler.apply(lambda s, c=col: color_status(c), subset=[col])
    styler = styler.format(precision=1)
    st.dataframe(styler, width="stretch")

    st.caption(
        f"🟢 {GOOD}  –  🟠 {WARN}  –  🔴 {BAD}. "
        "Màu nền thể hiện trạng thái so với mục tiêu của từng KPI."
    )

    # Tải xuống
    csv = qt.to_csv().encode("utf-8-sig")
    st.download_button(
        "⬇️ Tải bảng KPI (CSV)", csv,
        file_name="kpi_theo_quy.csv", mime="text/csv",
    )


# ===========================================================================
# TAB 5 – DỮ LIỆU GỐC
# ===========================================================================
with tab_raw:
    st.subheader("Dữ liệu sản xuất gốc (theo tháng)")
    st.dataframe(fdf, width="stretch", height=500)
    st.download_button(
        "⬇️ Tải dữ liệu gốc (CSV)",
        fdf.to_csv(index=False).encode("utf-8-sig"),
        file_name="du_lieu_goc.csv", mime="text/csv",
    )
