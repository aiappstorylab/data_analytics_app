import logging
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-5-nano-2025-08-07"

# CSV 테이블 스키마 (SQL 생성용)
DB_SCHEMA = """
테이블: csv_rows
컬럼:
  - analysis_id TEXT  (현재 분석 ID, 항상 WHERE analysis_id = '{aid}' 조건 필수)
  - transaction_id TEXT
  - date TEXT         (날짜 형식: 'YYYY-MM-DD', 예: '2026-01-15')
  - time TEXT         (시간 형식: 'HH:MM:SS', 예: '14:30:00')
  - category TEXT     (상품 카테고리)
  - product_name TEXT (상품명, 한글)
  - price REAL        (단가)
  - quantity INTEGER  (수량)
  - payment_method TEXT (결제수단)
  - store_location TEXT (지점명, 영문으로 저장됨)
  - total_amount REAL  (총 결제금액)
  - age_group TEXT    (연령대)

실제 store_location 값 (영문):
  - Gangnam  (강남, 강남점)
  - Hongdae  (홍대, 홍대점)
  - Mapo     (마포, 마포점)
  - Sinsa    (신사, 신사점)
  - Yeouido  (여의도, 여의도점)

실제 age_group 값 (영문):
  - 10s   (10대, 10대 고객)
  - 20s   (20대, 20대 고객)
  - 30s   (30대, 30대 고객)
  - 40s   (40대, 40대 고객)
  - 50s   (50대, 50대 고객)
  - 60s+  (60대 이상, 60대+)

날짜 필터 방법 (SQLite):
  - 특정 월: WHERE strftime('%Y-%m', date) = '2026-01'
  - 특정 연도: WHERE strftime('%Y', date) = '2026'
  - 날짜 범위: WHERE date >= '2026-01-01' AND date < '2026-02-01'
  - 1월: strftime('%m', date) = '01'
"""


async def chat_with_analysis(
    analysis_summary: dict,
    aggregated_data: dict,
    messages: list[dict],
    user_question: str,
    analysis_id: str = "",
    db_executor=None,
) -> str:
    """
    1단계: 질문 분류 (집계 데이터로 충분한지 vs DB 직접 쿼리 필요한지)
    2단계-A: 집계 데이터로 답변 가능 → 기존 방식
    2단계-B: DB 쿼리 필요 → SQL 생성 → 실행 → 결과로 답변
    """
    # DB 쿼리가 가능한 경우 Text-to-SQL 시도
    if db_executor and analysis_id:
        try:
            return await _answer_with_sql(
                analysis_summary, aggregated_data, messages, user_question, analysis_id, db_executor
            )
        except Exception as e:
            logger.warning(f"[LLM] Text-to-SQL 실패, fallback: {e}")

    # fallback: 기존 집계 데이터 기반 답변
    return await _answer_with_context(analysis_summary, aggregated_data, messages, user_question)


async def _answer_with_sql(
    analysis_summary: dict,
    aggregated_data: dict,
    messages: list[dict],
    user_question: str,
    analysis_id: str,
    db_executor,
) -> str:
    """Text-to-SQL: 질문 → SQL 생성 → 실행 → 답변"""

    # ── Step 1: SQL 생성 ─────────────────────────────────────────────────
    sql_system = f"""당신은 SQLite SQL 전문가입니다.
아래 스키마를 참고하여 사용자 질문에 답하는 SELECT SQL을 딱 하나만 생성하세요.

{DB_SCHEMA}

규칙:
1. 반드시 WHERE 절에 analysis_id = '{analysis_id}' 조건을 포함하세요.
2. SQL 코드만 출력하세요. 설명, 마크다운 코드블록(``` 등) 없이 순수 SQL만.
3. 결과는 최대 50행으로 제한하세요 (LIMIT 50).
4. 집계함수(SUM, COUNT, AVG 등)와 GROUP BY를 적극 활용하세요.
5. 정렬(ORDER BY)을 통해 의미있는 순서로 반환하세요.
6. ★ 절대 금지: 사용자가 명시적으로 요청하지 않은 날짜/기간 조건을 추가하지 마세요.
7. ★ 지점명 변환: 한글 지점명은 반드시 영문으로 변환하세요.
   강남→Gangnam, 홍대→Hongdae, 마포→Mapo, 신사→Sinsa, 여의도→Yeouido
   store_location = 'Gangnam' (정확한 영문 값 사용)
8. ★ 연령대 변환: 한글 연령대는 반드시 영문으로 변환하세요.
   10대→10s, 20대→20s, 30대→30s, 40대→40s, 50대→50s, 60대 이상→60s+
   age_group = '20s' (정확한 영문 값 사용)
9. ★ 날짜 변환: 자연어 날짜를 SQLite strftime()으로 변환하세요.
   "1월" → strftime('%m', date) = '01'
   "2026년 1월" → strftime('%Y-%m', date) = '2026-01'
   "1월~2월" → date >= '2026-01-01' AND date < '2026-03-01'

예시:
Q: "강남 지점 1월에 제일 많이 팔린 상품은?"
A:
SELECT product_name, SUM(quantity) AS total_qty
FROM csv_rows
WHERE analysis_id = '{analysis_id}'
  AND store_location = 'Gangnam'
  AND strftime('%m', date) = '01'
GROUP BY product_name
ORDER BY total_qty DESC
LIMIT 10;

Q: "20대 고객이 가장 많이 구매한 카테고리는?"
A:
SELECT category, SUM(quantity) AS total_qty, ROUND(SUM(total_amount),0) AS revenue
FROM csv_rows
WHERE analysis_id = '{analysis_id}'
  AND age_group = '20s'
GROUP BY category
ORDER BY total_qty DESC
LIMIT 10;

Q: "지점별 2월 매출 비교"
A:
SELECT store_location, SUM(total_amount) AS revenue, COUNT(*) AS transactions
FROM csv_rows
WHERE analysis_id = '{analysis_id}'
  AND strftime('%m', date) = '02'
GROUP BY store_location
ORDER BY revenue DESC;
"""
    sql_response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": sql_system},
            {"role": "user", "content": user_question},
        ],
        max_completion_tokens=4096,
    )

    sql_query = sql_response.choices[0].message.content
    if not sql_query:
        raise ValueError("SQL 생성 실패")
    sql_query = sql_query.strip().strip("```sql").strip("```").strip()
    logger.warning(f"[LLM] 생성된 SQL:\n{sql_query}")

    # ── Step 2: SQL 실행 ─────────────────────────────────────────────────
    try:
        query_result = db_executor(sql_query)
    except Exception as e:
        logger.warning(f"[LLM] SQL 실행 오류: {e}\nSQL: {sql_query}")
        raise ValueError(f"SQL 실행 오류: {e}")

    logger.warning(f"[LLM] SQL 결과 ({len(query_result)}행): {list(query_result[:3])}")

    # ── Step 3: 결과를 바탕으로 자연어 답변 ─────────────────────────────
    if not query_result:
        # SQL 결과가 없으면 집계 컨텍스트 기반 답변으로 fallback
        # (store_analysis TOP3 등 summary 데이터 포함)
        logger.warning("[LLM] SQL 결과 없음 → _answer_with_context fallback")
        return await _answer_with_context(
            analysis_summary, aggregated_data, messages, user_question
        )

    result_text = _format_query_result(query_result)

    answer_system = """당신은 매출 데이터 분석 전문 AI 어시스턴트입니다.
사용자가 제공하는 DB 쿼리 결과를 바탕으로 한국어로 친절하고 명확하게 답변하세요.
- 쿼리 결과의 수치(상품명, 매출액, 판매량 등)를 반드시 구체적으로 언급하세요.
- 쿼리 결과에 없는 데이터는 언급하지 마세요.
- 데이터가 충분하다면 "데이터가 없다"고 하지 마세요."""

    # user 메시지에 SQL + 쿼리 결과를 직접 포함 (reasoning 모델이 필터 조건을 인식하도록)
    user_msg_with_data = (
        f"[실행된 SQL — 이 SQL의 WHERE 조건이 이미 적용된 결과입니다]\n"
        f"```sql\n{sql_query}\n```\n\n"
        f"[위 SQL의 DB 쿼리 결과 — {len(query_result)}행]\n"
        f"{result_text}\n\n"
        f"위 결과는 SQL의 조건(지점, 날짜, 연령대 등)이 이미 필터링된 데이터입니다.\n"
        f"이 데이터를 그대로 사용하여 다음 질문에 한국어로 답해주세요:\n{user_question}"
    )

    history = [{"role": "system", "content": answer_system}]
    for msg in messages[-10:]:
        history.append({"role": msg["role"], "content": msg["content"]})
    history.append({"role": "user", "content": user_msg_with_data})

    answer_response = await client.chat.completions.create(
        model=MODEL,
        messages=history,
        max_completion_tokens=16384,
    )

    choice = answer_response.choices[0]
    logger.warning(f"[LLM-ANS] finish_reason={choice.finish_reason}, content={repr(choice.message.content)[:200]}")

    content = choice.message.content
    if not content:
        # content가 비어있으면 직접 텍스트로 결과 포맷하여 반환
        logger.warning("[LLM-ANS] content 비어있음 → 직접 포맷 반환")
        lines = [f"DB 쿼리 결과 ({len(query_result)}행):"]
        for i, row in enumerate(query_result, 1):
            parts = ", ".join(f"{k}: {v}" for k, v in row.items())
            lines.append(f"  {i}. {parts}")
        return "\n".join(lines)
    return content.strip()


async def _answer_with_context(
    analysis_summary: dict,
    aggregated_data: dict,
    messages: list[dict],
    user_question: str,
) -> str:
    """기존 방식: 집계 데이터 컨텍스트 기반 답변"""
    base_prompt = _build_system_prompt(analysis_summary, aggregated_data)

    # 데이터 정직성 규칙 추가
    honesty_rules = """
## 중요 규칙
- 아래 제공된 데이터에만 근거하여 답변하세요.
- 데이터에 없는 세부 조건(특정 날짜/월별 필터 등)을 물어보면,
  "현재 분석 데이터에는 해당 기간별 세부 데이터가 없습니다. 대신 전체 기간 기준으로 알려드리겠습니다:"
  라고 먼저 안내한 뒤, 가진 데이터 내에서 최대한 유사한 답을 주세요.
- 지점별 질문은 반드시 "지점별 매출 및 인기 상품 TOP3" 섹션의 데이터를 우선 사용하세요.
- 전체 TOP5 데이터를 지점별 질문의 답으로 사용하지 마세요.
"""
    system_prompt = base_prompt + honesty_rules

    conversation = [{"role": "system", "content": system_prompt}]
    for msg in messages[-20:]:
        conversation.append({"role": msg["role"], "content": msg["content"]})
    conversation.append({"role": "user", "content": user_question})

    response = await client.chat.completions.create(
        model=MODEL,
        messages=conversation,
        max_completion_tokens=16384,
    )

    choice = response.choices[0]
    logger.warning(f"[LLM] finish_reason={choice.finish_reason}")
    content = choice.message.content
    if not content:
        return "응답 내용이 비어있습니다. 모델이 해당 질문에 응답하지 못했습니다."
    return content.strip()


# ── 포맷 헬퍼 ──────────────────────────────────────────────────────────────

def _format_query_result(rows: list) -> str:
    if not rows:
        return "  결과 없음 (해당 조건의 데이터가 없습니다)"
    lines = []
    for i, row in enumerate(rows, 1):
        row_dict = row if isinstance(row, dict) else dict(row)
        parts = ", ".join(f"{k}={v}" for k, v in row_dict.items())
        lines.append(f"  {i}. {parts}")
    return "\n".join(lines)


def _format_basic_stats(summary: dict) -> str:
    basic = summary.get("basic_stats", {})
    return (
        f"- 총 매출: {_fmt(basic.get('total_revenue', 'N/A'), '원')}\n"
        f"- 총 거래 건수: {_fmt(basic.get('total_transactions', 'N/A'), '건')}\n"
        f"- 평균 객단가: {_fmt(basic.get('avg_order_value', 'N/A'), '원')}"
    )


def _fmt(value, unit: str = "") -> str:
    """숫자면 천 단위 콤마 포맷, 아니면 그대로 반환."""
    try:
        return f"{float(value):,.0f}{unit}"
    except (TypeError, ValueError):
        return str(value)


def _build_system_prompt(summary: dict, aggregated_data: dict) -> str:
    basic = summary.get("basic_stats", {})
    trend = summary.get("trend", {})
    product = summary.get("product_strategy", {})
    stores = summary.get("store_analysis", {})

    # 지점별 TOP3 상품 섹션 생성
    store_lines = []
    for store_name, store_data in stores.items():
        top3 = store_data.get("top3_products", [])
        top3_str = ", ".join(
            f"{p.get('product_name', '?')}({p.get('quantity', 0)}개)"
            for p in top3
        )
        store_lines.append(
            f"  - {store_name}: 총매출 {_fmt(store_data.get('total_revenue', 0), '원')} "
            f"| 거래 {_fmt(store_data.get('total_transactions', 0), '건')} "
            f"| TOP3 상품: {top3_str or '없음'}"
        )
    store_section = "\n".join(store_lines) if store_lines else "  데이터 없음"

    prompt = f"""당신은 매출 데이터 분석 전문 AI 어시스턴트입니다.
아래 분석된 데이터를 기반으로 사용자의 질문에 한국어로 정확하고 친절하게 답변하세요.
추측이 아닌 주어진 데이터에 근거하여 답변하세요.

## 기초 통계
- 총 매출: {_fmt(basic.get('total_revenue', 'N/A'), '원')}
- 총 거래 건수: {_fmt(basic.get('total_transactions', 'N/A'), '건')}
- 평균 객단가: {_fmt(basic.get('avg_order_value', 'N/A'), '원')}

## 피크 타임
- 최고 매출 시간대: {trend.get('peak_hour_label', 'N/A')} (매출: {_fmt(trend.get('peak_revenue', 'N/A'), '원')})

## TOP 5 상품 (판매량 기준)
{_format_list(product.get('top5_by_quantity', []), 'product_name', 'total_quantity', '개')}

## TOP 5 상품 (매출 기여도 기준)
{_format_list(product.get('top5_by_revenue', []), 'product_name', 'total_revenue', '원')}

## 지점별 매출 및 인기 상품 TOP3
{store_section}

## 실시간 집계 데이터
{_format_aggregated(aggregated_data)}
"""
    return prompt


def _format_list(items: list, name_key: str, value_key: str, unit: str) -> str:
    if not items:
        return "  데이터 없음"
    lines = []
    for i, item in enumerate(items, 1):
        val = item.get(value_key, 0)
        lines.append(f"  {i}. {item.get(name_key, '?')} - {val:,.0f}{unit}")
    return "\n".join(lines)


def _format_aggregated(data: dict) -> str:
    if not data:
        return "  없음"
    lines = []
    for key, val in data.items():
        lines.append(f"  - {key}: {val}")
    return "\n".join(lines)
