"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import axios from "axios";
import {
    AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend
} from "recharts";

const API = process.env.NEXT_PUBLIC_API_URL;

const COLORS = ["#8b5cf6", "#6366f1", "#3b82f6", "#06b6d4", "#10b981"];

interface Analysis {
    id: string;
    filename: string;
    uploaded_at: string;
    row_count: number;
    summary: {
        basic_stats?: { total_revenue: number; total_transactions: number; avg_order_value: number };
        trend?: { peak_hour_label: string; peak_revenue: number };
        product_strategy?: {
            top5_by_quantity: { product_name: string; total_quantity: number }[];
            top5_by_revenue: { product_name: string; total_revenue: number; contribution_pct: number }[];
        };
        store_analysis?: Record<string, { total_revenue: number; total_transactions: number; avg_order_value: number; top3_products: unknown[] }>;
    };
    chart_data: {
        hourly_sales?: { hour: string; revenue: number; transactions: number }[];
        top_products?: {
            top5_quantity: { product_name: string; total_quantity: number }[];
            top5_revenue: { product_name: string; total_revenue: number }[];
        };
        store_comparison?: { store: string; revenue: number; transactions: number }[];
    };
    insights: { positives: string[]; negatives: string[] };
}

export default function AnalysisDetailPage() {
    const { id } = useParams<{ id: string }>();
    const [data, setData] = useState<Analysis | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        axios.get(`${API}/api/analyses/${id}`)
            .then(res => setData(res.data))
            .finally(() => setLoading(false));
    }, [id]);

    if (loading) return (
        <div className="flex justify-center items-center min-h-[60vh]">
            <div className="w-10 h-10 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
        </div>
    );
    if (!data) return <div className="text-center py-20 text-gray-500">분석 기록을 찾을 수 없습니다.</div>;

    const bs = data.summary?.basic_stats;
    const trend = data.summary?.trend;
    const products = data.summary?.product_strategy;
    const stores = data.summary?.store_analysis;
    const hourlySales = data.chart_data?.hourly_sales || [];
    const storeChart = data.chart_data?.store_comparison || [];
    const top5qty = data.chart_data?.top_products?.top5_quantity || [];
    const top5rev = data.chart_data?.top_products?.top5_revenue || [];

    const fmt = (n: number) => n?.toLocaleString("ko-KR") ?? "-";
    const fmtDate = (s: string) =>
        new Date(s).toLocaleString("ko-KR", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });

    return (
        <div className="max-w-6xl mx-auto px-4 py-10">
            {/* 헤더 */}
            <div className="flex items-start justify-between mb-8">
                <div>
                    <div className="flex items-center gap-2 text-gray-500 text-sm mb-2">
                        <Link href="/history" className="hover:text-gray-300 transition-colors">분석 기록</Link>
                        <span>/</span>
                        <span className="text-gray-300">{data.filename}</span>
                    </div>
                    <h1 className="text-2xl font-bold text-white">{data.filename}</h1>
                    <p className="text-gray-500 text-sm mt-1">{fmtDate(data.uploaded_at)} · {fmt(data.row_count)}개 거래</p>
                </div>
                <Link
                    href={`/analysis/${id}/chat`}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white text-sm font-medium transition-all"
                >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                    AI에게 질문하기
                </Link>
            </div>

            {/* 기초 통계 카드 */}
            {bs && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                    <StatCard label="총 매출" value={`₩${fmt(bs.total_revenue)}`} icon="💰" color="violet" />
                    <StatCard label="총 거래 건수" value={`${fmt(bs.total_transactions)}건`} icon="🧾" color="indigo" />
                    <StatCard label="평균 객단가" value={`₩${fmt(bs.avg_order_value)}`} icon="📊" color="blue" />
                </div>
            )}

            {/* 피크 타임 배너 */}
            {trend && (
                <div className="mb-8 p-4 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center gap-3">
                    <span className="text-2xl">⚡</span>
                    <div>
                        <p className="text-violet-300 font-semibold">피크 타임: {trend.peak_hour_label}</p>
                        <p className="text-gray-400 text-sm">해당 시간대 최고 매출 ₩{fmt(trend.peak_revenue)}</p>
                    </div>
                </div>
            )}

            {/* 시간대별 매출 차트 */}
            {hourlySales.length > 0 && (
                <ChartCard title="시간대별 매출 흐름">
                    <ResponsiveContainer width="100%" height={250}>
                        <AreaChart data={hourlySales}>
                            <defs>
                                <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                            <XAxis dataKey="hour" tick={{ fill: "#6b7280", fontSize: 11 }} />
                            <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} tickFormatter={(v) => `₩${(v / 1000).toFixed(0)}k`} />
                            <Tooltip
                                contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: "12px" }}
                                labelStyle={{ color: "#e5e7eb" }}
                                formatter={(v: number) => [`₩${fmt(v)}`, "매출"]}
                            />
                            <Area type="monotone" dataKey="revenue" stroke="#8b5cf6" strokeWidth={2} fill="url(#revGrad)" />
                        </AreaChart>
                    </ResponsiveContainer>
                </ChartCard>
            )}

            {/* 상품 전략 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                {top5qty.length > 0 && (
                    <ChartCard title="TOP 5 상품 (판매량)">
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={top5qty} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
                                <XAxis type="number" tick={{ fill: "#6b7280", fontSize: 11 }} />
                                <YAxis dataKey="product_name" type="category" tick={{ fill: "#9ca3af", fontSize: 11 }} width={120} />
                                <Tooltip
                                    contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: "12px" }}
                                    formatter={(v: number) => [`${fmt(v)}개`, "판매량"]}
                                />
                                <Bar dataKey="total_quantity" fill="#8b5cf6" radius={[0, 6, 6, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </ChartCard>
                )}
                {top5rev.length > 0 && (
                    <ChartCard title="TOP 5 상품 (매출 기여도)">
                        <ResponsiveContainer width="100%" height={220}>
                            <PieChart>
                                <Pie data={top5rev} dataKey="total_revenue" nameKey="product_name" cx="50%" cy="50%" outerRadius={80} label={false}>
                                    {top5rev.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: "12px" }}
                                    formatter={(v: number) => [`₩${fmt(v)}`, "매출"]}
                                />
                                <Legend iconType="circle" wrapperStyle={{ color: "#9ca3af", fontSize: "12px" }} />
                            </PieChart>
                        </ResponsiveContainer>
                    </ChartCard>
                )}
            </div>

            {/* 지점별 매출 비교 */}
            {storeChart.length > 0 && (
                <ChartCard title="지점별 매출 비교" className="mt-6">
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={storeChart}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                            <XAxis dataKey="store" tick={{ fill: "#6b7280", fontSize: 11 }} />
                            <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} tickFormatter={(v) => `₩${(v / 1000).toFixed(0)}k`} />
                            <Tooltip
                                contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: "12px" }}
                                formatter={(v: number) => [`₩${fmt(v)}`, "매출"]}
                            />
                            <Bar dataKey="revenue" fill="#6366f1" radius={[6, 6, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </ChartCard>
            )}

            {/* 인사이트 */}
            {(data.insights?.positives?.length > 0 || data.insights?.negatives?.length > 0) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                    {data.insights.positives.length > 0 && (
                        <div className="p-5 rounded-2xl bg-emerald-500/5 border border-emerald-500/20">
                            <h3 className="text-emerald-400 font-semibold mb-3 flex items-center gap-2">
                                <span>✅</span> 긍정적 인사이트
                            </h3>
                            <ul className="space-y-2">
                                {data.insights.positives.map((txt, i) => (
                                    <li key={i} className="text-gray-300 text-sm leading-relaxed">{txt}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                    {data.insights.negatives.length > 0 && (
                        <div className="p-5 rounded-2xl bg-amber-500/5 border border-amber-500/20">
                            <h3 className="text-amber-400 font-semibold mb-3 flex items-center gap-2">
                                <span>⚠️</span> 개선 포인트
                            </h3>
                            <ul className="space-y-2">
                                {data.insights.negatives.map((txt, i) => (
                                    <li key={i} className="text-gray-300 text-sm leading-relaxed">{txt}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}

            {/* 지점별 상세 표 */}
            {stores && Object.keys(stores).length > 0 && (
                <div className="mt-6 p-5 rounded-2xl bg-gray-900/60 border border-gray-800">
                    <h3 className="text-white font-semibold mb-4">지점별 상세 통계</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="text-gray-500 border-b border-gray-800">
                                    <th className="text-left pb-3 pr-4">지점</th>
                                    <th className="text-right pb-3 pr-4">총 매출</th>
                                    <th className="text-right pb-3 pr-4">거래 건수</th>
                                    <th className="text-right pb-3">평균 객단가</th>
                                </tr>
                            </thead>
                            <tbody>
                                {Object.entries(stores).map(([store, s]) => (
                                    <tr key={store} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                                        <td className="py-3 pr-4 text-gray-300 font-medium">{store}</td>
                                        <td className="py-3 pr-4 text-right text-white">₩{fmt(s.total_revenue)}</td>
                                        <td className="py-3 pr-4 text-right text-gray-400">{fmt(s.total_transactions)}건</td>
                                        <td className="py-3 text-right text-gray-400">₩{fmt(s.avg_order_value)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}

function StatCard({ label, value, icon }: { label: string; value: string; icon: string; color: string }) {
    return (
        <div className="p-5 rounded-2xl bg-gray-900/60 border border-gray-800">
            <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{icon}</span>
                <p className="text-gray-400 text-sm">{label}</p>
            </div>
            <p className="text-2xl font-bold text-white">{value}</p>
        </div>
    );
}

function ChartCard({ title, children, className = "" }: { title: string; children: React.ReactNode; className?: string }) {
    return (
        <div className={`p-5 rounded-2xl bg-gray-900/60 border border-gray-800 ${className}`}>
            <h3 className="text-white font-semibold mb-4">{title}</h3>
            {children}
        </div>
    );
}
