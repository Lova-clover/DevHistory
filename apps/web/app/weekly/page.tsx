"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Calendar, ChevronLeft, ChevronRight, FileText, Plus, TrendingUp } from "lucide-react";
import { addDays, addWeeks, format, startOfWeek, subWeeks } from "date-fns";
import { ko } from "date-fns/locale";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Tabs } from "@/components/ui/tabs";
import { fetchWithAuth } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";

type DaySummary = {
  commits?: number;
  problems?: number;
  notes?: number;
};

type WeeklyItem = {
  id: string;
  week_start: string;
  week_end: string;
  commit_count: number;
  problem_count: number;
  note_count: number;
  summary_json?: {
    by_day?: Record<string, DaySummary>;
  };
  llm_summary?: string | null;
  status?: string;
  title?: string;
};

type WeeklyListResponse = {
  summaries: WeeklyItem[];
  total: number;
  page: number;
  page_size: number;
};

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: 0.2,
    },
  },
};

export default function WeeklyPage() {
  const [weeklies, setWeeklies] = useState<WeeklyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [activeTab, setActiveTab] = useState("calendar");

  useEffect(() => {
    fetchWeeklies();
  }, []);

  const fetchWeeklies = async () => {
    try {
      const res = await fetchWithAuth("/api/weekly");
      const data = await res.json();
      const summaries = Array.isArray(data)
        ? data
        : Array.isArray((data as WeeklyListResponse)?.summaries)
          ? (data as WeeklyListResponse).summaries
          : [];
      setWeeklies(summaries);
    } catch (error) {
      console.error("Failed to fetch weeklies:", error);
      setWeeklies([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateReport = async () => {
    setGenerating(true);
    try {
      const res = await fetchWithAuth("/api/weekly/generate", { method: "POST" });
      const data = await res.json();
      trackEvent({
        event_name: "generate_weekly_report",
        meta: { content_type: "weekly_report", source: "weekly_list" },
      });
      alert(data?.message || "주간 리포트 생성이 시작되었습니다.");
      setTimeout(fetchWeeklies, 2500);
    } catch (error) {
      console.error("Failed to generate weekly report:", error);
      alert("주간 리포트 생성에 실패했습니다.");
    } finally {
      setGenerating(false);
    }
  };

  const weekDays = useMemo(() => {
    const start = startOfWeek(currentDate, { locale: ko, weekStartsOn: 1 });
    return Array.from({ length: 7 }, (_, i) => addDays(start, i));
  }, [currentDate]);

  const weeklyReports = useMemo(
    () =>
      weeklies.map((weekly) => ({
        id: weekly.id,
        week: weekly.week_start,
        title: weekly.title || `주간 리포트 ${weekly.week_start}`,
        commits: weekly.commit_count ?? 0,
        problems: weekly.problem_count ?? 0,
        notes: weekly.note_count ?? 0,
        summary_json: weekly.summary_json || {},
        status:
          weekly.status === "published" ||
          weekly.status === "completed" ||
          Boolean(weekly.llm_summary)
            ? "published"
            : "draft",
      })),
    [weeklies]
  );

  if (loading) {
    return <div className="container mx-auto px-4 py-16">Loading...</div>;
  }

  const tabs = [
    { id: "calendar", label: "Calendar", icon: Calendar },
    { id: "list", label: "List", icon: FileText },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.div initial="hidden" animate="visible" variants={containerVariants} className="space-y-8">
        <motion.div variants={itemVariants} className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">Weekly Report</h1>
            <p className="text-gray-600 dark:text-gray-400">주간 활동 요약과 생성된 리포트를 확인할 수 있습니다.</p>
          </div>
          <Button onClick={handleCreateReport} size="lg" disabled={generating}>
            <Plus className="w-5 h-5 mr-2" />
            {generating ? "Generating..." : "Generate"}
          </Button>
        </motion.div>

        {weeklyReports.length === 0 ? (
          <EmptyState
            title="주간 리포트가 없습니다"
            description="첫 번째 주간 리포트를 생성해보세요."
            action={{ label: "Generate", onClick: handleCreateReport }}
          />
        ) : (
          <>
            <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200 dark:border-blue-800">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Reports</h3>
                  <TrendingUp className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">{weeklyReports.length}</p>
              </Card>

              <Card className="p-6 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-green-200 dark:border-green-800">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Latest Week Activity</h3>
                  <Calendar className="w-5 h-5 text-green-600 dark:text-green-400" />
                </div>
                <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                  {weeklyReports[0]
                    ? weeklyReports[0].commits + weeklyReports[0].problems + weeklyReports[0].notes
                    : 0}
                </p>
              </Card>

              <Card className="p-6 bg-gradient-to-br from-slate-50 to-zinc-100 dark:from-slate-900/20 dark:to-zinc-900/20 border-slate-200 dark:border-slate-800">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Weekly Average</h3>
                  <TrendingUp className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                </div>
                <p className="text-3xl font-bold text-slate-700 dark:text-slate-300">
                  {Math.round(
                    weeklyReports.reduce(
                      (acc, report) => acc + report.commits + report.problems + report.notes,
                      0
                    ) / weeklyReports.length
                  )}
                </p>
              </Card>
            </motion.div>

            <motion.div variants={itemVariants}>
              <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
            </motion.div>

            {activeTab === "calendar" && (
              <motion.div variants={itemVariants}>
                <Card className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <Button variant="ghost" onClick={() => setCurrentDate(subWeeks(currentDate, 1))}>
                      <ChevronLeft className="w-5 h-5 mr-2" />
                      Previous
                    </Button>
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                      {format(weekDays[0], "yyyy-MM-dd")} - {format(weekDays[6], "yyyy-MM-dd")}
                    </h2>
                    <Button variant="ghost" onClick={() => setCurrentDate(addWeeks(currentDate, 1))}>
                      Next
                      <ChevronRight className="w-5 h-5 ml-2" />
                    </Button>
                  </div>

                  <div className="grid grid-cols-7 gap-4">
                    {weekDays.map((day, index) => {
                      const dayStr = format(day, "yyyy-MM-dd");
                      const isToday = dayStr === format(new Date(), "yyyy-MM-dd");
                      const dayActivity = weeklyReports.reduce(
                        (acc, report) => {
                          const byDay = report.summary_json?.by_day?.[dayStr];
                          if (!byDay) return acc;
                          acc.commits += byDay.commits ?? 0;
                          acc.problems += byDay.problems ?? 0;
                          acc.notes += byDay.notes ?? 0;
                          return acc;
                        },
                        { commits: 0, problems: 0, notes: 0 }
                      );
                      const hasActivity =
                        dayActivity.commits > 0 || dayActivity.problems > 0 || dayActivity.notes > 0;

                      return (
                        <motion.div
                          key={index}
                          whileHover={{ scale: 1.03 }}
                          className={`p-4 rounded-lg border-2 transition-all ${
                            isToday
                              ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20"
                              : "border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-700"
                          }`}
                        >
                          <div className="text-center">
                            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                              {format(day, "EEE", { locale: ko })}
                            </p>
                            <p
                              className={`text-2xl font-bold mb-3 ${
                                isToday ? "text-primary-600 dark:text-primary-400" : "text-gray-900 dark:text-white"
                              }`}
                            >
                              {format(day, "d")}
                            </p>
                            {hasActivity && (
                              <div className="space-y-2">
                                {dayActivity.commits > 0 && (
                                  <div className="text-xs">
                                    <Badge variant="info" size="sm">
                                      {dayActivity.commits} commits
                                    </Badge>
                                  </div>
                                )}
                                {dayActivity.problems > 0 && (
                                  <div className="text-xs">
                                    <Badge variant="success" size="sm">
                                      {dayActivity.problems} problems
                                    </Badge>
                                  </div>
                                )}
                                {dayActivity.notes > 0 && (
                                  <div className="text-xs">
                                    <Badge variant="default" size="sm">
                                      {dayActivity.notes} notes
                                    </Badge>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </Card>
              </motion.div>
            )}

            {activeTab === "list" && (
              <motion.div variants={containerVariants} className="space-y-4">
                {weeklyReports.map((report) => (
                  <motion.div key={report.id} variants={itemVariants} whileHover={{ scale: 1.01, y: -2 }}>
                    <a href={`/weekly/${report.id}`}>
                      <Card className="p-6 hover:shadow-lg transition-all duration-300 cursor-pointer">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">{report.title}</h3>
                              <Badge variant={report.status === "published" ? "success" : "default"}>
                                {report.status === "published" ? "Published" : "Draft"}
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                              {format(new Date(report.week), "yyyy-MM-dd")}
                            </p>
                            <div className="flex items-center gap-6">
                              <span className="text-sm text-gray-700 dark:text-gray-300">{report.commits} commits</span>
                              <span className="text-sm text-gray-700 dark:text-gray-300">{report.problems} problems</span>
                              <span className="text-sm text-gray-700 dark:text-gray-300">{report.notes} notes</span>
                            </div>
                          </div>
                          <Button variant="ghost">View</Button>
                        </div>
                      </Card>
                    </a>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </>
        )}
      </motion.div>
    </div>
  );
}
