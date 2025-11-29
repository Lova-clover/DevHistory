import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "DevHistory - 개발 활동 자동 머지 플랫폼",
  description: "GitHub, solved.ac, 노트를 자동 수집해서 포트폴리오로 만들어주는 서비스",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className={inter.className}>
        <nav className="border-b bg-white">
          <div className="container mx-auto px-4 py-3 flex items-center justify-between">
            <h1 className="text-2xl font-bold text-primary-600">DevHistory</h1>
            <div className="flex gap-4">
              <a href="/dashboard" className="hover:text-primary-600">대시보드</a>
              <a href="/weekly" className="hover:text-primary-600">주간 리포트</a>
              <a href="/repos" className="hover:text-primary-600">레포지토리</a>
              <a href="/portfolio" className="hover:text-primary-600">포트폴리오</a>
            </div>
          </div>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}
