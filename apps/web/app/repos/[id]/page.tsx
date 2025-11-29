"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

export default function RepoDetailPage() {
  const params = useParams();
  const [repo, setRepo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [generatedContent, setGeneratedContent] = useState<string | null>(null);

  useEffect(() => {
    if (params.id) {
      fetchRepo();
    }
  }, [params.id]);

  const fetchRepo = async () => {
    try {
      const res = await fetch(`/api/repos/${params.id}`);
      const data = await res.json();
      setRepo(data);
    } catch (error) {
      console.error("Failed to fetch repo:", error);
    } finally {
      setLoading(false);
    }
  };

  const generateBlog = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`/api/generate/repo-blog/${params.id}`, {
        method: "POST",
      });
      const data = await res.json();
      setGeneratedContent(data.content);
    } catch (error) {
      console.error("Failed to generate blog:", error);
      alert("블로그 생성에 실패했습니다");
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-16">로딩 중...</div>;
  }

  if (!repo) {
    return <div className="container mx-auto px-4 py-16">레포지토리를 찾을 수 없습니다</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">{repo.full_name}</h1>
        <p className="text-gray-600 mb-4">{repo.description}</p>
        <div className="flex gap-4 text-sm">
          {repo.language && <span>📝 {repo.language}</span>}
          <span>⭐ {repo.stars} stars</span>
          <span>🍴 {repo.forks} forks</span>
          <a href={repo.html_url} target="_blank" className="text-primary-600 hover:underline">
            GitHub에서 보기 →
          </a>
        </div>
      </div>

      {/* Recent Commits */}
      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <h2 className="text-2xl font-bold mb-4">최근 커밋</h2>
        {repo.recent_commits?.length > 0 ? (
          <div className="space-y-3">
            {repo.recent_commits.map((commit: any) => (
              <div key={commit.sha} className="border-l-4 border-primary-500 pl-4">
                <p className="font-medium">{commit.message}</p>
                <p className="text-sm text-gray-500">
                  {new Date(commit.committed_at).toLocaleDateString()} ·
                  +{commit.additions || 0} -{commit.deletions || 0}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">커밋이 없습니다</p>
        )}
      </div>

      {/* Blog Generation */}
      <div className="bg-white p-8 rounded-lg shadow">
        <h2 className="text-2xl font-bold mb-4">블로그 초안 생성</h2>
        
        {generatedContent ? (
          <div>
            <div className="flex justify-between items-center mb-4">
              <p className="text-gray-600">AI가 생성한 블로그 초안입니다</p>
              <button
                onClick={() => navigator.clipboard.writeText(generatedContent)}
                className="border border-primary-600 text-primary-600 px-4 py-2 rounded-lg hover:bg-primary-50"
              >
                복사
              </button>
            </div>
            <div className="prose max-w-none border-t pt-4">
              <pre className="whitespace-pre-wrap">{generatedContent}</pre>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-600 mb-6">
              이 프로젝트에 대한 블로그 글 초안을 AI가 자동으로 작성해드립니다
            </p>
            <button
              onClick={generateBlog}
              disabled={generating}
              className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 disabled:bg-gray-400"
            >
              {generating ? "생성 중..." : "블로그 초안 생성"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
