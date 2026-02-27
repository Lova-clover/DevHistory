"use client";

import { useEffect, useState } from "react";
import { fetchWithAuth } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";
import Link from "next/link";

interface GeneratedContent {
  id: string;
  type: string;
  source_ref: string;
  title: string | null;
  content: string;
  created_at: string;
}

export default function ContentsPage() {
  const [contents, setContents] = useState<GeneratedContent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedContent, setSelectedContent] = useState<GeneratedContent | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editedContent, setEditedContent] = useState("");

  useEffect(() => {
    fetchContents();
  }, []);

  const fetchContents = async () => {
    try {
      const res = await fetchWithAuth("/api/generate/contents");
      const data = await res.json();
      setContents(data);
    } catch (error) {
      console.error("Failed to fetch contents:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("정말 삭제하시겠습니까?")) return;

    try {
      await fetchWithAuth(`/api/generate/content/${id}`, {
        method: "DELETE",
      });
      trackEvent({ event_name: "content_deleted", meta: { content_id: id } });
      setContents(contents.filter((c) => c.id !== id));
      if (selectedContent?.id === id) {
        setSelectedContent(null);
      }
      alert("삭제되었습니다");
    } catch (error) {
      console.error("Failed to delete content:", error);
      alert("삭제에 실패했습니다");
    }
  };

  const handleEdit = () => {
    if (selectedContent) {
      setEditedContent(selectedContent.content);
      setEditMode(true);
    }
  };

  const handleSave = async () => {
    if (!selectedContent) return;

    try {
      await fetchWithAuth(`/api/generate/content/${selectedContent.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: editedContent }),
      });
      
      // Update local state
      setContents(
        contents.map((c) =>
          c.id === selectedContent.id ? { ...c, content: editedContent } : c
        )
      );
      setSelectedContent({ ...selectedContent, content: editedContent });
      setEditMode(false);
      alert("저장되었습니다");
    } catch (error) {
      console.error("Failed to update content:", error);
      alert("저장에 실패했습니다");
    }
  };

  const handleCancel = () => {
    setEditMode(false);
    setEditedContent("");
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case "repo_blog":
        return "레포지토리 블로그";
      case "weekly_report":
        return "주간 리포트";
      default:
        return type;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "repo_blog":
        return "bg-blue-100 text-blue-800";
      case "weekly_report":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-16">로딩 중...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">생성된 콘텐츠</h1>
        <p className="text-gray-600">AI가 생성한 블로그 글과 주간 리포트 목록</p>
      </div>

      {contents.length === 0 ? (
        <div className="bg-white p-12 rounded-lg shadow text-center">
          <p className="text-gray-500 mb-4">아직 생성된 콘텐츠가 없습니다</p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/repos"
              className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700"
            >
              레포지토리에서 블로그 작성하기
            </Link>
            <Link
              href="/weekly"
              className="border border-primary-600 text-primary-600 px-6 py-3 rounded-lg hover:bg-primary-50"
            >
              주간 리포트 생성하기
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Contents List */}
          <div className="lg:col-span-1 space-y-4">
            {contents.map((content) => (
              <div
                key={content.id}
                onClick={() => setSelectedContent(content)}
                className={`bg-white p-4 rounded-lg shadow cursor-pointer hover:shadow-md transition ${
                  selectedContent?.id === content.id ? "ring-2 ring-primary-500" : ""
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <span
                    className={`text-xs px-2 py-1 rounded ${getTypeColor(content.type)}`}
                  >
                    {getTypeLabel(content.type)}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(content.created_at).toLocaleDateString()}
                  </span>
                </div>
                <h3 className="font-semibold text-sm mb-1">
                  {content.title || "제목 없음"}
                </h3>
                <p className="text-xs text-gray-500 line-clamp-2">
                  {content.content.substring(0, 100)}...
                </p>
              </div>
            ))}
          </div>

          {/* Content Viewer */}
          <div className="lg:col-span-2">
            {selectedContent ? (
              <div className="bg-white dark:bg-gray-800 p-8 rounded-lg shadow">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <span
                      className={`text-sm px-3 py-1 rounded ${getTypeColor(
                        selectedContent.type
                      )}`}
                    >
                      {getTypeLabel(selectedContent.type)}
                    </span>
                    <h2 className="text-2xl font-bold mt-2">
                      {selectedContent.title || "제목 없음"}
                    </h2>
                    <p className="text-sm text-gray-500 mt-1">
                      {new Date(selectedContent.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    {editMode ? (
                      <>
                        <button
                          onClick={handleSave}
                          className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
                        >
                          저장
                        </button>
                        <button
                          onClick={handleCancel}
                          className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50"
                        >
                          취소
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() =>
                            navigator.clipboard.writeText(selectedContent.content)
                          }
                          className="border border-primary-600 text-primary-600 px-4 py-2 rounded-lg hover:bg-primary-50"
                        >
                          복사
                        </button>
                        <button
                          onClick={handleEdit}
                          className="border border-blue-600 text-blue-600 px-4 py-2 rounded-lg hover:bg-blue-50"
                        >
                          수정
                        </button>
                        <button
                          onClick={() => handleDelete(selectedContent.id)}
                          className="border border-red-600 text-red-600 px-4 py-2 rounded-lg hover:bg-red-50"
                        >
                          삭제
                        </button>
                      </>
                    )}
                  </div>
                </div>
                <div className="prose max-w-none">
                  {editMode ? (
                    <textarea
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      className="w-full h-96 p-4 border rounded-lg font-mono text-sm"
                    />
                  ) : (
                    <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded">
                      {selectedContent.content}
                    </pre>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white p-12 rounded-lg shadow text-center">
                <p className="text-gray-500">
                  왼쪽에서 콘텐츠를 선택하면 내용을 볼 수 있습니다
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
