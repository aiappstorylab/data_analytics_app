"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import axios from "axios";

const API = process.env.NEXT_PUBLIC_API_URL;

interface AnalysisSummary {
    id: string;
    filename: string;
    uploaded_at: string;
    basic_stats: {
        total_revenue: number;
        total_transactions: number;
        avg_order_value: number;
    } | null;
}

export default function HistoryPage() {
    const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [deleting, setDeleting] = useState<string | null>(null);

    const fetchAnalyses = async () => {
        try {
            const res = await axios.get(`${API}/api/analyses`);
            setAnalyses(res.data);
        } catch {
            /* ignore */
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchAnalyses(); }, []);

    const handleDelete = async (id: string, filename: string) => {
        if (!confirm(`"${filename}" 분석 기록을 삭제하시겠습니까?\n관련 CSV 데이터와 분석 기록이 모두 삭제됩니다.`)) return;
        setDeleting(id);
        try {
            await axios.delete(`${API}/api/analyses/${id}`);
            setAnalyses((prev) => prev.filter((a) => a.id !== id));
        } catch {
            alert("삭제 중 오류가 발생했습니다.");
        } finally {
            setDeleting(null);
        }
    };

    const fmt = (n: number) => n?.toLocaleString("ko-KR") ?? "-";
    const fmtDate = (s: string) =>
        new Date(s).toLocaleString("ko-KR", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });

    return (
        <div className="max-w-5xl mx-auto px-4 py-12">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-white">분석 기록</h1>
                    <p className="text-gray-500 text-sm mt-1">업로드한 CSV 파일의 분석 기록을 열람합니다.</p>
                </div>
                <Link href="/" className="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors">
                    + 새 분석
                </Link>
            </div>

            {loading ? (
                <div className="flex justify-center py-20">
                    <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
                </div>
            ) : analyses.length === 0 ? (
                <div className="text-center py-20">
                    <div className="w-16 h-16 rounded-2xl bg-gray-900 flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                    </div>
                    <p className="text-gray-500">아직 분석 기록이 없습니다.</p>
                    <Link href="/" className="mt-4 inline-block text-violet-400 hover:text-violet-300 text-sm underline">
                        CSV 파일 업로드하기
                    </Link>
                </div>
            ) : (
                <div className="grid gap-4">
                    {analyses.map((a) => (
                        <div key={a.id} className="group p-5 rounded-2xl bg-gray-900/60 border border-gray-800 hover:border-gray-700 transition-all">
                            <div className="flex items-start justify-between gap-4">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <svg className="w-4 h-4 text-violet-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                        </svg>
                                        <span className="font-medium text-white truncate">{a.filename}</span>
                                    </div>
                                    <p className="text-gray-500 text-xs mb-3">{fmtDate(a.uploaded_at)}</p>

                                    {a.basic_stats && (
                                        <div className="flex flex-wrap gap-4">
                                            <Stat label="총 매출" value={`₩${fmt(a.basic_stats.total_revenue)}`} />
                                            <Stat label="거래 건수" value={`${fmt(a.basic_stats.total_transactions)}건`} />
                                            <Stat label="평균 객단가" value={`₩${fmt(a.basic_stats.avg_order_value)}`} />
                                        </div>
                                    )}
                                </div>

                                <div className="flex items-center gap-2 flex-shrink-0">
                                    <Link
                                        href={`/analysis/${a.id}`}
                                        className="px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs font-medium transition-colors"
                                    >
                                        상세 보기
                                    </Link>
                                    <Link
                                        href={`/analysis/${a.id}/chat`}
                                        className="px-3 py-1.5 rounded-lg bg-violet-500/10 hover:bg-violet-500/20 text-violet-400 text-xs font-medium transition-colors border border-violet-500/20"
                                    >
                                        AI 질문
                                    </Link>
                                    <button
                                        id={`delete-${a.id}`}
                                        onClick={() => handleDelete(a.id, a.filename)}
                                        disabled={deleting === a.id}
                                        className="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-medium transition-colors border border-red-500/20 disabled:opacity-40"
                                    >
                                        {deleting === a.id ? "삭제 중..." : "삭제"}
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function Stat({ label, value }: { label: string; value: string }) {
    return (
        <div>
            <p className="text-xs text-gray-500">{label}</p>
            <p className="text-sm font-semibold text-white">{value}</p>
        </div>
    );
}
