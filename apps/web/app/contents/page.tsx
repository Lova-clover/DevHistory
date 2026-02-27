"use client";

import { useEffect, useState, useMemo } from "react";
import { fetchWithAuth } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Copy,
  Check,
  Pencil,
  Trash2,
  FileText,
  BarChart3,
  Clock,
  Download,
  RefreshCw,
  Sparkles,
  X,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface GeneratedContent {
  id: string;
  type: string;
  source_ref: string;
  title: string | null;
  content: string;
  status?: string;
  created_at: string;
}

type FilterType = "all" | "repo_blog" | "weekly_report";
type SortType = "newest" | "oldest" | "title";

export default function ContentsPage() {
  const [contents, setContents] = useState<GeneratedContent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedContent, setSelectedContent] = useState<GeneratedContent | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editedContent, setEditedContent] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<FilterType>("all");
  const [sortType, setSortType] = useState<SortType>("newest");
  const [copied, setCopied] = useState(false);
  const [showMobileList, setShowMobileList] = useState(true);

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
      await fetchWithAuth(`/api/generate/content/${id}`, { method: "DELETE" });
      trackEvent({ event_name: "content_deleted", meta: { content_id: id } });
      setContents(contents.filter((c) => c.id !== id));
      if (selectedContent?.id === id) setSelectedContent(null);
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
      setContents(
        contents.map((c) =>
          c.id === selectedContent.id ? { ...c, content: editedContent } : c
        )
      );
      setSelectedContent({ ...selectedContent, content: editedContent });
      setEditMode(false);
    } catch (error) {
      console.error("Failed to update content:", error);
      alert("저장에 실패했습니다");
    }
  };

  const handleCopy = () => {
    if (selectedContent) {
      navigator.clipboard.writeText(selectedContent.content);
      setCopied(true);
      trackEvent({ event_name: "content_copied", meta: { content_id: selectedContent.id } });
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (!selectedContent) return;
    const blob = new Blob([selectedContent.content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${selectedContent.title || "content"}.md`;
    a.click();
    URL.revokeObjectURL(url);
    trackEvent({ event_name: "content_downloaded", meta: { content_id: selectedContent.id } });
  };

  const filteredContents = useMemo(() => {
    let result = [...contents];
    if (filterType !== "all") {
      result = result.filter((c) => c.type === filterType);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (c) =>
          (c.title || "").toLowerCase().includes(q) ||
          c.content.toLowerCase().includes(q)
      );
    }
    switch (sortType) {
      case "oldest":
        result.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
        break;
      case "title":
        result.sort((a, b) => (a.title || "").localeCompare(b.title || ""));
        break;
      default:
        result.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    }
    return result;
  }, [contents, filterType, searchQuery, sortType]);

  const stats = useMemo(() => {
    const total = contents.length;
    const blogs = contents.filter((c) => c.type === "repo_blog").length;
    const reports = contents.filter((c) => c.type === "weekly_report").length;
    const totalChars = contents.reduce((acc, c) => acc + c.content.length, 0);
    return { total, blogs, reports, totalChars };
  }, [contents]);

  const getTypeLabel = (type: string) => {
    switch (type) {
      case "repo_blog": return "레포 블로그";
      case "weekly_report": return "주간 리포트";
      default: return type;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "repo_blog": return "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300";
      case "weekly_report": return "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300";
      default: return "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300";
    }
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case "generating":
      case "pending":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300">
            <RefreshCw className="w-3 h-3 animate-spin" /> 생성 중
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300">
            실패
          </span>
        );
      default:
        return null;
    }
  };

  const formatRelativeDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 60) return `${diffMins}분 전`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}시간 전`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}일 전`;
    return date.toLocaleDateString("ko-KR");
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
      .replace(/^(\d+)\. (.+)$/gm, '<li class="ml-4 list-decimal">$2</li>')
      .replace(/\n\n/g, "<br/><br/>")
      .replace(/\n/g, "<br/>");
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-16 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">콘텐츠를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">생성된 콘텐츠</h1>
            <p className="text-gray-600 dark:text-gray-400">AI가 작성한 블로그 글과 주간 리포트를 관리하세요</p>
          </div>
          <div className="flex gap-3">
            <Link href="/repos">
              <Button variant="primary">
                <Sparkles className="w-4 h-4 mr-1.5" />
                새 블로그 작성
              </Button>
            </Link>
            <Link href="/weekly">
              <Button variant="outline">주간 리포트 생성</Button>
            </Link>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "전체 콘텐츠", value: stats.total, icon: FileText, color: "text-primary-600 dark:text-primary-400" },
            { label: "레포 블로그", value: stats.blogs, icon: Sparkles, color: "text-blue-600 dark:text-blue-400" },
            { label: "주간 리포트", value: stats.reports, icon: BarChart3, color: "text-emerald-600 dark:text-emerald-400" },
            { label: "총 글자 수", value: stats.totalChars.toLocaleString(), icon: FileText, color: "text-purple-600 dark:text-purple-400" },
          ].map((stat) => (
            <Card key={stat.label} className="p-4">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg bg-gray-100 dark:bg-gray-800 ${stat.color}`}>
                  <stat.icon className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{stat.label}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {contents.length === 0 ? (
          <Card className="p-12 text-center">
            <div className="max-w-md mx-auto">
              <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-4">
                <FileText className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">아직 생성된 콘텐츠가 없습니다</h3>
              <p className="text-gray-500 dark:text-gray-400 mb-6">레포지토리에서 블로그를 작성하거나 주간 리포트를 생성해보세요</p>
              <div className="flex gap-3 justify-center">
                <Link href="/repos">
                  <Button variant="primary">레포지토리에서 블로그 작성</Button>
                </Link>
                <Link href="/weekly">
                  <Button variant="outline">주간 리포트 생성</Button>
                </Link>
              </div>
            </div>
          </Card>
        ) : (
          <>
            {/* Search & Filter Bar */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="제목이나 내용으로 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery("")}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
              <div className="flex gap-2">
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value as FilterType)}
                  className="px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-primary-500"
                >
                  <option value="all">전체 유형</option>
                  <option value="repo_blog">레포 블로그</option>
                  <option value="weekly_report">주간 리포트</option>
                </select>
                <select
                  value={sortType}
                  onChange={(e) => setSortType(e.target.value as SortType)}
                  className="px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-primary-500"
                >
                  <option value="newest">최신순</option>
                  <option value="oldest">오래된순</option>
                  <option value="title">제목순</option>
                </select>
              </div>
            </div>

            {/* Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* List Panel */}
              <div className={`lg:col-span-4 xl:col-span-3 space-y-2 ${!showMobileList && selectedContent ? "hidden lg:block" : ""}`}>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">{filteredContents.length}개의 콘텐츠</p>
                <div className="space-y-2 max-h-[calc(100vh-320px)] overflow-y-auto pr-1">
                  <AnimatePresence>
                    {filteredContents.map((content, idx) => (
                      <motion.div
                        key={content.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ delay: idx * 0.03 }}
                        onClick={() => {
                          setSelectedContent(content);
                          setEditMode(false);
                          setShowMobileList(false);
                        }}
                        className={`group p-3.5 rounded-xl border cursor-pointer transition-all duration-200 ${
                          selectedContent?.id === content.id
                            ? "bg-primary-50 dark:bg-primary-900/20 border-primary-300 dark:border-primary-700 shadow-sm"
                            : "bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-primary-200 dark:hover:border-primary-800 hover:shadow-sm"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2 mb-1.5">
                          <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${getTypeColor(content.type)}`}>
                            {getTypeLabel(content.type)}
                          </span>
                          <div className="flex items-center gap-1.5">
                            {getStatusBadge(content.status)}
                            <span className="text-[11px] text-gray-400 dark:text-gray-500 whitespace-nowrap">
                              {formatRelativeDate(content.created_at)}
                            </span>
                          </div>
                        </div>
                        <h3 className="font-semibold text-sm text-gray-900 dark:text-white leading-tight mb-1">
                          {content.title || "제목 없음"}
                        </h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 leading-relaxed">
                          {content.content.replace(/[#*`\-]/g, "").substring(0, 120)}
                        </p>
                        <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(content.id);
                            }}
                            className="text-[11px] text-red-500 hover:text-red-700"
                          >
                            삭제
                          </button>
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </div>

              {/* Content Viewer */}
              <div className="lg:col-span-8 xl:col-span-9">
                {selectedContent ? (
                  <motion.div
                    key={selectedContent.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden"
                  >
                    {/* Viewer Header */}
                    <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <button
                            onClick={() => {
                              setSelectedContent(null);
                              setShowMobileList(true);
                            }}
                            className="lg:hidden text-sm text-primary-600 mb-2 flex items-center gap-1"
                          >
                            ← 목록으로
                          </button>
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${getTypeColor(selectedContent.type)}`}>
                              {getTypeLabel(selectedContent.type)}
                            </span>
                            {getStatusBadge(selectedContent.status)}
                          </div>
                          <h2 className="text-2xl font-bold text-gray-900 dark:text-white leading-tight">
                            {selectedContent.title || "제목 없음"}
                          </h2>
                          <div className="flex items-center gap-3 mt-2 text-sm text-gray-500 dark:text-gray-400">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3.5 h-3.5" />
                              {new Date(selectedContent.created_at).toLocaleString("ko-KR")}
                            </span>
                            <span>{selectedContent.content.length.toLocaleString()}자</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-1.5 flex-shrink-0">
                          {editMode ? (
                            <>
                              <Button onClick={handleSave} variant="primary" className="text-sm">
                                저장
                              </Button>
                              <Button onClick={() => setEditMode(false)} variant="ghost" className="text-sm">
                                취소
                              </Button>
                            </>
                          ) : (
                            <>
                              <Button onClick={handleCopy} variant="outline" className="text-sm">
                                {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                              </Button>
                              <Button onClick={handleDownload} variant="outline" className="text-sm">
                                <Download className="w-4 h-4" />
                              </Button>
                              <Button onClick={handleEdit} variant="outline" className="text-sm">
                                <Pencil className="w-4 h-4" />
                              </Button>
                              <Button
                                onClick={() => handleDelete(selectedContent.id)}
                                variant="ghost"
                                className="text-sm text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Viewer Body */}
                    <div className="p-6">
                      {editMode ? (
                        <textarea
                          value={editedContent}
                          onChange={(e) => setEditedContent(e.target.value)}
                          className="w-full min-h-[500px] p-4 border border-gray-300 dark:border-gray-600 rounded-lg font-mono text-sm bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-y"
                        />
                      ) : (
                        <div
                          className="prose dark:prose-invert max-w-none text-gray-800 dark:text-gray-200 leading-relaxed"
                          dangerouslySetInnerHTML={{ __html: renderMarkdown(selectedContent.content) }}
                        />
                      )}
                    </div>
                  </motion.div>
                ) : (
                  <Card className="p-16 text-center">
                    <div className="max-w-sm mx-auto">
                      <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-4">
                        <FileText className="w-8 h-8 text-gray-300 dark:text-gray-600" />
                      </div>
                      <p className="text-gray-500 dark:text-gray-400 text-lg">콘텐츠를 선택하면 내용을 볼 수 있습니다</p>
                      <p className="text-gray-400 dark:text-gray-500 text-sm mt-1">왼쪽 목록에서 클릭하세요</p>
                    </div>
                  </Card>
                )}
              </div>
            </div>
          </>
        )}
      </motion.div>
    </div>
  );
}
