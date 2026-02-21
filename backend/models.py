import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    summary = Column(JSON, nullable=True)        # 기초통계, 트렌드, 상품전략 등
    chart_data = Column(JSON, nullable=True)     # 차트 렌더링용 raw data
    insights = Column(JSON, nullable=True)       # 긍정/부정 인사이트

    rows = relationship("CsvRow", back_populates="analysis", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="analysis", cascade="all, delete-orphan")


class CsvRow(Base):
    __tablename__ = "csv_rows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    transaction_id = Column(String, nullable=True)
    date = Column(String, nullable=True)
    time = Column(String, nullable=True)
    category = Column(String, nullable=True)
    product_name = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=True)
    payment_method = Column(String, nullable=True)
    store_location = Column(String, nullable=True)
    total_amount = Column(Float, nullable=True)
    age_group = Column(String, nullable=True)

    analysis = relationship("Analysis", back_populates="rows")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    role = Column(String, nullable=False)        # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("Analysis", back_populates="messages")
