"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Calendar, Plus, TrendingUp, ChevronLeft, ChevronRight, FileText } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { Tabs } from "@/components/ui/tabs";
import { EmptyState } from "@/components/ui/empty-state";
import { format, startOfWeek, addDays, subWeeks, addWeeks } from "date-fns";
import { ko } from "date-fns/locale";

interface WeeklyReport {
  id: string;
  week: string;
  title: string;
  commits: number;
  problems: number;
  notes: number;
  status: "draft" | "published";
}

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
  hidden: { opacity: 0, scale: 0.9 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: 0.3,
    },
  },
};

export default function WeeklyPage() {
  const [weeklies, setWeeklies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedReport, setSelectedReport] = useState<WeeklyReport | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("calendar");

  useEffect(() => {
    fetchWeeklies();
  }, []);

  const fetchWeeklies = async () => {
    try {
      const res = await fetch("/api/weekly");
      const data = await res.json();
      setWeeklies(data);
    } catch (error) {
      console.error("Failed to fetch weeklies:", error);
    } finally {
      setLoading(false);
    }
  };

  const getWeekDays = () => {
    const start = startOfWeek(currentDate, { locale: ko });
    return Array.from({ length: 7 }, (_, i) => addDays(start, i));
  };

  const handlePreviousWeek = () => {
    setCurrentDate(subWeeks(currentDate, 1));
  };

  const handleNextWeek = () => {
    setCurrentDate(addWeeks(currentDate, 1));
  };

  const handleCreateReport = () => {
    setIsModalOpen(true);
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-16">로딩 중...</div>;
  }

  const weekDays = getWeekDays();

  const tabs = [
    { id: "calendar", label: "캘린더 뷰", icon: Calendar },
    { id: "list", label: "리스트 뷰", icon: FileText },
  ];

  // Transform API data to match WeeklyReport interface
  const weeklyReports: WeeklyReport[] = weeklies.map((w) => ({
    id: w.id,
    week: w.week_start || w.created_at,
    title: w.title || `주간 리포트 ${w.id}`,
    commits: w.commit_count || 0,
    problems: w.problem_count || 0,
    notes: w.note_count || 0,
    status: w.status || "published",
  }));

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.div
        initial="hidden"
        animate="visible"
        variants={containerVariants}
        className="space-y-8"
      >
        {/* Header */}
        <motion.div variants={itemVariants} className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
              주간 리포트
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              매주 자동으로 생성되는 개발 활동 요약
            </p>
          </div>
          <Button onClick={handleCreateReport} size="lg">
            <Plus className="w-5 h-5 mr-2" />
            리포트 생성
          </Button>
        </motion.div>

        {weeklyReports.length === 0 ? (
          <EmptyState
            title="주간 리포트가 없습니다"
            description="첫 번째 주간 리포트를 생성해보세요"
            actionLabel="리포트 생성"
            onAction={handleCreateReport}
          />
        ) : (
          <>
            {/* Stats Overview */}
            <motion.div
              variants={itemVariants}
              className="grid grid-cols-1 md:grid-cols-3 gap-6"
            >
              <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200 dark:border-blue-800">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    총 리포트 수
                  </h3>
                  <TrendingUp className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                  {weeklyReports.length}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                  작성 완료된 리포트
                </p>
              </Card>

              <Card className="p-6 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-green-200 dark:border-green-800">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    이번 주 활동
                  </h3>
                  <Calendar className="w-5 h-5 text-green-600 dark:text-green-400" />
                </div>
                <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                  {weeklyReports[0]
                    ? weeklyReports[0].commits +
                      weeklyReports[0].problems +
                      weeklyReports[0].notes
                    : 0}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                  커밋, 문제, 노트 합계
                </p>
              </Card>

              <Card className="p-6 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border-purple-200 dark:border-purple-800">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    주간 평균
                  </h3>
                  <TrendingUp className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                </div>
                <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                  {Math.round(
                    weeklyReports.reduce(
                      (acc, r) => acc + r.commits + r.problems + r.notes,
                      0
                    ) / weeklyReports.length
                  )}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                  평균 활동량
                </p>
              </Card>
            </motion.div>

            {/* Tabs */}
            <motion.div variants={itemVariants}>
              <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
            </motion.div>

            {/* Calendar View */}
            {activeTab === "calendar" && (
              <motion.div variants={itemVariants}>
                <Card className="p-6">
                  {/* Week Navigation */}
                  <div className="flex items-center justify-between mb-6">
                    <Button variant="ghost" onClick={handlePreviousWeek}>
                      <ChevronLeft className="w-5 h-5 mr-2" />
                      이전 주
                    </Button>
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                      {format(weekDays[0], "yyyy년 M월 d일", { locale: ko })} -{" "}
                      {format(weekDays[6], "M월 d일", { locale: ko })}
                    </h2>
                    <Button variant="ghost" onClick={handleNextWeek}>
                      다음 주
                      <ChevronRight className="w-5 h-5 ml-2" />
                    </Button>
                  </div>

                  {/* Week Calendar */}
                  <div className="grid grid-cols-7 gap-4">
                    {weekDays.map((day, index) => {
                      const isToday =
                        format(day, "yyyy-MM-dd") === format(new Date(), "yyyy-MM-dd");
                      const hasActivity = Math.random() > 0.3; // Mock data

                      return (
                        <motion.div
                          key={index}
                          whileHover={{ scale: 1.05 }}
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
                                isToday
                                  ? "text-primary-600 dark:text-primary-400"
                                  : "text-gray-900 dark:text-white"
                              }`}
                            >
                              {format(day, "d")}
                            </p>
                            {hasActivity && (
                              <div className="space-y-2">
                                <div className="text-xs">
                                  <Badge variant="info" size="sm">
                                    5 커밋
                                  </Badge>
                                </div>
                                <div className="text-xs">
                                  <Badge variant="success" size="sm">
                                    2 문제
                                  </Badge>
                                </div>
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

            {/* List View */}
            {activeTab === "list" && (
              <motion.div variants={containerVariants} className="space-y-4">
                {weeklyReports.map((report) => (
                  <motion.div
                    key={report.id}
                    variants={itemVariants}
                    whileHover={{ scale: 1.01, y: -2 }}
                  >
                    <a href={`/weekly/${report.id}`}>
                      <Card className="p-6 hover:shadow-lg transition-all duration-300 cursor-pointer">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                                {report.title}
                              </h3>
                              <Badge
                                variant={
                                  report.status === "published" ? "success" : "default"
                                }
                              >
                                {report.status === "published" ? "발행됨" : "초안"}
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                              {format(new Date(report.week), "yyyy년 M월 d일 주", {
                                locale: ko,
                              })}
                            </p>
                            <div className="flex items-center gap-6">
                              <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                                <span className="text-sm text-gray-700 dark:text-gray-300">
                                  {report.commits} 커밋
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                                <span className="text-sm text-gray-700 dark:text-gray-300">
                                  {report.problems} 문제
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-purple-500"></div>
                                <span className="text-sm text-gray-700 dark:text-gray-300">
                                  {report.notes} 노트
                                </span>
                              </div>
                            </div>
                          </div>
                          <Button variant="ghost">상세보기</Button>
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

      {/* Create Report Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="새 주간 리포트 생성"
        size="lg"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              주차 선택
            </label>
            <input
              type="week"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              제목
            </label>
            <input
              type="text"
              placeholder="리포트 제목을 입력하세요"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              설명
            </label>
            <textarea
              rows={4}
              placeholder="이번 주의 주요 활동이나 목표를 작성하세요"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
            />
          </div>
          <div className="flex gap-3 pt-4">
            <Button variant="ghost" onClick={() => setIsModalOpen(false)}>
              취소
            </Button>
            <Button onClick={() => setIsModalOpen(false)}>생성하기</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
              className="block bg-white p-6 rounded-lg shadow hover:shadow-lg transition"
            >
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-xl font-bold mb-2">
                    {weekly.week_start} ~ {weekly.week_end}
                  </h3>
                  <div className="flex gap-6 text-sm text-gray-600">
                    <span>커밋 {weekly.commit_count}개</span>
                    <span>문제 {weekly.problem_count}개</span>
                    <span>노트 {weekly.note_count}개</span>
                  </div>
                </div>
                <div>
                  {weekly.has_llm_summary ? (
                    <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                      리포트 있음
                    </span>
                  ) : (
                    <span className="bg-gray-100 text-gray-600 px-3 py-1 rounded-full text-sm">
                      리포트 없음
                    </span>
                  )}
                </div>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
