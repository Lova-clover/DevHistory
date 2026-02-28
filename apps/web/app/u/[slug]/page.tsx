"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import { User, Code2, Award, BookOpen, Github, Mail, Star, GitFork, ExternalLink } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface PublicPortfolio {
  user: {
    name: string;
    email: string | null;
    bio: string | null;
    avatar_url: string | null;
    github_username: string | null;
  };
  stats: {
    total_repos: number;
    total_commits: number;
    total_problems: number;
    total_blogs: number;
    total_stars: number;
  };
  languages: Array<{ name: string; count: number }>;
  top_repos: Array<{
    name: string;
    full_name: string;
    description: string | null;
    language: string | null;
    stars: number;
    forks: number;
    html_url: string;
  }>;
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

const LANG_COLORS: Record<string, string> = {
  TypeScript: "#3178c6",
  JavaScript: "#f1e05a",
  Python: "#3572A5",
  Java: "#b07219",
  Go: "#00ADD8",
  Rust: "#dea584",
  C: "#555555",
  "C++": "#f34b7d",
  "C#": "#178600",
  Ruby: "#701516",
  Swift: "#F05138",
  Kotlin: "#A97BFF",
};

export default function PublicPortfolioPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [data, setData] = useState<PublicPortfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    fetch(`/api/public/portfolio/${encodeURIComponent(slug)}`)
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail || "Portfolio not found");
        }
        return res.json();
      })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <Card className="p-8 text-center max-w-md">
          <h2 className="text-xl font-semibold mb-2 dark:text-white">포트폴리오를 찾을 수 없습니다</h2>
          <p className="text-gray-500 dark:text-gray-400">{error || "존재하지 않는 페이지입니다."}</p>
        </Card>
      </div>
    );
  }

  const maxLang = Math.max(...data.languages.map((l) => l.count), 1);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4">
      <motion.div
        className="max-w-4xl mx-auto space-y-8"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Header */}
        <motion.div variants={itemVariants}>
          <Card className="p-8">
            <div className="flex items-center gap-6">
              {data.user.avatar_url && (
                <img
                  src={data.user.avatar_url}
                  alt={data.user.name}
                  className="w-20 h-20 rounded-full border-2 border-gray-200 dark:border-gray-700"
                />
              )}
              <div>
                <h1 className="text-2xl font-bold dark:text-white">{data.user.name}</h1>
                {data.user.bio && (
                  <p className="text-gray-600 dark:text-gray-400 mt-1">{data.user.bio}</p>
                )}
                <div className="flex items-center gap-4 mt-2 text-sm text-gray-500 dark:text-gray-400">
                  {data.user.github_username && (
                    <a
                      href={`https://github.com/${data.user.github_username}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 hover:text-blue-500 transition-colors"
                    >
                      <Github className="w-4 h-4" /> {data.user.github_username}
                    </a>
                  )}
                  {data.user.email && (
                    <a
                      href={`mailto:${data.user.email}`}
                      className="flex items-center gap-1 hover:text-blue-500 transition-colors"
                    >
                      <Mail className="w-4 h-4" /> {data.user.email}
                    </a>
                  )}
                </div>
              </div>
            </div>
          </Card>
        </motion.div>

        {/* Stats */}
        <motion.div variants={itemVariants}>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[
              { label: "리포지토리", value: data.stats.total_repos, icon: Code2 },
              { label: "커밋", value: data.stats.total_commits, icon: User },
              { label: "스타", value: data.stats.total_stars, icon: Star },
              { label: "문제풀이", value: data.stats.total_problems, icon: Award },
              { label: "블로그", value: data.stats.total_blogs, icon: BookOpen },
            ].map((s) => (
              <Card key={s.label} className="p-4 text-center">
                <s.icon className="w-5 h-5 mx-auto mb-2 text-blue-500" />
                <div className="text-2xl font-bold dark:text-white">{s.value.toLocaleString()}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">{s.label}</div>
              </Card>
            ))}
          </div>
        </motion.div>

        {/* Languages */}
        {data.languages.length > 0 && (
          <motion.div variants={itemVariants}>
            <Card className="p-6">
              <h2 className="text-lg font-semibold mb-4 dark:text-white">사용 언어</h2>
              <div className="space-y-3">
                {data.languages.map((lang) => (
                  <div key={lang.name} className="flex items-center gap-3">
                    <span className="w-24 text-sm text-gray-700 dark:text-gray-300 truncate">
                      {lang.name}
                    </span>
                    <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${(lang.count / maxLang) * 100}%`,
                          backgroundColor: LANG_COLORS[lang.name] || "#6366f1",
                        }}
                      />
                    </div>
                    <span className="text-xs text-gray-500 w-8 text-right">{lang.count}</span>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>
        )}

        {/* Top Repos */}
        {data.top_repos.length > 0 && (
          <motion.div variants={itemVariants}>
            <Card className="p-6">
              <h2 className="text-lg font-semibold mb-4 dark:text-white">주요 프로젝트</h2>
              <div className="grid md:grid-cols-2 gap-4">
                {data.top_repos.map((repo) => (
                  <a
                    key={repo.full_name}
                    href={repo.html_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-400 transition-colors"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <Code2 className="w-4 h-4 text-blue-500" />
                      <span className="font-medium dark:text-white">{repo.name}</span>
                      <ExternalLink className="w-3 h-3 text-gray-400 ml-auto" />
                    </div>
                    {repo.description && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 line-clamp-2">
                        {repo.description}
                      </p>
                    )}
                    <div className="flex items-center gap-3 text-xs text-gray-500">
                      {repo.language && (
                        <Badge variant="default" className="text-xs">
                          {repo.language}
                        </Badge>
                      )}
                      <span className="flex items-center gap-1">
                        <Star className="w-3 h-3" /> {repo.stars}
                      </span>
                      <span className="flex items-center gap-1">
                        <GitFork className="w-3 h-3" /> {repo.forks}
                      </span>
                    </div>
                  </a>
                ))}
              </div>
            </Card>
          </motion.div>
        )}

        {/* Footer */}
        <motion.div variants={itemVariants}>
          <p className="text-center text-xs text-gray-400 dark:text-gray-600">
            Powered by DevHistory
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
}
