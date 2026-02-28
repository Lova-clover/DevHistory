"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { fetchWithAuth } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";

type WeeklyDetail = {
  id: string;
  week_start: string;
  week_end: string;
  commit_count: number;
  problem_count: number;
  note_count: number;
  llm_summary?: string | null;
};

type GeneratedContent = {
  id: string;
  type: string;
  source_ref: string;
  content: string;
  status?: string;
  created_at: string;
};

export default function WeeklyDetailPage() {
  const params = useParams<{ id: string }>();
  const weeklyId = params?.id;

  const [weekly, setWeekly] = useState<WeeklyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const fetchWeekly = useCallback(async () => {
    if (!weeklyId) return;
    try {
      const res = await fetchWithAuth(`/api/weekly/${weeklyId}`);
      if (!res.ok) {
        setWeekly(null);
        return;
      }
      const data = await res.json();
      setWeekly(data);
    } catch (error) {
      console.error("Failed to fetch weekly:", error);
      setWeekly(null);
    } finally {
      setLoading(false);
    }
  }, [weeklyId]);

  useEffect(() => {
    fetchWeekly();
  }, [fetchWeekly]);

  const pollWeeklyReport = useCallback(async (): Promise<string | null> => {
    if (!weeklyId) return null;
    const sourceRef = `weekly:${weeklyId}`;
    const maxAttempts = 20;
    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      try {
        const listRes = await fetchWithAuth("/api/generate/contents");
        if (listRes.ok) {
          const list = (await listRes.json()) as GeneratedContent[];
          const matched = list
            .filter(
              (item) =>
                item.type === "weekly_report" &&
                item.source_ref === sourceRef &&
                item.status === "completed" &&
                item.content
            )
            .sort(
              (a, b) =>
                new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
            );
          if (matched.length > 0) {
            return matched[0].content;
          }
        }
      } catch (error) {
        console.error("Failed to poll weekly generated content:", error);
      }
      await new Promise((resolve) => setTimeout(resolve, 1500));
    }
    return null;
  }, [weeklyId]);

  const generateReport = async () => {
    if (!weeklyId) return;

    setGenerating(true);
    try {
      const res = await fetchWithAuth(`/api/generate/weekly-report/${weeklyId}`, {
        method: "POST",
      });
      const data = await res.json();

      trackEvent({
        event_name: "generate_weekly_report",
        meta: {
          weekly_id: weeklyId,
          content_type: "weekly_report",
          source: "weekly_detail",
        },
      });

      if (data?.content) {
        setWeekly((prev) => (prev ? { ...prev, llm_summary: data.content } : prev));
        return;
      }

      const polledContent = await pollWeeklyReport();
      if (polledContent) {
        setWeekly((prev) => (prev ? { ...prev, llm_summary: polledContent } : prev));
      } else {
        alert("리포트 생성이 진행 중입니다. 잠시 후 다시 확인해주세요.");
      }
    } catch (error) {
      console.error("Failed to generate report:", error);
      alert("리포트 생성에 실패했습니다.");
    } finally {
      setGenerating(false);
      fetchWeekly();
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-16">Loading...</div>;
  }

  if (!weekly) {
    return <div className="container mx-auto px-4 py-16">Weekly summary not found.</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-2">Weekly Report</h1>
      <p className="text-gray-600 mb-8">
        {weekly.week_start} ~ {weekly.week_end}
      </p>

      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-gray-500 dark:text-gray-400 text-sm mb-2">Commits</h3>
          <p className="text-3xl font-bold text-primary-600 dark:text-primary-400">
            {weekly.commit_count}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-gray-500 dark:text-gray-400 text-sm mb-2">Problems</h3>
          <p className="text-3xl font-bold text-green-600 dark:text-green-400">
            {weekly.problem_count}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-gray-500 dark:text-gray-400 text-sm mb-2">Notes</h3>
          <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">
            {weekly.note_count}
          </p>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 p-8 rounded-lg shadow">
        {weekly.llm_summary ? (
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">AI Report</h2>
              <button
                onClick={() => navigator.clipboard.writeText(weekly.llm_summary || "")}
                className="border border-primary-600 text-primary-600 px-4 py-2 rounded-lg hover:bg-primary-50 dark:hover:bg-primary-900/20"
              >
                Copy
              </button>
            </div>
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap bg-gray-50 dark:bg-gray-900 p-4 rounded">
                {weekly.llm_summary}
              </pre>
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              아직 AI 리포트가 생성되지 않았습니다.
            </p>
            <button
              onClick={generateReport}
              disabled={generating}
              className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 disabled:bg-gray-400"
            >
              {generating ? "Generating..." : "Generate AI Report"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
