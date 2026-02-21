import pandas as pd
import numpy as np
from typing import Any


def analyze_csv(df: pd.DataFrame) -> dict[str, Any]:
    """
    CSV 데이터프레임을 받아 분석 템플릿에 따라 분석 결과를 반환.
    반환값: summary, chart_data, insights 딕셔너리
    """
    df = _preprocess(df)

    summary = {}
    chart_data = {}
    insights = {}

    # ── 1. 기초 통계 ────────────────────────────────────────────────────
    summary["basic_stats"] = _basic_stats(df)

    # ── 2. 트렌드 (시간대별 매출) ─────────────────────────────────────────
    trend_result, trend_chart = _trend_analysis(df)
    summary["trend"] = trend_result
    chart_data["hourly_sales"] = trend_chart

    # ── 3. 상품 전략 (TOP 5) ──────────────────────────────────────────────
    product_result, product_chart = _product_strategy(df)
    summary["product_strategy"] = product_result
    chart_data["top_products"] = product_chart

    # ── 4. 지점별 분석 ────────────────────────────────────────────────────
    store_result, store_chart = _store_analysis(df)
    summary["store_analysis"] = store_result
    chart_data["store_comparison"] = store_chart

    # ── 5. 인사이트 ───────────────────────────────────────────────────────
    insights = _generate_insights(df, summary)

    return {
        "summary": summary,
        "chart_data": chart_data,
        "insights": insights,
    }


def _preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """컬럼명 정규화 및 타입 변환"""
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # 컬럼 매핑 (원본 CSV 컬럼명 → 내부 컬럼명)
    col_map = {
        "transaction_id": "transaction_id",
        "date": "date",
        "time": "time",
        "category": "category",
        "product_name": "product_name",
        "price": "price",
        "quantity": "quantity",
        "payment_method": "payment_method",
        "store_location": "store_location",
        "total_amount": "total_amount",
        "age_group": "age_group",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # 날짜/시간 파싱
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if "time" in df.columns:
        df["hour"] = pd.to_datetime(df["time"], format="%H:%M:%S", errors="coerce").dt.hour

    # 숫자 타입 변환
    for col in ["price", "quantity", "total_amount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _basic_stats(df: pd.DataFrame) -> dict:
    total_revenue = float(df["total_amount"].sum()) if "total_amount" in df.columns else 0
    total_transactions = int(len(df))
    avg_order_value = float(df["total_amount"].mean()) if "total_amount" in df.columns else 0

    return {
        "total_revenue": round(total_revenue, 2),
        "total_transactions": total_transactions,
        "avg_order_value": round(avg_order_value, 2),
    }


def _trend_analysis(df: pd.DataFrame) -> tuple[dict, list]:
    if "hour" not in df.columns or "total_amount" not in df.columns:
        return {}, []

    hourly = (
        df.groupby("hour")["total_amount"]
        .agg(["sum", "count"])
        .reset_index()
        .rename(columns={"sum": "revenue", "count": "transactions"})
    )
    hourly["hour"] = hourly["hour"].astype(int)

    # NaN이 아닌 값이 있을 때만 idxmax() 호출
    revenue_series = hourly["revenue"].dropna()
    if revenue_series.empty:
        return {}, []

    peak_idx = revenue_series.idxmax()
    peak_hour = int(hourly.loc[peak_idx, "hour"])
    peak_revenue = float(hourly["revenue"].max())

    chart = [
        {
            "hour": f"{int(row['hour']):02d}:00",
            "revenue": round(float(row["revenue"]), 2),
            "transactions": int(row["transactions"]),
        }
        for _, row in hourly.iterrows()
    ]

    return {
        "peak_hour": peak_hour,
        "peak_hour_label": f"{peak_hour:02d}:00",
        "peak_revenue": round(peak_revenue, 2),
    }, chart


def _product_strategy(df: pd.DataFrame) -> tuple[dict, dict]:
    if "product_name" not in df.columns:
        return {}, {}

    # 판매량 TOP 5
    top_qty = (
        df.groupby("product_name")["quantity"]
        .sum()
        .nlargest(5)
        .reset_index()
        .rename(columns={"quantity": "total_quantity"})
    )

    # 매출 기여도 TOP 5
    total_rev = df["total_amount"].sum() if "total_amount" in df.columns else 1
    top_rev = (
        df.groupby("product_name")["total_amount"]
        .sum()
        .nlargest(5)
        .reset_index()
        .rename(columns={"total_amount": "total_revenue"})
    )
    top_rev["contribution_pct"] = (top_rev["total_revenue"] / total_rev * 100).round(2)

    return (
        {
            "top5_by_quantity": top_qty.to_dict(orient="records"),
            "top5_by_revenue": top_rev.to_dict(orient="records"),
        },
        {
            "top5_quantity": top_qty.to_dict(orient="records"),
            "top5_revenue": top_rev.to_dict(orient="records"),
        },
    )


def _store_analysis(df: pd.DataFrame) -> tuple[dict, list]:
    if "store_location" not in df.columns:
        return {}, []

    store_stats = (
        df.groupby("store_location")
        .agg(
            total_revenue=("total_amount", "sum"),
            total_transactions=("transaction_id", "count"),
            avg_order_value=("total_amount", "mean"),
        )
        .reset_index()
    )

    chart = []
    result = {}
    for _, row in store_stats.iterrows():
        store_name = row["store_location"]
        store_df = df[df["store_location"] == store_name]

        # 지점별 TOP 3 상품 (판매량 기준)
        if "product_name" in store_df.columns:
            top3 = (
                store_df.groupby("product_name")["quantity"]
                .sum()
                .nlargest(3)
                .reset_index()
                .to_dict(orient="records")
            )
        else:
            top3 = []

        result[store_name] = {
            "total_revenue": round(float(row["total_revenue"]), 2),
            "total_transactions": int(row["total_transactions"]),
            "avg_order_value": round(float(row["avg_order_value"]), 2),
            "top3_products": top3,
        }

        chart.append(
            {
                "store": store_name,
                "revenue": round(float(row["total_revenue"]), 2),
                "transactions": int(row["total_transactions"]),
            }
        )

    return result, chart


def _generate_insights(df: pd.DataFrame, summary: dict) -> dict:
    positives = []
    negatives = []

    # 피크 타임 인사이트
    trend = summary.get("trend", {})
    if trend.get("peak_hour") is not None:
        peak = trend["peak_hour"]
        positives.append(
            f"피크 타임은 {peak:02d}:00으로, 이 시간대 집중 운영으로 매출 극대화 가능합니다."
        )

    # 카테고리 집중도 인사이트
    if "category" in df.columns and "total_amount" in df.columns:
        cat_rev = df.groupby("category")["total_amount"].sum().dropna()
        if not cat_rev.empty:
            top_cat = cat_rev.idxmax()
            top_cat_pct = cat_rev.max() / cat_rev.sum() * 100
            if top_cat_pct > 40:
                negatives.append(
                    f"'{top_cat}' 카테고리에 매출의 {top_cat_pct:.1f}%가 집중되어 있어 "
                    f"카테고리 다변화가 필요합니다."
                )
            else:
                positives.append(
                    f"카테고리별 매출이 비교적 고르게 분산되어 있어 안정적인 매출 구조입니다."
                )

    # 지점 편차 인사이트
    store = summary.get("store_analysis", {})
    if store and len(store) > 1:
        revenues = [v["total_revenue"] for v in store.values()]
        cv = float(np.std(revenues) / np.mean(revenues)) if np.mean(revenues) > 0 else 0
        if cv > 0.3:
            negatives.append(
                f"지점별 매출 편차가 크며(CV={cv:.2f}), 저성과 지점에 대한 운영 개선이 필요합니다."
            )
        else:
            positives.append("지점 간 매출 편차가 낮아 균형 잡힌 운영이 이루어지고 있습니다.")

    return {"positives": positives, "negatives": negatives}
