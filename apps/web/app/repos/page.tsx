"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Search, RefreshCw, GitFork, Star, Eye, Code2, Calendar } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { Loading } from "@/components/ui/loading";
import { fetchWithAuth } from "@/lib/api";
import { format } from "date-fns";
import { ko } from "date-fns/locale";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.3,
    },
  },
};

const languageColors: Record<string, string> = {
  JavaScript: "bg-yellow-500",
  TypeScript: "bg-blue-500",
  Python: "bg-blue-600",
  Java: "bg-red-500",
  "C++": "bg-pink-500",
  Go: "bg-cyan-500",
  Rust: "bg-orange-500",
  Ruby: "bg-red-600",
  PHP: "bg-purple-500",
};

export default function ReposPage() {
  const [repos, setRepos] = useState<any[]>([]);
  const [filteredRepos, setFilteredRepos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("all");

  useEffect(() => {
    fetchRepos();
  }, []);

  useEffect(() => {
    filterRepos();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery, selectedLanguage, repos]);

  const fetchRepos = async () => {
    try {
      const res = await fetchWithAuth("/api/repos");
      const data = await res.json();
      // Ensure data is an array
      const reposArray = Array.isArray(data) ? data : [];
      setRepos(reposArray);
      setFilteredRepos(reposArray);
    } catch (error) {
      console.error("Failed to fetch repos:", error);
      setRepos([]);
      setFilteredRepos([]);
    } finally {
      setLoading(false);
    }
  };

  const triggerSync = async () => {
    setSyncing(true);
    try {
      await fetchWithAuth("/api/collector/trigger/github", { method: "POST" });
      alert("GitHub 동기화를 시작했습니다");
      fetchRepos();
    } catch (error) {
      alert("동기화 실행에 실패했습니다");
    } finally {
      setSyncing(false);
    }
  };

  const filterRepos = () => {
    let filtered = repos;

    if (searchQuery) {
      filtered = filtered.filter(
        (repo) =>
          repo.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          repo.description?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    if (selectedLanguage !== "all") {
      filtered = filtered.filter((repo) => repo.language === selectedLanguage);
    }

    setFilteredRepos(filtered);
  };

  const getUniqueLanguages = () => {
    const languages = repos
      .map((repo) => repo.language)
      .filter((lang) => lang);
    return ["all", ...Array.from(new Set(languages))];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loading size="lg" />
      </div>
    );
  }

  const languages = getUniqueLanguages();

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.div
        initial="hidden"
        animate="visible"
        variants={containerVariants}
        className="space-y-8"
      >
        {/* Header */}
        <motion.div variants={itemVariants} className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
              레포지토리
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              {repos.length}개의 레포지토리를 관리하고 있습니다
            </p>
          </div>
          <Button onClick={triggerSync} disabled={syncing} size="lg">
            <RefreshCw className={`w-5 h-5 mr-2 ${syncing ? "animate-spin" : ""}`} />
            {syncing ? "동기화 중..." : "동기화"}
          </Button>
        </motion.div>

        {repos.length === 0 ? (
          <EmptyState
            title="레포지토리가 없습니다"
            description="GitHub에서 레포지토리를 동기화해보세요"
            action={{
              label: "지금 동기화",
              onClick: triggerSync
            }}
          />
        ) : (
          <>
            {/* Search and Filter */}
            <motion.div variants={itemVariants} className="space-y-4">
              {/* Search Bar */}
              <div className="relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="레포지토리 이름이나 설명으로 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-800 dark:text-white"
                />
              </div>

              {/* Language Filter */}
              <div className="flex items-center gap-3 flex-wrap">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  언어:
                </span>
                {languages.map((lang) => (
                  <button
                    key={lang}
                    onClick={() => setSelectedLanguage(lang)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      selectedLanguage === lang
                        ? "bg-primary-600 text-white shadow-lg scale-105"
                        : "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
                    }`}
                  >
                    {lang === "all" ? "전체" : lang}
                  </button>
                ))}
              </div>
            </motion.div>

            {/* Stats */}
            <motion.div
              variants={itemVariants}
              className="grid grid-cols-1 md:grid-cols-4 gap-4"
            >
              <Card className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20">
                <div className="flex items-center gap-3">
                  <Code2 className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">총 레포</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {repos.length}
                    </p>
                  </div>
                </div>
              </Card>

              <Card className="p-4 bg-gradient-to-br from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20">
                <div className="flex items-center gap-3">
                  <Star className="w-8 h-8 text-yellow-600 dark:text-yellow-400" />
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">총 스타</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {repos.reduce((acc, repo) => acc + (repo.stars || 0), 0)}
                    </p>
                  </div>
                </div>
              </Card>

              <Card className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20">
                <div className="flex items-center gap-3">
                  <GitFork className="w-8 h-8 text-green-600 dark:text-green-400" />
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">총 포크</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {repos.reduce((acc, repo) => acc + (repo.forks || 0), 0)}
                    </p>
                  </div>
                </div>
              </Card>

              <Card className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20">
                <div className="flex items-center gap-3">
                  <Eye className="w-8 h-8 text-purple-600 dark:text-purple-400" />
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">총 조회</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {repos.reduce((acc, repo) => acc + (repo.watchers || 0), 0)}
                    </p>
                  </div>
                </div>
              </Card>
            </motion.div>

            {/* Repos Grid */}
            {filteredRepos.length === 0 ? (
              <EmptyState
                title="검색 결과가 없습니다"
                description="다른 검색어나 필터를 시도해보세요"
              />
            ) : (
              <motion.div
                variants={containerVariants}
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
              >
                {filteredRepos.map((repo) => (
                  <motion.div
                    key={repo.id}
                    variants={itemVariants}
                    whileHover={{ scale: 1.02, y: -4 }}
                  >
                    <a href={`/repos/${repo.id}`}>
                      <Card className="p-6 h-full hover:shadow-xl transition-all duration-300 cursor-pointer">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center gap-2">
                            <Code2 className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                              {repo.name}
                            </h3>
                          </div>
                          {repo.language && (
                            <Badge variant="info" size="sm">
                              {repo.language}
                            </Badge>
                          )}
                        </div>

                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
                          {repo.description || "설명이 없습니다"}
                        </p>

                        <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400 mb-4">
                          <div className="flex items-center gap-1">
                            <Star className="w-4 h-4" />
                            {repo.stars || 0}
                          </div>
                          <div className="flex items-center gap-1">
                            <GitFork className="w-4 h-4" />
                            {repo.forks || 0}
                          </div>
                          <div className="flex items-center gap-1">
                            <Eye className="w-4 h-4" />
                            {repo.watchers || 0}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                          <Calendar className="w-3 h-3" />
                          {repo.last_commit_at
                            ? format(new Date(repo.last_commit_at), "yyyy-MM-dd", {
                                locale: ko,
                              })
                            : "N/A"}
                        </div>
                      </Card>
                    </a>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </>
        )}
      </motion.div>
    </div>
  );
}
