"""
MCP 서버 - Claude Desktop 연동
Claude Desktop의 claude_desktop_config.json에 아래와 같이 설정:

{
  "mcpServers": {
    "data-analytics": {
      "command": "python",
      "args": ["/absolute/path/to/backend/mcp_server.py"]
    }
  }
}
"""

import asyncio
import json
import sys
import os

# 백엔드 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from database import SessionLocal, init_db
from models import Analysis, ChatMessage, CsvRow
from services.llm import chat_with_analysis
from sqlalchemy import text

# DB 초기화
init_db()

server = Server("data-analytics")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_analyses",
            description="업로드된 CSV 분석 기록 목록을 반환합니다.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_analysis",
            description="특정 analysis_id의 분석 결과 상세를 반환합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "analysis_id": {
                        "type": "string",
                        "description": "조회할 분석 기록의 UUID",
                    }
                },
                "required": ["analysis_id"],
            },
        ),
        Tool(
            name="query_data",
            description="CSV 데이터를 SQL로 집계합니다. question_type: hourly | category | product | store | payment",
            inputSchema={
                "type": "object",
                "properties": {
                    "analysis_id": {"type": "string"},
                    "question_type": {
                        "type": "string",
                        "enum": ["hourly", "category", "product", "store", "payment"],
                    },
                },
                "required": ["analysis_id", "question_type"],
            },
        ),
        Tool(
            name="chat_with_data",
            description="특정 분석 데이터를 기반으로 AI에게 질문하고 답변을 받습니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "analysis_id": {"type": "string"},
                    "question": {"type": "string", "description": "사용자 질문"},
                },
                "required": ["analysis_id", "question"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    db = SessionLocal()
    try:
        if name == "list_analyses":
            analyses = db.query(Analysis).order_by(Analysis.uploaded_at.desc()).all()
            result = [
                {
                    "id": a.id,
                    "filename": a.filename,
                    "uploaded_at": str(a.uploaded_at),
                    "total_revenue": (
                        a.summary.get("basic_stats", {}).get("total_revenue")
                        if a.summary else None
                    ),
                }
                for a in analyses
            ]
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "get_analysis":
            analysis_id = arguments["analysis_id"]
            analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if not analysis:
                return [TextContent(type="text", text="분석 기록을 찾을 수 없습니다.")]
            result = {
                "id": analysis.id,
                "filename": analysis.filename,
                "uploaded_at": str(analysis.uploaded_at),
                "summary": analysis.summary,
                "insights": analysis.insights,
            }
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "query_data":
            analysis_id = arguments["analysis_id"]
            question_type = arguments["question_type"]

            query_map = {
                "hourly": """
                    SELECT substr(time,1,2) as hour, ROUND(SUM(total_amount),2), COUNT(*)
                    FROM csv_rows WHERE analysis_id=:aid GROUP BY hour ORDER BY hour
                """,
                "category": """
                    SELECT category, ROUND(SUM(total_amount),2), SUM(quantity)
                    FROM csv_rows WHERE analysis_id=:aid GROUP BY category ORDER BY 2 DESC
                """,
                "product": """
                    SELECT product_name, SUM(quantity), ROUND(SUM(total_amount),2)
                    FROM csv_rows WHERE analysis_id=:aid GROUP BY product_name ORDER BY 3 DESC LIMIT 20
                """,
                "store": """
                    SELECT store_location, ROUND(SUM(total_amount),2), COUNT(*)
                    FROM csv_rows WHERE analysis_id=:aid GROUP BY store_location ORDER BY 2 DESC
                """,
                "payment": """
                    SELECT payment_method, COUNT(*), ROUND(SUM(total_amount),2)
                    FROM csv_rows WHERE analysis_id=:aid GROUP BY payment_method ORDER BY 2 DESC
                """,
            }

            sql = query_map.get(question_type)
            if not sql:
                return [TextContent(type="text", text="지원하지 않는 question_type입니다.")]

            rows = db.execute(text(sql), {"aid": analysis_id}).fetchall()
            result = [list(r) for r in rows]
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "chat_with_data":
            analysis_id = arguments["analysis_id"]
            question = arguments["question"]

            analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if not analysis:
                return [TextContent(type="text", text="분석 기록을 찾을 수 없습니다.")]

            history = (
                db.query(ChatMessage)
                .filter(ChatMessage.analysis_id == analysis_id)
                .order_by(ChatMessage.created_at.asc())
                .all()
            )
            history_dicts = [{"role": m.role, "content": m.content} for m in history]

            answer = await chat_with_analysis(
                analysis_summary=analysis.summary or {},
                aggregated_data={},
                messages=history_dicts,
                user_question=question,
            )
            return [TextContent(type="text", text=answer)]

        else:
            return [TextContent(type="text", text=f"알 수 없는 도구: {name}")]
    finally:
        db.close()


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
