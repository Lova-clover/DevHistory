"use client";

import { useEffect, useState } from "react";

export default function WeeklyPage() {
  const [weeklies, setWeeklies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

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

  if (loading) {
    return <div className="container mx-auto px-4 py-16">로딩 중...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold">주간 리포트</h1>
        <button className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">
          새 리포트 생성
        </button>
      </div>

      {weeklies.length === 0 ? (
        <div className="bg-white p-12 rounded-lg shadow text-center">
          <p className="text-gray-500 mb-4">아직 생성된 주간 리포트가 없습니다</p>
          <button className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700">
            첫 리포트 생성하기
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {weeklies.map((weekly) => (
            <a
              key={weekly.id}
              href={`/weekly/${weekly.id}`}
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
