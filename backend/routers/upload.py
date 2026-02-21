import uuid
import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Analysis, CsvRow
from services.analyzer import analyze_csv

router = APIRouter(prefix="/api", tags=["upload"])

ALLOWED_EXTENSIONS = {".csv"}


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """CSV 파일을 업로드하고 Pandas로 분석 후 DB에 저장"""
    # 파일 확장자 체크
    filename = file.filename or "unknown.csv"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="CSV 파일만 업로드 가능합니다.")

    # CSV 읽기
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV 파싱 오류: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="빈 CSV 파일입니다.")

    # Pandas 분석
    try:
        result = analyze_csv(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 분석 오류: {str(e)}")

    # Analysis 레코드 생성
    analysis_id = str(uuid.uuid4())
    analysis = Analysis(
        id=analysis_id,
        filename=filename,
        summary=result["summary"],
        chart_data=result["chart_data"],
        insights=result["insights"],
    )
    db.add(analysis)

    # CSV 원본 행 저장 (컬럼명 소문자 정규화 후 저장)
    df_normalized = df.copy()
    df_normalized.columns = [c.strip().lower().replace(" ", "_") for c in df_normalized.columns]

    rows_to_insert = []
    for _, row in df_normalized.iterrows():
        csv_row = CsvRow(
            analysis_id=analysis_id,
            transaction_id=_safe_str(row, "transaction_id"),
            date=_safe_str(row, "date"),
            time=_safe_str(row, "time"),
            category=_safe_str(row, "category"),
            product_name=_safe_str(row, "product_name"),
            price=_safe_float(row, "price"),
            quantity=_safe_int(row, "quantity"),
            payment_method=_safe_str(row, "payment_method"),
            store_location=_safe_str(row, "store_location"),
            total_amount=_safe_float(row, "total_amount"),
            age_group=_safe_str(row, "age_group"),
        )
        rows_to_insert.append(csv_row)

    db.bulk_save_objects(rows_to_insert)
    db.commit()
    db.refresh(analysis)

    return {
        "id": analysis.id,
        "filename": analysis.filename,
        "uploaded_at": analysis.uploaded_at,
        "summary": analysis.summary,
        "chart_data": analysis.chart_data,
        "insights": analysis.insights,
        "row_count": len(rows_to_insert),
    }


def _safe_str(row, col):
    val = row.get(col)
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return str(val)


def _safe_float(row, col):
    try:
        val = row.get(col)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        return float(val)
    except Exception:
        return None


def _safe_int(row, col):
    try:
        val = row.get(col)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        return int(val)
    except Exception:
        return None
