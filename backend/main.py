from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import upload, analysis, chat

app = FastAPI(
    title="데이터 분석 API",
    description="CSV 매출 데이터 분석 및 AI 챗봇 서비스",
    version="1.0.0",
)

# CORS (Next.js 개발 서버 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}
