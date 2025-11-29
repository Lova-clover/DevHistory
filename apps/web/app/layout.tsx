import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "@/components/ui/toast";
import { ThemeProvider } from "@/components/theme-provider";
import { ThemeToggle } from "@/components/ui/theme-toggle";

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
    <html lang="ko" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <ToastProvider>
            <nav className="sticky top-0 z-40 border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-md shadow-sm">
              <div className="container mx-auto px-4 py-3 flex items-center justify-between">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-primary-400 bg-clip-text text-transparent">
                  DevHistory
                </h1>
                <div className="flex items-center gap-6">
                  <a href="/dashboard" className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors font-medium">
                    대시보드
                  </a>
                  <a href="/weekly" className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors font-medium">
                    주간 리포트
                  </a>
                  <a href="/repos" className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors font-medium">
                    레포지토리
                  </a>
                  <a href="/portfolio" className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors font-medium">
                    포트폴리오
                  </a>
                  <ThemeToggle />
                </div>
              </div>
            </nav>
            <main className="min-h-screen bg-gray-50 dark:bg-gray-900">{children}</main>
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
