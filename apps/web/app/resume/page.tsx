"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  FileText,
  Download,
  Copy,
  Check,
  RefreshCw,
  History,
  Briefcase,
  Heart,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { fetchWithAuth } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";

interface ResumeHistoryItem {
  id: string;
  type: string;
  title: string;
  content: string;
  created_at: string;
}

export default function ResumePage() {
  const [resumeType, setResumeType] = useState<"resume" | "cover_letter">("resume");
  const [extraContext, setExtraContext] = useState("");
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [history, setHistory] = useState<ResumeHistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  const handleGenerate = async () => {
    setGenerating(true);
    setResult(null);
    try {
      const res = await fetchWithAuth("/api/resume/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_type: resumeType,
          extra_context: extraContext || null,
        }),
      });
      const data = await res.json();
      trackEvent({ event_name: "resume_generated", meta: { type: resumeType } });
      if (data.status === "success") {
        setResult(data.content);
      } else {
        alert(data.message || data.error || "생성에 실패했습니다");
      }
    } catch {
      alert("요청에 실패했습니다");
    } finally {
      setGenerating(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetchWithAuth("/api/resume/history");
      const data = await res.json();
      setHistory(data);
      setShowHistory(true);
    } catch {
      alert("히스토리를 불러오지 못했습니다");
    }
  };

  const copyToClipboard = () => {
    if (!result) return;
    navigator.clipboard.writeText(result);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadMarkdown = () => {
    if (!result) return;
    const blob = new Blob([result], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = resumeType === "resume" ? "이력서.md" : "자기소개서.md";
    a.click();
    URL.revokeObjectURL(url);
  };

  const renderMarkdown = (text: string) => {
    return text
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
      .replace(/\n\n/g, "<br/><br/>")
      .replace(/\n/g, "<br/>");
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
              📄 이력서 & 자기소개서
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              포트폴리오 데이터를 기반으로 AI가 작성해드립니다
            </p>
          </div>
          <Button onClick={fetchHistory} variant="outline">
            <History className="w-4 h-4 mr-1.5" />
            히스토리
          </Button>
        </div>

        {/* Generator */}
        <Card className="p-6">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">생성 옵션</h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
            <button
              onClick={() => setResumeType("resume")}
              className={`flex items-center gap-3 p-4 rounded-xl border-2 transition ${
                resumeType === "resume"
                  ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20"
                  : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
              }`}
            >
              <Briefcase
                className={`w-6 h-6 ${
                  resumeType === "resume"
                    ? "text-primary-600 dark:text-primary-400"
                    : "text-gray-400"
                }`}
              />
              <div className="text-left">
                <p
                  className={`font-semibold ${
                    resumeType === "resume"
                      ? "text-primary-700 dark:text-primary-300"
                      : "text-gray-700 dark:text-gray-300"
                  }`}
                >
                  이력서
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  기술 스택, 프로젝트, 경력 중심
                </p>
              </div>
            </button>
            <button
              onClick={() => setResumeType("cover_letter")}
              className={`flex items-center gap-3 p-4 rounded-xl border-2 transition ${
                resumeType === "cover_letter"
                  ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20"
                  : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
              }`}
            >
              <Heart
                className={`w-6 h-6 ${
                  resumeType === "cover_letter"
                    ? "text-primary-600 dark:text-primary-400"
                    : "text-gray-400"
                }`}
              />
              <div className="text-left">
                <p
                  className={`font-semibold ${
                    resumeType === "cover_letter"
                      ? "text-primary-700 dark:text-primary-300"
                      : "text-gray-700 dark:text-gray-300"
                  }`}
                >
                  자기소개서
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  동기, 성장 과정, 비전 중심
                </p>
              </div>
            </button>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              추가 컨텍스트 (선택)
            </label>
            <textarea
              value={extraContext}
              onChange={(e) => setExtraContext(e.target.value)}
              placeholder="지원하는 회사, 포지션, 강조하고 싶은 점 등을 입력하세요..."
              rows={3}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <Button onClick={handleGenerate} disabled={generating} variant="primary" className="w-full sm:w-auto">
            {generating ? (
              <>
                <RefreshCw className="w-4 h-4 mr-1.5 animate-spin" />
                생성 중... (최대 45초)
              </>
            ) : (
              <>
                <FileText className="w-4 h-4 mr-1.5" />
                {resumeType === "resume" ? "이력서 생성" : "자기소개서 생성"}
              </>
            )}
          </Button>
        </Card>

        {/* Result Viewer */}
        {result && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                  {resumeType === "resume" ? "📋 생성된 이력서" : "💬 생성된 자기소개서"}
                </h3>
                <div className="flex gap-2">
                  <Button onClick={copyToClipboard} variant="outline" size="sm">
                    {copied ? (
                      <Check className="w-4 h-4 text-green-600" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                  <Button onClick={downloadMarkdown} variant="outline" size="sm">
                    <Download className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              <div
                className="prose dark:prose-invert max-w-none text-gray-800 dark:text-gray-200 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: renderMarkdown(result) }}
              />
            </Card>
          </motion.div>
        )}

        {/* History */}
        {showHistory && history.length > 0 && (
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">생성 히스토리</h3>
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
                    setResult(item.content);
                    setResumeType(item.type === "resume" ? "resume" : "cover_letter");
                    setShowHistory(false);
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          item.type === "resume"
                            ? "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                            : "bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300"
                        }`}
                      >
                        {item.type === "resume" ? "이력서" : "자기소개서"}
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

        {showHistory && history.length === 0 && (
          <Card className="p-8 text-center">
            <p className="text-gray-500 dark:text-gray-400">아직 생성된 이력서가 없습니다</p>
          </Card>
        )}
      </motion.div>
    </div>
  );
}
