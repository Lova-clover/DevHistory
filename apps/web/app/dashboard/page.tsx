"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Activity, GitCommit, BookOpen, TrendingUp, Award, Code2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Loading } from "@/components/ui/loading";
import { Badge } from "@/components/ui/badge";
import { CommitChart } from "@/components/charts/commit-chart";
import { LanguageChart } from "@/components/charts/language-chart";
import { ActivityHeatmap } from "@/components/charts/activity-heatmap";
import { fetchWithAuth } from "@/lib/api";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: "easeOut",
    },
  },
};

export default function DashboardPage() {
  const [summary, setSummary] = useState<any>(null);
  const [weeklyTrend, setWeeklyTrend] = useState<any>(null);
  const [commitData, setCommitData] = useState<any[]>([]);
  const [languageData, setLanguageData] = useState<any[]>([]);
  const [heatmapData, setHeatmapData] = useState<any[]>([]);
  const [recentActivity, setRecentActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      // Fetch all data in parallel - use 'year' for totals, 'week' for trends
      const [summaryRes, trendRes, commitRes, languageRes, heatmapRes, activityRes] = await Promise.all([
        fetchWithAuth("/api/dashboard/summary?range=year"),
        fetchWithAuth("/api/dashboard/summary?range=week"),
        fetchWithAuth("/api/charts/commit-activity?days=30"),
        fetchWithAuth("/api/charts/language-distribution"),
        fetchWithAuth("/api/charts/activity-heatmap?days=365"),
        fetchWithAuth("/api/dashboard/recent-activity?limit=5"),
      ]);

      const [summaryData, trendData, commitData, languageData, heatmapData, activityData] = await Promise.all([
        summaryRes.json(),
        trendRes.json(),
        commitRes.json(),
        languageRes.json(),
        heatmapRes.json(),
        activityRes.json(),
      ]);

      setSummary(summaryData);
      setWeeklyTrend(trendData);
      setCommitData(commitData.data || []);
      setLanguageData(languageData.data || []);
      setHeatmapData(heatmapData.data || []);
      setRecentActivity(Array.isArray(activityData) ? activityData : []);
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loading size="lg" />
      </div>
    );
  }

  const stats = {
    totalCommits: summary?.total_commits || 0,
    totalRepos: summary?.repo_count || 0,
    blogPosts: summary?.blog_count || 0,
    currentStreak: summary?.current_streak || 0,
    longestStreak: summary?.longest_streak || 0,
  };

  const statCards = [
    {
      title: "총 커밋",
      value: stats.totalCommits.toLocaleString(),
      icon: GitCommit,
      color: "text-blue-600 dark:text-blue-400",
      bgColor: "bg-blue-50 dark:bg-blue-900/20",
      trend: weeklyTrend?.commit_diff !== undefined ? `${weeklyTrend.commit_diff > 0 ? '+' : ''}${weeklyTrend.commit_diff}` : "0",
    },
    {
      title: "활성 레포지토리",
      value: stats.totalRepos.toLocaleString(),
      icon: Code2,
      color: "text-purple-600 dark:text-purple-400",
      bgColor: "bg-purple-50 dark:bg-purple-900/20",
      trend: weeklyTrend?.repo_diff ? `${weeklyTrend.repo_diff > 0 ? '+' : ''}${weeklyTrend.repo_diff}` : "0",
    },
    {
      title: "블로그 포스트",
      value: stats.blogPosts.toLocaleString(),
      icon: BookOpen,
      color: "text-orange-600 dark:text-orange-400",
      bgColor: "bg-orange-50 dark:bg-orange-900/20",
      trend: weeklyTrend?.blog_diff ? `${weeklyTrend.blog_diff > 0 ? '+' : ''}${weeklyTrend.blog_diff}` : "0",
    },
  ];

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
              대시보드
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              당신의 개발 활동을 한눈에 확인하세요
            </p>
          </div>
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Badge variant="success" size="lg">
              <Activity className="w-4 h-4 mr-2" />
              활성 중
            </Badge>
          </motion.div>
        </motion.div>

        {/* Stats Grid */}
        <motion.div
          variants={itemVariants}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {statCards.map((stat) => (
            <motion.div
              key={stat.title}
              whileHover={{ scale: 1.02, y: -4 }}
              transition={{ duration: 0.2 }}
            >
              <Card className="p-6 hover:shadow-xl transition-shadow duration-300">
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 rounded-xl ${stat.bgColor}`}>
                    <stat.icon className={`w-6 h-6 ${stat.color}`} />
                  </div>
                  <Badge variant="info" size="sm">
                    {stat.trend}
                  </Badge>
                </div>
                <h3 className="text-gray-600 dark:text-gray-400 text-sm font-medium mb-1">
                  {stat.title}
                </h3>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {stat.value}
                </p>
              </Card>
            </motion.div>
          ))}
        </motion.div>

        {/* Streak Cards */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="p-6 bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 border-orange-200 dark:border-orange-800">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                현재 연속 기록
              </h3>
              <TrendingUp className="w-6 h-6 text-orange-600 dark:text-orange-400" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-5xl font-bold text-orange-600 dark:text-orange-400">
                {stats.currentStreak}
              </span>
              <span className="text-xl text-gray-600 dark:text-gray-400">일</span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              계속 좋은 습관을 유지하세요! 🔥
            </p>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 border-purple-200 dark:border-purple-800">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                최장 연속 기록
              </h3>
              <Award className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-5xl font-bold text-purple-600 dark:text-purple-400">
                {stats.longestStreak}
              </span>
              <span className="text-xl text-gray-600 dark:text-gray-400">일</span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              이 기록을 깨보세요! 🏆
            </p>
          </Card>
        </motion.div>

        {/* Commit Chart */}
        <motion.div variants={itemVariants}>
          <CommitChart data={commitData} />
        </motion.div>

        {/* Charts Row */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <LanguageChart data={languageData} />

          <Card className="p-6">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
              최근 활동
            </h3>
            <div className="space-y-4">
              {recentActivity.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                  최근 활동이 없습니다
                </p>
              ) : (
                recentActivity.map((activity, index) => {
                  const timeAgo = new Date(activity.timestamp).toLocaleString('ko-KR', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  });
                  
                  return (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    >
                      <div
                        className={`w-2 h-2 rounded-full ${
                          activity.color === "blue"
                            ? "bg-blue-500"
                            : activity.color === "green"
                            ? "bg-green-500"
                            : activity.color === "purple"
                            ? "bg-purple-500"
                            : "bg-orange-500"
                        }`}
                      ></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {activity.title}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {timeAgo}
                        </p>
                      </div>
                    </motion.div>
                  );
                })
              )}
            </div>
          </Card>
        </motion.div>

        {/* Activity Heatmap */}
        <motion.div variants={itemVariants}>
          <ActivityHeatmap data={heatmapData} />
        </motion.div>
      </motion.div>
    </div>
  );
}
