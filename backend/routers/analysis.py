from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from models import Analysis

router = APIRouter(prefix="/api/analyses", tags=["analyses"])


@router.get("")
def list_analyses(db: Session = Depends(get_db)):
    """분석 기록 목록 조회 (최신순)"""
    analyses = (
        db.query(Analysis)
        .order_by(Analysis.uploaded_at.desc())
        .all()
    )
    return [
        {
            "id": a.id,
            "filename": a.filename,
            "uploaded_at": a.uploaded_at,
            "basic_stats": a.summary.get("basic_stats") if a.summary else None,
        }
        for a in analyses
    ]


@router.get("/{analysis_id}")
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """분석 기록 상세 조회"""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="분석 기록을 찾을 수 없습니다.")

    # 행 수 조회
    row_count = db.execute(
        text("SELECT COUNT(*) FROM csv_rows WHERE analysis_id = :aid"),
        {"aid": analysis_id},
    ).scalar()

    return {
        "id": analysis.id,
        "filename": analysis.filename,
        "uploaded_at": analysis.uploaded_at,
        "summary": analysis.summary,
        "chart_data": analysis.chart_data,
        "insights": analysis.insights,
        "row_count": row_count,
    }


@router.delete("/{analysis_id}")
def delete_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """분석 기록 삭제 (CSV 데이터 및 챗봇 대화 포함)"""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="분석 기록을 찾을 수 없습니다.")

    db.delete(analysis)
    db.commit()
    return {"message": "분석 기록이 삭제되었습니다.", "id": analysis_id}


@router.get("/{analysis_id}/query")
def query_data(
    analysis_id: str,
    question_type: str = "hourly",
    db: Session = Depends(get_db),
):
    """
    AI 챗봇을 위한 실시간 데이터 집계.
    question_type: hourly | category | product | store | payment
    """
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="분석 기록을 찾을 수 없습니다.")

    result = {}

    if question_type == "hourly":
        rows = db.execute(
            text("""
                SELECT substr(time, 1, 2) as hour,
                       ROUND(SUM(total_amount), 2) as revenue,
                       COUNT(*) as cnt
                FROM csv_rows
                WHERE analysis_id = :aid
                GROUP BY hour
                ORDER BY hour
            """),
            {"aid": analysis_id},
        ).fetchall()
        result = [{"hour": f"{r[0]}:00", "revenue": r[1], "transactions": r[2]} for r in rows]

    elif question_type == "category":
        rows = db.execute(
            text("""
                SELECT category,
                       ROUND(SUM(total_amount), 2) as revenue,
                       SUM(quantity) as total_qty
                FROM csv_rows
                WHERE analysis_id = :aid
                GROUP BY category
                ORDER BY revenue DESC
            """),
            {"aid": analysis_id},
        ).fetchall()
        result = [{"category": r[0], "revenue": r[1], "quantity": r[2]} for r in rows]

    elif question_type == "product":
        rows = db.execute(
            text("""
                SELECT product_name,
                       SUM(quantity) as total_qty,
                       ROUND(SUM(total_amount), 2) as revenue
                FROM csv_rows
                WHERE analysis_id = :aid
                GROUP BY product_name
                ORDER BY revenue DESC
                LIMIT 20
            """),
            {"aid": analysis_id},
        ).fetchall()
        result = [{"product": r[0], "quantity": r[1], "revenue": r[2]} for r in rows]

    elif question_type == "store":
        rows = db.execute(
            text("""
                SELECT store_location,
                       ROUND(SUM(total_amount), 2) as revenue,
                       COUNT(*) as transactions
                FROM csv_rows
                WHERE analysis_id = :aid
                GROUP BY store_location
                ORDER BY revenue DESC
            """),
            {"aid": analysis_id},
        ).fetchall()
        result = [{"store": r[0], "revenue": r[1], "transactions": r[2]} for r in rows]

    elif question_type == "payment":
        rows = db.execute(
            text("""
                SELECT payment_method,
                       COUNT(*) as cnt,
                       ROUND(SUM(total_amount), 2) as revenue
                FROM csv_rows
                WHERE analysis_id = :aid
                GROUP BY payment_method
                ORDER BY cnt DESC
            """),
            {"aid": analysis_id},
        ).fetchall()
        result = [{"method": r[0], "count": r[1], "revenue": r[2]} for r in rows]

    return {"question_type": question_type, "data": result}
