import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from models import Analysis, ChatMessage
from services.llm import chat_with_analysis

router = APIRouter(prefix="/api/analyses", tags=["chat"])


class ChatRequest(BaseModel):
    question: str


@router.post("/{analysis_id}/chat")
async def chat(
    analysis_id: str,
    body: ChatRequest,
    db: Session = Depends(get_db),
):
    """해당 분석 기준으로 AI 챗봇 답변"""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="분석 기록을 찾을 수 없습니다.")

    # 이전 대화 히스토리
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.analysis_id == analysis_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    history_dicts = [{"role": m.role, "content": m.content} for m in history]

    # 실시간 집계 데이터 (카테고리 + 지점 + 결제수단 기본 제공)
    aggregated = _build_aggregated_context(db, analysis_id)

    # DB executor: SQL 문자열을 받아 Row dict 목록 반환 (Text-to-SQL용)
    import logging
    _log = logging.getLogger(__name__)
    def db_executor(sql: str):
        rows = db.execute(text(sql)).mappings().all()
        result = [dict(r) for r in rows]
        _log.warning(f"[DB_EXEC] rows={len(result)}, sample={result[:2]}")
        return result

    # GPT 답변 생성 (Text-to-SQL 우선, fallback으로 집계 데이터 사용)
    answer = await chat_with_analysis(
        analysis_summary=analysis.summary or {},
        aggregated_data=aggregated,
        messages=history_dicts,
        user_question=body.question,
        analysis_id=analysis_id,
        db_executor=db_executor,
    )

    # 사용자 메시지 저장
    user_msg = ChatMessage(
        id=str(uuid.uuid4()),
        analysis_id=analysis_id,
        role="user",
        content=body.question,
    )
    db.add(user_msg)

    # AI 답변 저장
    ai_msg = ChatMessage(
        id=str(uuid.uuid4()),
        analysis_id=analysis_id,
        role="assistant",
        content=answer,
    )
    db.add(ai_msg)
    db.commit()

    return {
        "question": body.question,
        "answer": answer,
        "analysis_id": analysis_id,
    }


@router.get("/{analysis_id}/chat")
def get_chat_history(analysis_id: str, db: Session = Depends(get_db)):
    """대화 기록 조회"""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="분석 기록을 찾을 수 없습니다.")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.analysis_id == analysis_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at,
        }
        for m in messages
    ]


def _build_aggregated_context(db: Session, analysis_id: str) -> dict:
    """AI 컨텍스트용 실시간 집계"""
    context = {}

    # 카테고리별 매출
    rows = db.execute(
        text("""
            SELECT category, ROUND(SUM(total_amount),2), SUM(quantity)
            FROM csv_rows WHERE analysis_id=:aid GROUP BY category ORDER BY 2 DESC LIMIT 10
        """),
        {"aid": analysis_id},
    ).fetchall()
    context["카테고리별 매출"] = {r[0]: {"revenue": r[1], "quantity": r[2]} for r in rows}

    # 지점별 매출
    rows = db.execute(
        text("""
            SELECT store_location, ROUND(SUM(total_amount),2), COUNT(*)
            FROM csv_rows WHERE analysis_id=:aid GROUP BY store_location ORDER BY 2 DESC
        """),
        {"aid": analysis_id},
    ).fetchall()
    context["지점별 매출"] = {r[0]: {"revenue": r[1], "transactions": r[2]} for r in rows}

    # 결제수단별
    rows = db.execute(
        text("""
            SELECT payment_method, COUNT(*), ROUND(SUM(total_amount),2)
            FROM csv_rows WHERE analysis_id=:aid GROUP BY payment_method ORDER BY 2 DESC
        """),
        {"aid": analysis_id},
    ).fetchall()
    context["결제수단별"] = {r[0]: {"count": r[1], "revenue": r[2]} for r in rows}

    # ── 추가: 지점별 TOP 10 상품 (판매량 기준) ─────────────────────────────
    rows = db.execute(
        text("""
            SELECT store_location, product_name,
                   SUM(quantity) as total_qty,
                   ROUND(SUM(total_amount),2) as total_rev
            FROM csv_rows
            WHERE analysis_id=:aid AND store_location IS NOT NULL AND product_name IS NOT NULL
            GROUP BY store_location, product_name
            ORDER BY store_location, total_qty DESC
        """),
        {"aid": analysis_id},
    ).fetchall()
    store_products: dict = {}
    for store, product, qty, rev in rows:
        if store not in store_products:
            store_products[store] = []
        if len(store_products[store]) < 10:
            store_products[store].append({
                "product": product,
                "quantity": qty,
                "revenue": rev,
            })
    context["지점별 TOP10 상품(판매량)"] = store_products

    # ── 추가: 카테고리별 TOP 5 상품 ───────────────────────────────────────
    rows = db.execute(
        text("""
            SELECT category, product_name,
                   SUM(quantity) as total_qty,
                   ROUND(SUM(total_amount),2) as total_rev
            FROM csv_rows
            WHERE analysis_id=:aid AND category IS NOT NULL AND product_name IS NOT NULL
            GROUP BY category, product_name
            ORDER BY category, total_qty DESC
        """),
        {"aid": analysis_id},
    ).fetchall()
    cat_products: dict = {}
    for cat, product, qty, rev in rows:
        if cat not in cat_products:
            cat_products[cat] = []
        if len(cat_products[cat]) < 5:
            cat_products[cat].append({
                "product": product,
                "quantity": qty,
                "revenue": rev,
            })
    context["카테고리별 TOP5 상품"] = cat_products

    # ── 추가: 연령대별 선호 카테고리 & 상품 ───────────────────────────────
    rows = db.execute(
        text("""
            SELECT age_group, category, SUM(quantity) as qty
            FROM csv_rows
            WHERE analysis_id=:aid AND age_group IS NOT NULL AND category IS NOT NULL
            GROUP BY age_group, category
            ORDER BY age_group, qty DESC
        """),
        {"aid": analysis_id},
    ).fetchall()
    age_prefs: dict = {}
    for age, cat, qty in rows:
        if age not in age_prefs:
            age_prefs[age] = []
        if len(age_prefs[age]) < 5:
            age_prefs[age].append({"category": cat, "quantity": qty})
    context["연령대별 선호 카테고리"] = age_prefs

    # ── 추가: 전체 상품별 순위 TOP 20 ─────────────────────────────────────
    rows = db.execute(
        text("""
            SELECT product_name,
                   SUM(quantity) as total_qty,
                   ROUND(SUM(total_amount),2) as total_rev,
                   COUNT(*) as transactions
            FROM csv_rows
            WHERE analysis_id=:aid AND product_name IS NOT NULL
            GROUP BY product_name
            ORDER BY total_qty DESC
            LIMIT 20
        """),
        {"aid": analysis_id},
    ).fetchall()
    context["전체 상품 순위 TOP20(판매량)"] = [
        {"product": r[0], "quantity": r[1], "revenue": r[2], "transactions": r[3]}
        for r in rows
    ]

    return context
