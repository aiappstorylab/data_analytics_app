import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# 항상 이 파일(database.py)이 있는 디렉토리 기준으로 DB 경로를 결정
# MCP 서버처럼 다른 cwd에서 실행될 때도 정확히 찾을 수 있도록 절대 경로 사용
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_DB = f"sqlite:///{os.path.join(_BASE_DIR, 'analytics.db')}"
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DB)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite only
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from models import Analysis, CsvRow, ChatMessage  # noqa
    Base.metadata.create_all(bind=engine)
