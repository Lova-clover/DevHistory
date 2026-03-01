"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Brain,
  Target,
  Zap,
  Trophy,
  BookOpen,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  History,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { fetchWithAuth } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";

interface ProblemStats {
  total: number;
  by_level: Record<string, number>;
  by_tag: Record<string, number>;
  weak_tags: string[];
  recent: Array<{
    problem_id: number;
    title: string;
    level: number;
    tags: string[];
    solved_at: string | null;
  }>;
}

interface CoachHistoryItem {
  id: string;
  type: string;
  title: string;
  content: string;
  created_at: string;
}

const levelLabels: Record<number, string> = {
  0: "Unrated",
  1: "Bronze V", 2: "Bronze IV", 3: "Bronze III", 4: "Bronze II", 5: "Bronze I",
  6: "Silver V", 7: "Silver IV", 8: "Silver III", 9: "Silver II", 10: "Silver I",
  11: "Gold V", 12: "Gold IV", 13: "Gold III", 14: "Gold II", 15: "Gold I",
  16: "Platinum V", 17: "Platinum IV", 18: "Platinum III", 19: "Platinum II", 20: "Platinum I",
  21: "Diamond V", 22: "Diamond IV", 23: "Diamond III", 24: "Diamond II", 25: "Diamond I",
  26: "Ruby V", 27: "Ruby IV", 28: "Ruby III", 29: "Ruby II", 30: "Ruby I",
};

const getLevelColor = (level: number) => {
  if (level <= 5) return "text-amber-700 bg-amber-100 dark:bg-amber-900/30 dark:text-amber-300";
  if (level <= 10) return "text-gray-600 bg-gray-200 dark:bg-gray-700 dark:text-gray-300";
  if (level <= 15) return "text-yellow-700 bg-yellow-100 dark:bg-yellow-900/30 dark:text-yellow-300";
  if (level <= 20) return "text-cyan-700 bg-cyan-100 dark:bg-cyan-900/30 dark:text-cyan-300";
  if (level <= 25) return "text-blue-700 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-300";
  return "text-red-700 bg-red-100 dark:bg-red-900/30 dark:text-red-300";
};

export default function CoachPage() {
  const [stats, setStats] = useState<ProblemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [generatingQuiz, setGeneratingQuiz] = useState(false);
  const [quiz, setQuiz] = useState<string | null>(null);
  const [quizTopic, setQuizTopic] = useState("");
  const [history, setHistory] = useState<CoachHistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [activeTab, setActiveTab] = useState<"analysis" | "quiz">("analysis");

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await fetchWithAuth("/api/coach/stats");
      const data = await res.json();
      setStats(data);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    } finally {
      setLoading(false);
    }
  };

  const runAnalysis = async () => {
    setAnalyzing(true);
    setAnalysis(null);
    try {
      const res = await fetchWithAuth("/api/coach/analyze", { method: "POST" });
      const data = await res.json();
      trackEvent({ event_name: "coach_analysis_triggered" });
      if (data.status === "success") {
        setAnalysis(data.analysis);
      } else {
        alert(data.message || data.error || "분석에 실패했습니다");
      }
    } catch {
      alert("분석 요청에 실패했습니다");
    } finally {
      setAnalyzing(false);
    }
  };

  const pollQuizTask = async (taskId: string) => {
    const maxAttempts = 40;
    const delayMs = 3000;

    for (let i = 0; i < maxAttempts; i += 1) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));

      const res = await fetchWithAuth(`/api/coach/quiz/task/${encodeURIComponent(taskId)}`);
      const data = await res.json();

      if (!res.ok) {
        alert(data.detail || data.message || data.error || "퀴즈 생성에 실패했습니다");
        return;
      }

      if (data.status === "success") {
        trackEvent({ event_name: "coach_quiz_generated", meta: { topic: quizTopic } });
        setQuiz(data.quiz);
        return;
      }

      if (data.status !== "processing") {
        alert(data.message || data.error || "퀴즈 생성에 실패했습니다");
        return;
      }
    }

    alert("퀴즈 생성이 지연되고 있습니다. 잠시 후 다시 시도해주세요.");
  };

  const generateQuiz = async () => {
    setGeneratingQuiz(true);
    setQuiz(null);
    try {
      const res = await fetchWithAuth("/api/coach/quiz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: quizTopic }),
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.detail || data.message || data.error || "퀴즈 생성에 실패했습니다");
        return;
      }

      if (data.status === "success") {
        trackEvent({ event_name: "coach_quiz_generated", meta: { topic: quizTopic } });
        setQuiz(data.quiz);
        return;
      }

      if (data.status === "processing" && data.task_id) {
        await pollQuizTask(data.task_id);
        return;
      }

      if (data.status === "processing") {
        alert(data.message || "퀴즈를 생성 중입니다. 잠시 후 다시 시도해주세요.");
        return;
      }

      alert(data.message || data.error || "퀴즈 생성에 실패했습니다");
    } catch {
      alert("퀴즈 생성에 실패했습니다");
    } finally {
      setGeneratingQuiz(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetchWithAuth("/api/coach/history");
      const data = await res.json();
      setHistory(data);
      setShowHistory(true);
    } catch {
      alert("히스토리를 불러오지 못했습니다");
    }
  };

  const renderMarkdown = (text: string) => {
    const codeBlocks: string[] = [];
    let html = text.replace(/```(\w+)?\n([\s\S]*?)```/g, (_, lang: string, code: string) => {
      const safeCode = code
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
      const block = `<pre class="mt-3 mb-3 overflow-x-auto rounded-lg bg-gray-900 text-gray-100 p-3 text-sm"><code data-lang="${lang || "text"}">${safeCode}</code></pre>`;
      const token = `@@CODE_BLOCK_${codeBlocks.length}@@`;
      codeBlocks.push(block);
      return token;
    });

    html = html
      .replace(/^### (.+)$/gm, '<h3 class="text-lg font-bold mt-4 mb-2">$1</h3>')
      .replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold mt-5 mb-2">$1</h2>')
      .replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold mt-6 mb-3">$1</h1>')
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(
        /`([^`]+)`/g,
        '<code class="bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded text-sm font-mono">$1</code>'
      )
      .replace(/^- (.+)$/gm, '<li class="ml-4 list-disc">$1</li>')
      .replace(/<details>/g, '<details class="mt-3 border border-gray-200 dark:border-gray-700 rounded-lg p-3">')
      .replace(/<summary>(.+?)<\/summary>/g, '<summary class="cursor-pointer font-medium text-primary-600 dark:text-primary-400">$1</summary>')
      .replace(/\n\n/g, "<br/><br/>")
      .replace(/\n/g, "<br/>");

    for (let i = 0; i < codeBlocks.length; i += 1) {
      html = html.replace(`@@CODE_BLOCK_${i}@@`, codeBlocks[i]);
    }

    return html;
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-16 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
              🎓 코딩 코치
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Solved.ac 데이터를 기반으로 맞춤형 코딩 코칭을 받아보세요
            </p>
          </div>
          <Button onClick={fetchHistory} variant="outline">
            <History className="w-4 h-4 mr-1.5" />
            히스토리
          </Button>
        </div>

        {/* Stats Overview */}
        {stats && stats.total > 0 ? (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400">
                    <Trophy className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">풀이 수</p>
                  </div>
                </div>
              </Card>
              <Card className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                    <Target className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {Object.keys(stats.by_tag).length}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">알고리즘 유형</p>
                  </div>
                </div>
              </Card>
              <Card className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400">
                    <Zap className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {stats.weak_tags.length}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">취약 유형</p>
                  </div>
                </div>
              </Card>
              <Card className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400">
                    <BookOpen className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {Object.keys(stats.by_level).length}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">난이도 범위</p>
                  </div>
                </div>
              </Card>
            </div>

            {/* Top Tags & Weak Tags */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="p-6">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">💪 자주 푸는 유형</h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(stats.by_tag)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 12)
                    .map(([tag, count]) => (
                      <span
                        key={tag}
                        className="px-3 py-1.5 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-sm font-medium"
                      >
                        {tag} ({count})
                      </span>
                    ))}
                </div>
              </Card>
              <Card className="p-6">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">🎯 보완이 필요한 유형</h3>
                {stats.weak_tags.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {stats.weak_tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-3 py-1.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-full text-sm font-medium"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 dark:text-gray-400">취약 유형 데이터가 부족합니다</p>
                )}
              </Card>
            </div>

            {/* Tabs: Analysis / Quiz */}
            <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
              <button
                onClick={() => setActiveTab("analysis")}
                className={`px-4 py-2.5 font-medium text-sm border-b-2 transition ${
                  activeTab === "analysis"
                    ? "border-primary-600 text-primary-600 dark:text-primary-400"
                    : "border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                }`}
              >
                <Brain className="w-4 h-4 inline mr-1.5" />
                AI 분석 & 조언
              </button>
              <button
                onClick={() => setActiveTab("quiz")}
                className={`px-4 py-2.5 font-medium text-sm border-b-2 transition ${
                  activeTab === "quiz"
                    ? "border-primary-600 text-primary-600 dark:text-primary-400"
                    : "border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                }`}
              >
                <Zap className="w-4 h-4 inline mr-1.5" />
                코딩 퀴즈
              </button>
            </div>

            {activeTab === "analysis" && (
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                    문제 풀이 패턴 분석
                  </h3>
                  <Button onClick={runAnalysis} disabled={analyzing} variant="primary">
                    <Brain className={`w-4 h-4 mr-1.5 ${analyzing ? "animate-pulse" : ""}`} />
                    {analyzing ? "분석 중..." : "AI 분석 시작"}
                  </Button>
                </div>
                {analysis ? (
                  <div
                    className="prose dark:prose-invert max-w-none text-gray-800 dark:text-gray-200 leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: renderMarkdown(analysis) }}
                  />
                ) : (
                  <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                    <Brain className="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
                    <p>AI 분석을 시작하면 맞춤형 코칭을 받을 수 있습니다</p>
                    <p className="text-sm mt-1">문제 풀이 패턴, 강점/약점, 학습 로드맵을 제공합니다</p>
                  </div>
                )}
              </Card>
            )}

            {activeTab === "quiz" && (
              <Card className="p-6">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white">알고리즘 퀴즈</h3>
                  <div className="flex gap-2 w-full sm:w-auto">
                    <input
                      type="text"
                      value={quizTopic}
                      onChange={(e) => setQuizTopic(e.target.value)}
                      placeholder="주제 (빈칸=약점 기반)"
                      className="flex-1 sm:w-48 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-primary-500"
                    />
                    <Button onClick={generateQuiz} disabled={generatingQuiz} variant="primary">
                      <Zap className={`w-4 h-4 mr-1.5 ${generatingQuiz ? "animate-pulse" : ""}`} />
                      {generatingQuiz ? "생성 중..." : "퀴즈 생성"}
                    </Button>
                  </div>
                </div>
                {quiz ? (
                  <div
                    className="prose dark:prose-invert max-w-none text-gray-800 dark:text-gray-200 leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: renderMarkdown(quiz) }}
                  />
                ) : (
                  <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                    <Zap className="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
                    <p>취약한 알고리즘 유형을 기반으로 퀴즈를 생성합니다</p>
                    <p className="text-sm mt-1">특정 주제를 입력하거나, 빈칸으로 두면 자동으로 약점 유형이 선택됩니다</p>
                  </div>
                )}
              </Card>
            )}
          </>
        ) : (
          <Card className="p-12 text-center">
            <div className="max-w-md mx-auto">
              <Trophy className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Solved.ac 데이터가 없습니다
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-6">
                설정에서 백준 아이디를 등록하고 동기화를 실행해주세요
              </p>
              <a href="/settings">
                <Button variant="primary">설정으로 이동</Button>
              </a>
            </div>
          </Card>
        )}

        {/* History */}
        {showHistory && history.length > 0 && (
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">코칭 히스토리</h3>
              <button onClick={() => setShowHistory(false)} className="text-sm text-gray-500 hover:text-gray-700">
                닫기
              </button>
            </div>
            <div className="space-y-3">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition"
                  onClick={() => {
                    if (item.type === "coach_analysis") {
                      setAnalysis(item.content);
                      setActiveTab("analysis");
                    } else {
                      setQuiz(item.content);
                      setActiveTab("quiz");
                    }
                    setShowHistory(false);
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          item.type === "coach_analysis"
                            ? "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                            : "bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300"
                        }`}
                      >
                        {item.type === "coach_analysis" ? "분석" : "퀴즈"}
                      </span>
                      <span className="font-medium text-sm text-gray-900 dark:text-white">{item.title}</span>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {new Date(item.created_at).toLocaleDateString("ko-KR")}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </motion.div>
    </div>
  );
}
