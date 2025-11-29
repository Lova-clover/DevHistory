"use client";

import { useEffect, useState } from "react";

export default function ReposPage() {
  const [repos, setRepos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRepos();
  }, []);

  const fetchRepos = async () => {
    try {
      const res = await fetch("/api/repos");
      const data = await res.json();
      setRepos(data);
    } catch (error) {
      console.error("Failed to fetch repos:", error);
    } finally {
      setLoading(false);
    }
  };

  const triggerSync = async () => {
    try {
      await fetch("/api/collector/trigger/github", { method: "POST" });
      alert("GitHub 동기화를 시작했습니다");
    } catch (error) {
      alert("동기화 실행에 실패했습니다");
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-16">로딩 중...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold">레포지토리</h1>
        <button
          onClick={triggerSync}
          className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
        >
          🔄 동기화
        </button>
      </div>

      {repos.length === 0 ? (
        <div className="bg-white p-12 rounded-lg shadow text-center">
          <p className="text-gray-500 mb-4">아직 레포지토리가 없습니다</p>
          <button
            onClick={triggerSync}
            className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700"
          >
            GitHub에서 가져오기
          </button>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {repos.map((repo) => (
            <a
              key={repo.id}
              href={`/repos/${repo.id}`}
              className="block bg-white p-6 rounded-lg shadow hover:shadow-lg transition"
            >
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-xl font-bold">{repo.full_name}</h3>
                <span className="text-yellow-500">⭐ {repo.stars}</span>
              </div>
              <p className="text-gray-600 mb-4 line-clamp-2">
                {repo.description || "설명 없음"}
              </p>
              <div className="flex gap-4 text-sm text-gray-500">
                {repo.language && <span>📝 {repo.language}</span>}
                <span>🍴 {repo.forks} forks</span>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
