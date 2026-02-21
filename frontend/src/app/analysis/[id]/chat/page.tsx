"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import axios from "axios";

const API = process.env.NEXT_PUBLIC_API_URL;

interface Message { id: string; role: "user" | "assistant"; content: string; created_at?: string; }
interface Analysis { filename: string; summary: { basic_stats?: { total_revenue: number; total_transactions: number } } }

export default function ChatPage() {
    const { id } = useParams<{ id: string }>();
    const [analysis, setAnalysis] = useState<Analysis | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [initLoading, setInitLoading] = useState(true);
    const bottomRef = useRef<HTMLDivElement>(null);

    const fmt = (n: number) => n?.toLocaleString("ko-KR") ?? "-";

    // 초기 데이터 로드
    useEffect(() => {
        Promise.all([
            axios.get(`${API}/api/analyses/${id}`),
            axios.get(`${API}/api/analyses/${id}/chat`),
        ]).then(([aRes, cRes]) => {
            setAnalysis(aRes.data);
            setMessages(cRes.data.map((m: Message) => ({ ...m })));
        }).finally(() => setInitLoading(false));
    }, [id]);

    // 스크롤 최하단 이동
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    const sendMessage = async () => {
        const q = input.trim();
        if (!q || loading) return;
        setInput("");
        const userMsg: Message = { id: Date.now().toString(), role: "user", content: q };
        setMessages(prev => [...prev, userMsg]);
        setLoading(true);
        try {
            const res = await axios.post(`${API}/api/analyses/${id}/chat`, { question: q });
            const aiMsg: Message = { id: (Date.now() + 1).toString(), role: "assistant", content: res.data.answer };
            setMessages(prev => [...prev, aiMsg]);
        } catch {
            const errMsg: Message = { id: (Date.now() + 1).toString(), role: "assistant", content: "죄송합니다. 답변 생성 중 오류가 발생했습니다." };
            setMessages(prev => [...prev, errMsg]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    };

    const SUGGESTIONS = [
        "피크 타임이 언제야?",
        "가장 많이 팔린 상품은?",
        "지점별 매출 차이는?",
        "결제 수단 중 가장 많이 사용된 건?",
        "매출 개선을 위한 제안을 해줘",
    ];

    if (initLoading) return (
        <div className="flex justify-center items-center min-h-[60vh]">
            <div className="w-10 h-10 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
        </div>
    );

    return (
        <div className="flex flex-col h-[calc(100vh-64px)]">
            {/* 상단 헤더 */}
            <div className="border-b border-gray-800 bg-gray-950/90 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Link href={`/analysis/${id}`} className="text-gray-500 hover:text-gray-300 transition-colors">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                    </Link>
                    <div>
                        <p className="text-white font-medium text-sm">{analysis?.filename ?? "분석 기록"}</p>
                        {analysis?.summary?.basic_stats && (
                            <p className="text-gray-500 text-xs">
                                총 매출 ₩{fmt(analysis.summary.basic_stats.total_revenue)} · {fmt(analysis.summary.basic_stats.total_transactions)}건
                            </p>
                        )}
                    </div>
                </div>
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-violet-500/10 border border-violet-500/20">
                    <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
                    <span className="text-violet-400 text-xs font-medium">AI 분석 챗봇</span>
                </div>
            </div>

            {/* 메시지 영역 */}
            <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
                {messages.length === 0 && (
                    <div className="text-center py-10">
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500/20 to-indigo-500/20 border border-violet-500/20 flex items-center justify-center mx-auto mb-4">
                            <svg className="w-7 h-7 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                        </div>
                        <p className="text-gray-300 font-medium mb-1">데이터 기반 AI 챗봇</p>
                        <p className="text-gray-500 text-sm mb-6">업로드한 매출 데이터를 분석하여 질문에 답변합니다.</p>
                        <div className="flex flex-wrap justify-center gap-2">
                            {SUGGESTIONS.map((s) => (
                                <button
                                    key={s}
                                    onClick={() => { setInput(s); }}
                                    className="px-3 py-1.5 rounded-full bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm transition-colors border border-gray-700"
                                >
                                    {s}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                        {msg.role === "assistant" && (
                            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center mr-2 mt-1 flex-shrink-0">
                                <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                                </svg>
                            </div>
                        )}
                        <div
                            className={`chat-bubble max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${msg.role === "user"
                                    ? "bg-violet-600 text-white rounded-tr-sm"
                                    : "bg-gray-800 text-gray-100 rounded-tl-sm border border-gray-700"
                                }`}
                        >
                            {msg.content}
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="flex justify-start">
                        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center mr-2 mt-1">
                            <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                        </div>
                        <div className="bg-gray-800 border border-gray-700 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1">
                            <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
                            <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
                            <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                        </div>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            {/* 입력창 */}
            <div className="border-t border-gray-800 bg-gray-950/90 px-4 py-4">
                <div className="max-w-4xl mx-auto flex gap-3">
                    <textarea
                        id="chat-input"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="데이터에 대해 질문하세요... (Enter로 전송)"
                        rows={1}
                        className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-gray-100 placeholder-gray-500 text-sm resize-none focus:outline-none focus:border-violet-500 transition-colors"
                        style={{ minHeight: "48px", maxHeight: "120px" }}
                    />
                    <button
                        id="send-button"
                        onClick={sendMessage}
                        disabled={!input.trim() || loading}
                        className="px-4 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                    </button>
                </div>
                <p className="text-center text-gray-600 text-xs mt-2">Shift+Enter로 줄바꿈</p>
            </div>
        </div>
    );
}
