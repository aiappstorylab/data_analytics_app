# DataIQ - 매출 데이터 분석 플랫폼

CSV 매출 데이터를 업로드하면 AI가 자동으로 분석하고, 챗봇으로 질문할 수 있는 풀스택 웹 애플리케이션입니다.

---

## 🚀 빠른 시작

### 1. 백엔드 설정

```bash
cd backend

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate   # macOS / Linux

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 OPENAI_API_KEY 입력

# 서버 실행 (포트 8000)
uvicorn main:app --reload
```

### 2. 프론트엔드 설정

```bash
cd frontend
npm install
npm run dev   # 포트 3000
```

이제 브라우저에서 http://localhost:3000 접속!

---

## 🔌 Claude Desktop MCP 연동

`claude_desktop_config.json`에 아래를 추가하세요:

```json
{
  "mcpServers": {
    "data-analytics": {
      "command": "/Users/elzenaro/workspace/data_analytics_app/backend/venv/bin/python",
      "args": ["/Users/elzenaro/workspace/data_analytics_app/backend/mcp_server.py"]
    }
  }
}
```

> Claude Desktop 재시작 후 `list_analyses`, `get_analysis`, `query_data`, `chat_with_data` 도구 사용 가능

---

## 📁 프로젝트 구조

```
data_analytics_app/
├── backend/
│   ├── main.py              # FastAPI 앱
│   ├── models.py            # DB 모델 (Analysis, CsvRow, ChatMessage)
│   ├── database.py          # SQLite 설정
│   ├── mcp_server.py        # MCP 서버 (Claude Desktop)
│   ├── routers/
│   │   ├── upload.py        # CSV 업로드 API
│   │   ├── analysis.py      # 분석 기록 CRUD
│   │   └── chat.py          # AI 챗봇 API
│   └── services/
│       ├── analyzer.py      # Pandas 분석 엔진
│       └── llm.py           # OpenAI 연동
└── frontend/
    └── src/app/
        ├── page.tsx                    # 홈 (CSV 업로드)
        ├── history/page.tsx            # 분석 기록 목록
        └── analysis/[id]/
            ├── page.tsx               # 분석 결과 + 차트
            └── chat/page.tsx          # AI 챗봇
```

---

## 🤖 지원 데이터 컬럼

| 컬럼 | 설명 |
|------|------|
| Transaction_ID | 거래 고유 ID |
| Date | 날짜 |
| Time | 시간 (HH:MM:SS) |
| Category | 카테고리 |
| Product_Name | 상품명 |
| Price | 단가 |
| Quantity | 수량 |
| Payment_Method | 결제수단 |
| Store_Location | 지점명 |
| Total_Amount | 총 금액 |
| Age_Group | 연령대 |

---

## 📊 분석 항목

1. **기초 통계** - 총 매출, 거래 건수, 평균 객단가
2. **트렌드** - 시간대별 매출 흐름 + 피크 타임 특정
3. **상품 전략** - 판매량 TOP 5 / 매출 기여도 TOP 5
4. **지점별 분석** - 지점별 매출, 거래 건수, 인기 상품
5. **인사이트** - 긍정적 요소 / 개선 포인트 자동 도출

---

## 🗂️ 샘플 데이터

`sample_data_code/` 폴더에 테스트용 CSV 파일과 생성 코드가 포함되어 있습니다.

### 바로 사용하기

`sample_data_code/cvs_sales_with_age_1.csv` 또는 `cvs_sales_with_age_2.csv` 파일을 앱에 직접 업로드하세요.

### 새 샘플 데이터 생성하기

```bash
cd sample_data_code

# 의존성 설치 (최초 1회)
pip install pandas numpy

# 샘플 데이터 생성
python sample_data.py
# → cvs_sales_with_age.csv 파일이 생성됩니다
```

### 생성 데이터 스펙

| 항목 | 내용 |
|------|------|
| 레코드 수 | 3,000건 (기본값) |
| 지점 | Gangnam / Sinsa / Mapo / Hongdae / Yeouido |
| 연령대 | 10s / 20s / 30s / 40s / 50s / 60s+ |
| 카테고리 | Fresh Food / Beverage / Instant Food / Snack / Alcohol / Tobacco |
| 결제수단 | Credit Card / Mobile Pay / Cash / Points |
| 날짜 범위 | 시작일로부터 45일 (랜덤) |

### 커스터마이징

`sample_data.py` 상단의 설정값을 수정하여 원하는 데이터를 생성할 수 있습니다:

```python
num_records = 3000            # 생성할 레코드 수
start_date = datetime(2026, 3, 1)  # 시작 날짜
locations = ['Gangnam', ...]  # 지점 목록
age_groups = ['10s', ...]     # 연령대 목록
age_weights = [15, 30, ...]   # 연령대 가중치 (2030세대 편의점 이용 빈도 반영)
```

> **참고:** 연령대별 카테고리 구매 패턴이 사전 설정되어 있습니다 (10대 → 간식/라면 위주, 40-50대 → 주류/담배 비중 높음).
