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
