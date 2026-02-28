"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import Image from "next/image";
import { Menu, X, LogIn, LogOut } from "lucide-react";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { logout } from "@/lib/api";

const navLinks = [
  { href: "/dashboard", label: "대시보드" },
  { href: "/repos", label: "레포지토리" },
  { href: "/contents", label: "콘텐츠" },
  { href: "/coach", label: "코칭" },
  { href: "/resume", label: "이력서" },
  { href: "/writing-style", label: "글쓰기" },
  { href: "/portfolio", label: "포트폴리오" },
  { href: "/settings", label: "설정" },
];

export function NavBar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const pathname = usePathname();
  const canUseNav = authChecked && isLoggedIn;

  useEffect(() => {
    let cancelled = false;

    const checkAuth = async () => {
      try {
        const res = await fetch("/api/auth/me", { credentials: "include" });
        if (!cancelled) {
          setIsLoggedIn(res.ok);
        }
      } catch {
        if (!cancelled) {
          setIsLoggedIn(false);
        }
      } finally {
        if (!cancelled) {
          setAuthChecked(true);
        }
      }
    };

    checkAuth();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleLogout = async () => {
    if (loggingOut) return;
    setMobileOpen(false);
    setLoggingOut(true);
    try {
      await logout();
    } catch (error) {
      console.error("Failed to logout:", error);
      setLoggingOut(false);
    }
  };

  return (
    <nav className="sticky top-0 z-40 border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md shadow-sm">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <a href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <Image
            src="/devhistory_logo.png"
            alt="DevHistory"
            width={32}
            height={32}
            className="rounded-lg"
          />
          <span className="text-xl font-bold bg-gradient-to-r from-primary-600 to-primary-400 bg-clip-text text-transparent">
            DevHistory
          </span>
        </a>

        <div className="hidden lg:flex items-center gap-5">
          {navLinks.map((link) => {
            const isActive = pathname === link.href || pathname.startsWith(link.href + "/");

            if (!canUseNav) {
              return (
                <button
                  key={link.href}
                  type="button"
                  disabled
                  title="로그인 후 이용 가능"
                  className="text-sm font-medium text-gray-400 dark:text-gray-600 cursor-not-allowed"
                >
                  {link.label}
                </button>
              );
            }

            return (
              <a
                key={link.href}
                href={link.href}
                className={`text-sm font-medium transition-colors ${
                  isActive
                    ? "text-primary-600 dark:text-primary-400"
                    : "text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                }`}
              >
                {link.label}
              </a>
            );
          })}

          {canUseNav && <ThemeToggle />}

          {authChecked &&
            (isLoggedIn ? (
              <button
                onClick={handleLogout}
                disabled={loggingOut}
                className="inline-flex items-center gap-1 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <LogOut className="w-4 h-4" />
                {loggingOut ? "Logging out..." : "Logout"}
              </button>
            ) : (
              <a
                href="/api/auth/github/login"
                className="inline-flex items-center gap-1 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
              >
                <LogIn className="w-4 h-4" />
                Login
              </a>
            ))}
        </div>

        <div className="flex items-center gap-3 lg:hidden">
          {canUseNav ? (
            <>
              <ThemeToggle />
              <button
                onClick={() => setMobileOpen(!mobileOpen)}
                className="p-2 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
                aria-label="메뉴 열기"
              >
                {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </>
          ) : (
            authChecked && (
              <a
                href="/api/auth/github/login"
                className="inline-flex items-center gap-1 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
              >
                <LogIn className="w-4 h-4" />
                Login
              </a>
            )
          )}
        </div>
      </div>

      {mobileOpen && canUseNav && (
        <div className="lg:hidden border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
          <div className="container mx-auto px-4 py-3 flex flex-col gap-1">
            {navLinks.map((link) => {
              const isActive = pathname === link.href || pathname.startsWith(link.href + "/");
              return (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className={`px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400"
                      : "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800"
                  }`}
                >
                  {link.label}
                </a>
              );
            })}
            <button
              onClick={handleLogout}
              disabled={loggingOut}
              className="px-3 py-2.5 rounded-lg text-left text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loggingOut ? "Logging out..." : "Logout"}
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
