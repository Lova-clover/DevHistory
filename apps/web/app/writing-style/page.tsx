"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Sparkles, Save, RefreshCw, BookOpen, Palette, PenTool } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { fetchWithAuth } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";

interface StyleProfile {
  language: string;
  tone: string;
  blog_structure: string[];
  report_structure: string[];
  extra_instructions: string | null;
  learned_style_prompt: string | null;
  learned_at: string | null;
}

export default function WritingStylePage() {
  const [style, setStyle] = useState<StyleProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [learning, setLearning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState(false);
  const [promptDraft, setPromptDraft] = useState("");
  const [editingStyle, setEditingStyle] = useState(false);

  // Editable style fields
  const [language, setLanguage] = useState("ko");
  const [tone, setTone] = useState("technical");
  const [blogStructure, setBlogStructure] = useState("Intro, Problem, Approach, Result, Next");
  const [reportStructure, setReportStructure] = useState("Summary, What I did, Learned, Next");
  const [extraInstructions, setExtraInstructions] = useState("");

  useEffect(() => {
    fetchStyle();
  }, []);

  const fetchStyle = async () => {
    try {
      const res = await fetchWithAuth("/api/profile/style");
      const data = await res.json();
      setStyle(data);
      setLanguage(data.language || "ko");
      setTone(data.tone || "technical");
      setBlogStructure((data.blog_structure || []).join(", "));
      setReportStructure((data.report_structure || []).join(", "));
      setExtraInstructions(data.extra_instructions || "");
      if (data.learned_style_prompt) {
        setPromptDraft(data.learned_style_prompt);
      }
    } catch (error) {
      console.error("Failed to fetch style:", error);
    } finally {
      setLoading(false);
    }
  };

  const learnStyle = async () => {
    setLearning(true);
    try {
      const res = await fetchWithAuth("/api/profile/style/learn", { method: "POST" });
      const data = await res.json();
      trackEvent({ event_name: "style_learn_triggered" });

      if (data.status === "success" && data.learned_style_prompt) {
        setStyle((prev) =>
          prev ? { ...prev, learned_style_prompt: data.learned_style_prompt, learned_at: new Date().toISOString() } : prev
        );
        setPromptDraft(data.learned_style_prompt);
        alert("✅ Velog 글쓰기 스타일 분석이 완료되었습니다!");
      } else if (data.status === "processing") {
        alert("분석이 진행 중입니다. 잠시 후 새로고침해주세요.");
      } else {
        alert(`분석 실패: ${data.error || "알 수 없는 오류"}`);
      }
    } catch (error: any) {
      alert("스타일 분석에 실패했습니다");
    } finally {
      setLearning(false);
    }
  };

  const saveLearnedPrompt = async () => {
    setSaving(true);
    try {
      await fetchWithAuth("/api/profile/style/learned-prompt", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ learned_style_prompt: promptDraft }),
      });
      setStyle((prev) => (prev ? { ...prev, learned_style_prompt: promptDraft } : prev));
      setEditingPrompt(false);
      alert("스타일 프롬프트가 저장되었습니다");
    } catch {
      alert("저장에 실패했습니다");
    } finally {
      setSaving(false);
    }
  };

  const saveStyleProfile = async () => {
    setSaving(true);
    try {
      const res = await fetchWithAuth("/api/profile/style", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          language,
          tone,
          blog_structure: blogStructure.split(",").map((s) => s.trim()).filter(Boolean),
          report_structure: reportStructure.split(",").map((s) => s.trim()).filter(Boolean),
          extra_instructions: extraInstructions || null,
        }),
      });
      const data = await res.json();
      setStyle(data);
      setEditingStyle(false);
      alert("스타일 설정이 저장되었습니다");
    } catch {
      alert("저장에 실패했습니다");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-16 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">스타일 정보를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">글쓰기 스타일</h1>
          <p className="text-gray-600 dark:text-gray-400">
            AI가 당신의 스타일로 글을 쓸 수 있도록 학습하고, 세부 설정을 조정하세요
          </p>
        </div>

        {/* Velog Style Learning */}
        <Card className="p-6 border-2 border-primary-200 dark:border-primary-800">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-primary-100 dark:bg-primary-900/30 rounded-xl flex-shrink-0">
              <Sparkles className="w-7 h-7 text-primary-600 dark:text-primary-400" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-1">
                Velog 글쓰기 스타일 학습
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Velog에 작성한 블로그 글을 AI가 분석하여 당신만의 글쓰기 스타일 프롬프트를 자동 생성합니다.
                이 프롬프트를 통해 AI가 당신의 문체와 구조를 흉내낼 수 있습니다.
              </p>

              {style?.learned_style_prompt ? (
                <div className="space-y-4">
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">학습된 스타일 프롬프트</span>
                      {style.learned_at && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          학습일: {new Date(style.learned_at).toLocaleDateString("ko-KR")}
                        </span>
                      )}
                    </div>
                    {editingPrompt ? (
                      <textarea
                        value={promptDraft}
                        onChange={(e) => setPromptDraft(e.target.value)}
                        rows={8}
                        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm font-mono focus:ring-2 focus:ring-primary-500 resize-y"
                      />
                    ) : (
                      <div className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap leading-relaxed">
                        {style.learned_style_prompt}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {editingPrompt ? (
                      <>
                        <Button onClick={saveLearnedPrompt} disabled={saving} variant="primary">
                          <Save className="w-4 h-4 mr-1.5" />
                          {saving ? "저장 중..." : "저장"}
                        </Button>
                        <Button
                          onClick={() => {
                            setEditingPrompt(false);
                            setPromptDraft(style.learned_style_prompt || "");
                          }}
                          variant="ghost"
                        >
                          취소
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button onClick={() => setEditingPrompt(true)} variant="outline">
                          <PenTool className="w-4 h-4 mr-1.5" />
                          프롬프트 수정
                        </Button>
                        <Button onClick={learnStyle} disabled={learning} variant="outline">
                          <RefreshCw className={`w-4 h-4 mr-1.5 ${learning ? "animate-spin" : ""}`} />
                          {learning ? "분석 중..." : "다시 학습"}
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-6 bg-gray-50 dark:bg-gray-800 rounded-xl border border-dashed border-gray-300 dark:border-gray-600">
                  <BookOpen className="w-10 h-10 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-500 dark:text-gray-400 mb-4">
                    아직 학습된 스타일이 없습니다
                  </p>
                  <Button onClick={learnStyle} disabled={learning} variant="primary">
                    <Sparkles className={`w-4 h-4 mr-1.5 ${learning ? "animate-pulse" : ""}`} />
                    {learning ? "Velog 분석 중..." : "Velog 스타일 학습하기"}
                  </Button>
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* Manual Style Settings */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-xl">
                <Palette className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">글쓰기 설정</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">AI 글 생성 시 적용되는 기본 설정</p>
              </div>
            </div>
            {!editingStyle ? (
              <Button onClick={() => setEditingStyle(true)} variant="outline">
                수정
              </Button>
            ) : (
              <div className="flex gap-2">
                <Button onClick={() => setEditingStyle(false)} variant="ghost">
                  취소
                </Button>
                <Button onClick={saveStyleProfile} disabled={saving} variant="primary">
                  {saving ? "저장 중..." : "저장"}
                </Button>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">언어</label>
              {editingStyle ? (
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                >
                  <option value="ko">한국어</option>
                  <option value="en">English</option>
                </select>
              ) : (
                <p className="px-4 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg text-gray-900 dark:text-white">
                  {language === "ko" ? "한국어" : "English"}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">톤/어투</label>
              {editingStyle ? (
                <select
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                >
                  <option value="technical">기술적 (Technical)</option>
                  <option value="casual">친근한 (Casual)</option>
                  <option value="study-note">공부 노트 (Study Note)</option>
                </select>
              ) : (
                <p className="px-4 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg text-gray-900 dark:text-white">
                  {tone === "technical" ? "기술적" : tone === "casual" ? "친근한" : "공부 노트"}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                블로그 글 구조 (쉼표 구분)
              </label>
              {editingStyle ? (
                <input
                  type="text"
                  value={blogStructure}
                  onChange={(e) => setBlogStructure(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                />
              ) : (
                <p className="px-4 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg text-gray-900 dark:text-white">
                  {blogStructure}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                리포트 구조 (쉼표 구분)
              </label>
              {editingStyle ? (
                <input
                  type="text"
                  value={reportStructure}
                  onChange={(e) => setReportStructure(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                />
              ) : (
                <p className="px-4 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg text-gray-900 dark:text-white">
                  {reportStructure}
                </p>
              )}
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                추가 지시사항
              </label>
              {editingStyle ? (
                <textarea
                  value={extraInstructions}
                  onChange={(e) => setExtraInstructions(e.target.value)}
                  rows={3}
                  placeholder="예: 코드 블록을 많이 사용해줘, 이모지를 적극 활용해줘"
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                />
              ) : (
                <p className="px-4 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg text-gray-900 dark:text-white min-h-[60px]">
                  {extraInstructions || "없음"}
                </p>
              )}
            </div>
          </div>
        </Card>

        {/* Info */}
        <Card className="p-6 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">💡 스타일 학습 안내</h3>
          <ul className="space-y-1.5 text-sm text-blue-800 dark:text-blue-200">
            <li>• 학습된 프롬프트는 블로그 글 생성 시 자동으로 적용됩니다.</li>
            <li>• 프롬프트를 직접 수정하여 원하는 스타일로 미세 조정할 수 있습니다.</li>
            <li>• Velog에 새 글을 발행한 후 다시 학습하면 최신 스타일이 반영됩니다.</li>
            <li>• 학습에는 최근 블로그 글 최대 5개가 사용됩니다.</li>
          </ul>
        </Card>
      </motion.div>
    </div>
  );
}
