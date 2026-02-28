import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "@/components/ui/toast";
import { ThemeProvider } from "@/components/theme-provider";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { AnalyticsTracker } from "@/components/analytics-tracker";
import { NavBar } from "@/components/nav-bar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "DevHistory - 개발 활동 자동 머지 플랫폼",
  description: "GitHub, solved.ac, 노트를 자동 수집해서 포트폴리오로 만들어주는 서비스",
  metadataBase: new URL("https://devhistory.com"),
  icons: {
    icon: "/devhistory_logo.png",
    apple: "/devhistory_logo.png",
  },
  openGraph: {
    title: "DevHistory - 개발 활동 자동 머지 플랫폼",
    description: "GitHub, solved.ac, 노트를 자동 수집해서 포트폴리오로 만들어주는 서비스",
    url: "https://devhistory.com",
    siteName: "DevHistory",
    images: [{ url: "/devhistory_logo.png", width: 512, height: 512 }],
    locale: "ko_KR",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "DevHistory",
    description: "GitHub, solved.ac, 노트를 자동 수집해서 포트폴리오로 만들어주는 서비스",
    images: ["/devhistory_logo.png"],
  },
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
            <NavBar />
            <main className="min-h-screen bg-gray-50 dark:bg-gray-900">{children}</main>
            <AnalyticsTracker />
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
