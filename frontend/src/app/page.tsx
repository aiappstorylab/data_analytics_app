"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";

const API = process.env.NEXT_PUBLIC_API_URL;

export default function UploadPage() {
    const router = useRouter();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [dragging, setDragging] = useState(false);
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleFile = useCallback((f: File) => {
        if (!f.name.endsWith(".csv")) {
            setError("CSV 파일만 업로드 가능합니다.");
            return;
        }
        setFile(f);
        setError(null);
    }, []);

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setDragging(false);
        const f = e.dataTransfer.files[0];
        if (f) handleFile(f);
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const f = e.target.files?.[0];
        if (f) handleFile(f);
    };

    const handleUpload = async () => {
        if (!file) return;
        setLoading(true);
        setError(null);
        const formData = new FormData();
        formData.append("file", file);
        try {
            const res = await axios.post(`${API}/api/upload`, formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            router.push(`/analysis/${res.data.id}`);
        } catch (err: unknown) {
            const error = err as { response?: { data?: { detail?: string } } };
            setError(error.response?.data?.detail || "업로드 중 오류가 발생했습니다.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-3xl mx-auto px-4 py-20">
            {/* 헤더 */}
            <div className="text-center mb-12">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-xs font-medium mb-4">
                    <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
                    AI 매출 분석 플랫폼
                </div>
                <h1 className="text-4xl font-bold text-white mb-3 leading-tight">
                    데이터를 올리면<br />
                    <span className="bg-gradient-to-r from-violet-400 to-indigo-400 bg-clip-text text-transparent">
                        인사이트가 됩니다
                    </span>
                </h1>
                <p className="text-gray-400 text-base">
                    CSV 매출 파일을 업로드하면 AI가 자동으로 분석하고 인사이트를 제공합니다.
                </p>
            </div>

            {/* 업로드 영역 */}
            <div
                className={`drop-zone border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${dragging
                        ? "drag-over border-violet-500/80 bg-violet-500/6"
                        : "border-gray-700 hover:border-violet-500/50 hover:bg-gray-900/50"
                    }`}
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    className="hidden"
                    onChange={handleChange}
                    id="csv-file-input"
                />

                {file ? (
                    <div className="flex flex-col items-center gap-3">
                        <div className="w-14 h-14 rounded-xl bg-violet-500/20 flex items-center justify-center">
                            <svg className="w-7 h-7 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                        </div>
                        <div>
                            <p className="text-white font-medium">{file.name}</p>
                            <p className="text-gray-500 text-sm">{(file.size / 1024).toFixed(1)} KB</p>
                        </div>
                        <button
                            onClick={(e) => { e.stopPropagation(); setFile(null); }}
                            className="text-xs text-gray-500 hover:text-gray-300 underline"
                        >
                            파일 변경
                        </button>
                    </div>
                ) : (
                    <div className="flex flex-col items-center gap-4">
                        <div className="w-16 h-16 rounded-2xl bg-gray-800 flex items-center justify-center">
                            <svg className="w-8 h-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                            </svg>
                        </div>
                        <div>
                            <p className="text-white font-medium text-base">CSV 파일을 드래그하거나 클릭하여 업로드</p>
                            <p className="text-gray-500 text-sm mt-1">Transaction_ID, Date, Time, Category, Product_Name ... 컬럼 포함 필요</p>
                        </div>
                    </div>
                )}
            </div>

            {/* 에러 메시지 */}
            {error && (
                <div className="mt-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                    {error}
                </div>
            )}

            {/* 업로드 버튼 */}
            <button
                id="upload-button"
                onClick={handleUpload}
                disabled={!file || loading}
                className="mt-6 w-full py-4 rounded-xl font-semibold text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 glow-violet"
            >
                {loading ? (
                    <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        분석 중...
                    </span>
                ) : (
                    "분석 시작"
                )}
            </button>

            {/* 지원 컬럼 안내 */}
            <div className="mt-10 p-5 rounded-2xl bg-gray-900/50 border border-gray-800">
                <p className="text-xs text-gray-500 font-medium mb-3 uppercase tracking-wider">지원 데이터 컬럼</p>
                <div className="flex flex-wrap gap-2">
                    {["Transaction_ID", "Date", "Time", "Category", "Product_Name", "Price", "Quantity", "Payment_Method", "Store_Location", "Total_Amount", "Age_Group"].map(col => (
                        <span key={col} className="px-2 py-1 rounded-md bg-gray-800 text-gray-400 text-xs font-mono">
                            {col}
                        </span>
                    ))}
                </div>
            </div>
        </div>
    );
}
