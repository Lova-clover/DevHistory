"use client";

import { useEffect, useState } from "react";

export default function DashboardPage() {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSummary();
  }, []);

  const fetchSummary = async () => {
    try {
      const res = await fetch("/api/dashboard/summary?range=week");
      const data = await res.json();
      setSummary(data);
    } catch (error) {
      console.error("Failed to fetch summary:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-16">로딩 중...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">대시보드</h1>

      {/* Summary Cards */}
      <div className="grid md:grid-cols-3 gap-6 mb-12">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium mb-2">이번 주 커밋</h3>
          <p className="text-4xl font-bold text-primary-600">
            {summary?.commit_count || 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium mb-2">이번 주 문제</h3>
          <p className="text-4xl font-bold text-green-600">
            {summary?.problem_count || 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium mb-2">이번 주 노트</h3>
          <p className="text-4xl font-bold text-purple-600">
            {summary?.note_count || 0}
          </p>
        </div>
      </div>

      {/* Activity Heatmap Placeholder */}
      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <h2 className="text-2xl font-bold mb-4">활동 히트맵</h2>
        <div className="h-64 bg-gray-100 rounded flex items-center justify-center text-gray-500">
          차트가 여기에 표시됩니다 (Chart.js, Recharts 등으로 구현 예정)
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-bold mb-4">빠른 실행</h3>
          <div className="space-y-2">
            <button className="w-full text-left px-4 py-2 border rounded hover:bg-gray-50">
              📊 주간 리포트 생성
            </button>
            <button className="w-full text-left px-4 py-2 border rounded hover:bg-gray-50">
              🔄 GitHub 동기화
            </button>
            <button className="w-full text-left px-4 py-2 border rounded hover:bg-gray-50">
              ✍️ 새 노트 작성
            </button>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-bold mb-4">최근 활동</h3>
          <div className="space-y-3">
            <div className="text-sm">
              <span className="text-gray-500">방금 전</span>
              <p>FreshGuard 레포지토리에 커밋</p>
            </div>
            <div className="text-sm">
              <span className="text-gray-500">2시간 전</span>
              <p>백준 1234번 문제 해결</p>
            </div>
            <div className="text-sm">
              <span className="text-gray-500">어제</span>
              <p>주간 리포트 생성</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
