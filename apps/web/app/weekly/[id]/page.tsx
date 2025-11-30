"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

export default function WeeklyDetailPage() {
  const params = useParams();
  const [weekly, setWeekly] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (params.id) {
      fetchWeekly();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  const fetchWeekly = async () => {
    try {
      const res = await fetch(`/api/weekly/${params.id}`);
      const data = await res.json();
      setWeekly(data);
    } catch (error) {
      console.error("Failed to fetch weekly:", error);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`/api/generate/weekly-report/${params.id}`, {
        method: "POST",
      });
      const data = await res.json();
      setWeekly({ ...weekly, llm_summary: data.content });
    } catch (error) {
      console.error("Failed to generate report:", error);
      alert("리포트 생성에 실패했습니다");
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-16">로딩 중...</div>;
  }

  if (!weekly) {
    return <div className="container mx-auto px-4 py-16">주간 데이터를 찾을 수 없습니다</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-2">
        주간 리포트
      </h1>
      <p className="text-gray-600 mb-8">
        {weekly.week_start} ~ {weekly.week_end}
      </p>

      {/* Summary Stats */}
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm mb-2">커밋</h3>
          <p className="text-3xl font-bold text-primary-600">{weekly.commit_count}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm mb-2">문제 풀이</h3>
          <p className="text-3xl font-bold text-green-600">{weekly.problem_count}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm mb-2">노트</h3>
          <p className="text-3xl font-bold text-purple-600">{weekly.note_count}</p>
        </div>
      </div>

      {/* LLM Summary */}
      <div className="bg-white p-8 rounded-lg shadow">
        {weekly.llm_summary ? (
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">AI 생성 리포트</h2>
              <button
                onClick={() => navigator.clipboard.writeText(weekly.llm_summary)}
                className="border border-primary-600 text-primary-600 px-4 py-2 rounded-lg hover:bg-primary-50"
              >
                복사
              </button>
            </div>
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap">{weekly.llm_summary}</pre>
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600 mb-6">
              아직 AI 리포트가 생성되지 않았습니다
            </p>
            <button
              onClick={generateReport}
              disabled={generating}
              className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 disabled:bg-gray-400"
            >
              {generating ? "생성 중..." : "AI 리포트 생성"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
