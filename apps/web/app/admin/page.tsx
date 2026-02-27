"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { BarChart3, Users, Eye, Activity, TrendingUp } from "lucide-react";
import { Card } from "@/components/ui/card";
import { fetchWithAuth } from "@/lib/api";

interface Overview {
  total_users: number;
  dau: number;
  mau: number;
  events_7d: number;
  pv_today: number;
  uv_today: number;
}

interface TimeseriesPoint {
  date: string;
  pv: number;
  uv: number;
}

interface TopPage {
  path: string;
  views: number;
}

export default function AdminPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [timeseries, setTimeseries] = useState<TimeseriesPoint[]>([]);
  const [topPages, setTopPages] = useState<TopPage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [overviewRes, tsRes, pagesRes] = await Promise.all([
        fetchWithAuth("/api/analytics/admin/overview"),
        fetchWithAuth("/api/analytics/admin/timeseries?days=30"),
        fetchWithAuth("/api/analytics/admin/top-pages?days=7"),
      ]);

      if (!overviewRes.ok) throw new Error("Admin access required");

      setOverview(await overviewRes.json());
      setTimeseries(await tsRes.json());
      setTopPages(await pagesRes.json());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="p-8 text-center">
          <h2 className="text-xl font-semibold mb-2 dark:text-white">접근 불가</h2>
          <p className="text-gray-500 dark:text-gray-400">{error}</p>
        </Card>
      </div>
    );
  }

  const maxPv = Math.max(...timeseries.map((t) => t.pv), 1);

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold dark:text-white mb-2">관리자 대시보드</h1>
        <p className="text-gray-500 dark:text-gray-400">서비스 분석 개요</p>
      </motion.div>

      {/* KPI Cards */}
      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[
            { label: "총 사용자", value: overview.total_users, icon: Users, color: "text-blue-500" },
            { label: "DAU", value: overview.dau, icon: Activity, color: "text-green-500" },
            { label: "MAU", value: overview.mau, icon: TrendingUp, color: "text-purple-500" },
            { label: "이벤트 (7일)", value: overview.events_7d, icon: BarChart3, color: "text-indigo-500" },
            { label: "PV (오늘)", value: overview.pv_today, icon: Eye, color: "text-amber-500" },
            { label: "UV (오늘)", value: overview.uv_today, icon: Users, color: "text-rose-500" },
          ].map((kpi) => (
            <motion.div
              key={kpi.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
            >
              <Card className="p-4">
                <kpi.icon className={`w-5 h-5 ${kpi.color} mb-2`} />
                <div className="text-2xl font-bold dark:text-white">{kpi.value.toLocaleString()}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">{kpi.label}</div>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* Simple bar chart for timeseries */}
      {timeseries.length > 0 && (
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4 dark:text-white">일일 PV / UV (최근 30일)</h2>
          <div className="flex items-end gap-1 h-40 overflow-x-auto">
            {timeseries.map((t) => (
              <div key={t.date} className="flex flex-col items-center gap-1 min-w-[20px]" title={`${t.date}\nPV: ${t.pv}  UV: ${t.uv}`}>
                <div className="flex items-end gap-0.5 h-32">
                  <div
                    className="w-2 bg-blue-400 rounded-t"
                    style={{ height: `${(t.pv / maxPv) * 100}%`, minHeight: t.pv > 0 ? 4 : 0 }}
                  />
                  <div
                    className="w-2 bg-green-400 rounded-t"
                    style={{ height: `${(t.uv / maxPv) * 100}%`, minHeight: t.uv > 0 ? 4 : 0 }}
                  />
                </div>
                <span className="text-[8px] text-gray-400 rotate-45 origin-left whitespace-nowrap">
                  {t.date.slice(5)}
                </span>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-4 mt-4 text-xs text-gray-500">
            <span className="flex items-center gap-1"><span className="w-2 h-2 bg-blue-400 rounded" /> PV</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 bg-green-400 rounded" /> UV</span>
          </div>
        </Card>
      )}

      {/* Top Pages */}
      {topPages.length > 0 && (
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4 dark:text-white">인기 페이지 (최근 7일)</h2>
          <div className="space-y-2">
            {topPages.map((page, i) => (
              <div key={page.path} className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-400 w-6 text-right">{i + 1}</span>
                  <span className="text-sm dark:text-gray-200 font-mono">{page.path}</span>
                </div>
                <span className="text-sm font-medium dark:text-white">{page.views.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
