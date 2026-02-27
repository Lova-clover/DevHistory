"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { fetchWithAuth } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";

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
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  const fetchRepo = async () => {
    try {
      const res = await fetchWithAuth(`/api/repos/${params.id}`);
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
      const res = await fetchWithAuth(`/api/generate/repo-blog/${params.id}`, {
        method: "POST",
      });
      const data = await res.json();
      trackEvent({ event_name: "generate_repo_blog", meta: { repo_id: params.id, content_type: "repo_blog", source: "repo_detail" } });
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
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow mb-8">
        <h2 className="text-2xl font-bold mb-4">최근 커밋</h2>
        {repo.recent_commits?.length > 0 ? (
          <div className="space-y-3">
            {repo.recent_commits.map((commit: any) => (
              <div key={commit.sha} className="border-l-4 border-primary-500 pl-4">
                <p className="font-medium">{commit.message}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {new Date(commit.committed_at).toLocaleDateString()} ·
                  +{commit.additions || 0} -{commit.deletions || 0}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400">커밋이 없습니다</p>
        )}
      </div>

      {/* Blog Generation */}
      <div className="bg-white dark:bg-gray-800 p-8 rounded-lg shadow">
        <h2 className="text-2xl font-bold mb-4">블로그 글 작성</h2>
        
        {generatedContent ? (
          <div>
            <div className="flex justify-between items-center mb-4">
              <p className="text-gray-600">AI가 생성한 블로그 글입니다</p>
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
              이 프로젝트에 대한 기술 블로그 글을 AI가 자동으로 작성해드립니다.<br />
              당신의 Velog 스타일로 프로젝트 경험을 정리해보세요.
            </p>
            <button
              onClick={generateBlog}
              disabled={generating}
              className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 disabled:bg-gray-400"
            >
              {generating ? "생성 중..." : "블로그 글 작성"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
