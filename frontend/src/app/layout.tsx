import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "DataIQ - 매출 데이터 분석 플랫폼",
    description: "CSV 매출 데이터를 업로드하고 AI 기반 인사이트를 받아보세요.",
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="ko">
            <body className={inter.className}>
                <div className="min-h-screen bg-gray-950 text-gray-100">
                    {/* 네비게이션 */}
                    <nav className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
                        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                            <div className="flex items-center justify-between h-16">
                                <Link href="/" className="flex items-center gap-2">
                                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center">
                                        <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                        </svg>
                                    </div>
                                    <span className="font-bold text-lg text-white">DataIQ</span>
                                </Link>
                                <div className="flex items-center gap-6">
                                    <Link href="/" className="text-sm text-gray-400 hover:text-white transition-colors">
                                        업로드
                                    </Link>
                                    <Link href="/history" className="text-sm text-gray-400 hover:text-white transition-colors">
                                        분석 기록
                                    </Link>
                                </div>
                            </div>
                        </div>
                    </nav>
                    <main>{children}</main>
                </div>
            </body>
        </html>
    );
}
