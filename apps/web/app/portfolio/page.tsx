"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Download, Share2, User, Code2, Award, BookOpen, Calendar, Github, Mail, ExternalLink, Globe, Link2, Copy, Check, X, RefreshCw, Eye, EyeOff } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs } from "@/components/ui/tabs";
import { fetchWithAuth } from "@/lib/api";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
    },
  },
};

interface PortfolioData {
  user: {
    id: string;
    name: string;
    email: string;
    bio: string | null;
    avatar_url: string;
    github_username: string;
  };
  stats: {
    total_repos: number;
    total_commits: number;
    total_problems: number;
    total_blogs: number;
    total_stars: number;
    activity_days: number;
    recent_commits: number;
  };
  languages: Array<{ name: string; count: number }>;
  top_repos: Array<{
    id: string;
    name: string;
    full_name: string;
    description: string;
    language: string;
    stars: number;
    forks: number;
    html_url: string;
  }>;
  recent_activity: Array<{
    id: string;
    type: string;
    date: string;
    message: string;
    repo_name: string;
  }>;
}

export default function PortfolioPage() {
  const [activeTab, setActiveTab] = useState("overview");
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const portfolioRef = useRef<HTMLDivElement>(null);
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareSettings, setShareSettings] = useState<{
    portfolio_public: boolean;
    public_slug: string | null;
    portfolio_show_email: boolean;
    share_token: string | null;
    share_token_expires_at: string | null;
    public_url: string | null;
    share_url: string | null;
  } | null>(null);
  const [shareLoading, setShareLoading] = useState(false);
  const [slugInput, setSlugInput] = useState("");
  const [copied, setCopied] = useState<"public" | "private" | null>(null);

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const fetchPortfolio = async () => {
    try {
      const res = await fetchWithAuth("/api/me/portfolio");
      const data = await res.json();
      setPortfolio(data);
    } catch (error) {
      console.error("Failed to fetch portfolio:", error);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: "overview", label: "개요", icon: User },
    { id: "projects", label: "프로젝트", icon: Code2 },
    { id: "skills", label: "스킬", icon: Award },
    { id: "activity", label: "활동", icon: Calendar },
  ];

  const handleExport = async () => {
    if (!portfolioRef.current || exporting) return;

    try {
      setExporting(true);
      
      // Save current tab
      const originalTab = activeTab;
      
      // Hide buttons and tabs during export
      const buttons = portfolioRef.current.querySelectorAll('.export-hide');
      buttons.forEach(btn => (btn as HTMLElement).style.display = 'none');

      // Wait for initial render
      await new Promise(resolve => setTimeout(resolve, 800));

      // Create PDF
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
      });

      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();

      // Capture each tab: overview, projects, skills
      const tabsToCapture = ['overview', 'projects', 'skills'];
      
      for (let i = 0; i < tabsToCapture.length; i++) {
        const tabId = tabsToCapture[i];
        
        // Switch to the tab
        setActiveTab(tabId);
        
        // Wait for render and animations to complete
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Capture the portfolio content
        const canvas = await html2canvas(portfolioRef.current, {
          scale: 2,
          useCORS: true,
          logging: false,
          backgroundColor: '#ffffff',
          windowWidth: portfolioRef.current.scrollWidth,
          windowHeight: portfolioRef.current.scrollHeight,
        });

        const imgData = canvas.toDataURL('image/png');
        const imgWidth = canvas.width;
        const imgHeight = canvas.height;
        
        // Calculate dimensions to fit on page width
        const ratio = pdfWidth / imgWidth;
        const scaledHeight = imgHeight * ratio;
        
        // Add new page if not the first tab
        if (i > 0) {
          pdf.addPage();
        }
        
        // Split content across multiple pages if needed
        let position = 0;
        const pageHeight = pdfHeight;
        
        while (position < scaledHeight) {
          if (position > 0) {
            pdf.addPage();
          }
          
          // Calculate the portion of the image for this page
          const sourceY = position / ratio;
          const sourceHeight = Math.min(pageHeight / ratio, imgHeight - sourceY);
          
          // Create a canvas for this page's content
          const pageCanvas = document.createElement('canvas');
          pageCanvas.width = imgWidth;
          pageCanvas.height = sourceHeight;
          
          const ctx = pageCanvas.getContext('2d');
          if (ctx) {
            ctx.drawImage(
              canvas,
              0, sourceY,
              imgWidth, sourceHeight,
              0, 0,
              imgWidth, sourceHeight
            );
            
            const pageImgData = pageCanvas.toDataURL('image/png');
            const pageScaledHeight = sourceHeight * ratio;
            pdf.addImage(pageImgData, 'PNG', 0, 0, pdfWidth, pageScaledHeight);
          }
          
          position += pageHeight;
        }
      }

      // Restore buttons and original tab
      buttons.forEach(btn => (btn as HTMLElement).style.display = '');
      setActiveTab(originalTab);
      
      // Download PDF
      const fileName = `${portfolio?.user.name || 'portfolio'}_${new Date().toISOString().split('T')[0]}.pdf`;
      pdf.save(fileName);

    } catch (error) {
      console.error('PDF 생성 실패:', error);
      alert('PDF 생성에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setExporting(false);
    }
  };

  const handleShare = async () => {
    setShowShareModal(true);
    if (!shareSettings) {
      setShareLoading(true);
      try {
        const res = await fetchWithAuth("/api/me/share-settings");
        const data = await res.json();
        setShareSettings(data);
        setSlugInput(data.public_slug || "");
      } catch (e) {
        console.error("Failed to load share settings:", e);
      } finally {
        setShareLoading(false);
      }
    }
  };

  const updateShareSettings = async (updates: Record<string, unknown>) => {
    setShareLoading(true);
    try {
      const res = await fetchWithAuth("/api/me/share-settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      });
      const data = await res.json();
      setShareSettings(data);
    } catch (e) {
      console.error("Failed to update share settings:", e);
    } finally {
      setShareLoading(false);
    }
  };

  const rotateToken = async () => {
    setShareLoading(true);
    try {
      const res = await fetchWithAuth("/api/me/share/rotate", { method: "POST" });
      const data = await res.json();
      setShareSettings(data);
    } catch (e) {
      console.error("Failed to rotate token:", e);
    } finally {
      setShareLoading(false);
    }
  };

  const copyUrl = (type: "public" | "private") => {
    const url = type === "public" ? shareSettings?.public_url : shareSettings?.share_url;
    if (!url) return;
    navigator.clipboard.writeText(`${window.location.origin}${url}`);
    setCopied(type);
    setTimeout(() => setCopied(null), 2000);
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">포트폴리오를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="p-8 text-center">
          <p className="text-gray-600 dark:text-gray-400">포트폴리오 데이터를 불러올 수 없습니다.</p>
        </Card>
      </div>
    );
  }

  // Calculate language percentages
  const totalLanguageCount = portfolio.languages.reduce((sum, lang) => sum + lang.count, 0);
  const languageSkills = portfolio.languages.map(lang => ({
    name: lang.name,
    level: totalLanguageCount > 0 ? Math.round((lang.count / totalLanguageCount) * 100) : 0
  }));

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.div
        ref={portfolioRef}
        initial="hidden"
        animate="visible"
        variants={containerVariants}
        className="space-y-8"
      >
        {/* Header */}
        <motion.div variants={itemVariants} className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
              내 포트폴리오
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              개발 활동을 기반으로 자동 생성된 포트폴리오
            </p>
          </div>
          <div className="flex gap-3 export-hide">
            <Button onClick={handleShare} variant="ghost">
              <Share2 className="w-5 h-5 mr-2" />
              공유
            </Button>
            <Button onClick={handleExport} disabled={exporting}>
              <Download className="w-5 h-5 mr-2" />
              {exporting ? 'PDF 생성 중...' : 'PDF 내보내기'}
            </Button>
          </div>
        </motion.div>

        {/* Profile Card */}
        <motion.div variants={itemVariants}>
          <Card className="p-8 bg-gradient-to-br from-primary-50 to-indigo-50 dark:from-primary-900/20 dark:to-indigo-900/20">
            <div className="flex items-start gap-8">
              {/* Avatar */}
              <div className="flex-shrink-0">
                {portfolio.user.avatar_url ? (
                  <img
                    src={portfolio.user.avatar_url}
                    alt={portfolio.user.name}
                    className="w-32 h-32 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-32 h-32 bg-gradient-to-br from-primary-400 to-indigo-500 rounded-full flex items-center justify-center text-white text-5xl font-bold">
                    {portfolio.user.name?.charAt(0).toUpperCase() || "U"}
                  </div>
                )}
              </div>

              {/* Profile Info */}
              <div className="flex-1">
                <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                  {portfolio.user.name || "Unknown User"}
                  {portfolio.user.github_username && (
                    <span className="text-xl text-gray-600 dark:text-gray-400 ml-2">
                      ({portfolio.user.github_username})
                    </span>
                  )}
                </h2>
                <p className="text-lg text-gray-600 dark:text-gray-400 mb-4">
                  Full Stack Developer
                </p>
                <p className="text-gray-700 dark:text-gray-300 mb-6 max-w-2xl">
                  {portfolio.user.bio || `${portfolio.stats.total_repos}개의 레포지토리와 ${portfolio.stats.total_commits}개의 커밋으로
                  활발히 개발하고 있습니다.`}
                </p>

                {/* Social Links */}
                <div className="flex gap-4">
                  {portfolio.user.github_username && (
                    <motion.a
                      href={`https://github.com/${portfolio.user.github_username}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      whileHover={{ scale: 1.1 }}
                      className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-all text-gray-900 dark:text-white"
                    >
                      <Github className="w-5 h-5" />
                      <span>GitHub</span>
                    </motion.a>
                  )}
                  <motion.a
                    href={`mailto:${portfolio.user.email}`}
                    whileHover={{ scale: 1.1 }}
                    className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-all text-gray-900 dark:text-white"
                  >
                    <Mail className="w-5 h-5" />
                    <span>Email</span>
                  </motion.a>
                </div>
              </div>

              {/* Stats */}
              <div className="flex-shrink-0 grid grid-cols-1 gap-4 text-center">
                <div className="bg-white dark:bg-gray-800 rounded-lg p-4 min-w-[120px]">
                  <p className="text-3xl font-bold text-primary-600 dark:text-primary-400">
                    {portfolio.stats.total_repos}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">레포지토리</p>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                  <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                    {portfolio.stats.total_problems}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">문제 해결</p>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                  <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                    {portfolio.stats.total_commits}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">총 커밋</p>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>

        {/* Tabs */}
        <motion.div variants={itemVariants}>
          <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
        </motion.div>

        {/* Tab Content */}
        <motion.div variants={containerVariants}>
          {/* Overview Tab */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              <motion.div variants={itemVariants}>
                <Card className="p-6">
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                    요약
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <Code2 className="w-8 h-8 mx-auto mb-2 text-blue-600 dark:text-blue-400" />
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        {portfolio.stats.total_repos}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">활성 프로젝트</p>
                    </div>
                    <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                      <Award className="w-8 h-8 mx-auto mb-2 text-green-600 dark:text-green-400" />
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        {portfolio.languages.length}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">기술 스택</p>
                    </div>
                    <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                      <BookOpen className="w-8 h-8 mx-auto mb-2 text-purple-600 dark:text-purple-400" />
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        {portfolio.stats.total_blogs}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">기술 블로그</p>
                    </div>
                    <div className="text-center p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                      <Calendar className="w-8 h-8 mx-auto mb-2 text-orange-600 dark:text-orange-400" />
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        {portfolio.stats.activity_days}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">활동 일수</p>
                    </div>
                  </div>
                </Card>
              </motion.div>
            </div>
          )}

          {/* Projects Tab */}
          {activeTab === "projects" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {portfolio.top_repos.map((project, index) => (
                <motion.div key={project.id} variants={itemVariants} whileHover={{ scale: 1.02 }}>
                  <Card className="p-6 h-full hover:shadow-xl transition-all duration-300">
                    <div className="flex items-start justify-between mb-4">
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                        {project.name}
                      </h3>
                      <div className="flex items-center gap-1 text-yellow-500">
                        <Award className="w-4 h-4" />
                        <span className="text-sm">{project.stars}</span>
                      </div>
                    </div>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      {project.description || "설명 없음"}
                    </p>
                    <div className="flex flex-wrap gap-2 mb-4">
                      {project.language && (
                        <Badge variant="info" size="sm">
                          {project.language}
                        </Badge>
                      )}
                      {project.forks > 0 && (
                        <Badge variant="default" size="sm">
                          {project.forks} forks
                        </Badge>
                      )}
                    </div>
                    <a
                      href={project.html_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-primary-600 dark:text-primary-400 hover:underline"
                    >
                      자세히 보기
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}

          {/* Skills Tab */}
          {activeTab === "skills" && (
            <div className="space-y-6">
              <motion.div variants={itemVariants}>
                <Card className="p-6">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                    프로그래밍 언어 (커밋 기준)
                  </h3>
                  <div className="space-y-4">
                    {languageSkills.slice(0, 10).map((skill) => (
                      <div key={skill.name}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            {skill.name}
                          </span>
                          <span className="text-sm text-gray-500 dark:text-gray-400">
                            {skill.level}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${skill.level}%` }}
                            transition={{ duration: 1, delay: 0.1 }}
                            className="bg-gradient-to-r from-primary-500 to-primary-600 h-2 rounded-full"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              </motion.div>
            </div>
          )}

          {/* Activity Tab */}
          {activeTab === "activity" && (
            <div className="space-y-6">
              <motion.div variants={itemVariants}>
                <Card className="p-6">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
                    최근 활동
                  </h3>
                  <div className="space-y-4">
                    {portfolio.recent_activity.map((item, index) => (
                      <motion.div
                        key={item.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="flex items-center gap-4 p-4 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                      >
                        <div className="w-3 h-3 rounded-full bg-blue-500" />
                        <div className="flex-1">
                          <p className="font-medium text-gray-900 dark:text-white">
                            {item.message}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {item.repo_name} · {new Date(item.date).toLocaleDateString("ko-KR")}
                          </p>
                        </div>
                        <Badge variant="info" size="sm">
                          {item.type}
                        </Badge>
                      </motion.div>
                    ))}
                  </div>
                </Card>
              </motion.div>
            </div>
          )}
        </motion.div>
      </motion.div>

      {/* Share Modal */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowShareModal(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl max-w-lg w-full p-6 space-y-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold dark:text-white flex items-center gap-2">
                <Share2 className="w-5 h-5" /> 포트폴리오 공유
              </h2>
              <button onClick={() => setShowShareModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            {shareLoading && !shareSettings ? (
              <div className="py-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto" />
              </div>
            ) : shareSettings ? (
              <div className="space-y-5">
                {/* Public Portfolio */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Globe className="w-4 h-4 text-green-500" />
                      <span className="font-medium dark:text-white">공개 포트폴리오</span>
                    </div>
                    <button
                      onClick={() => updateShareSettings({ portfolio_public: !shareSettings.portfolio_public })}
                      disabled={shareLoading}
                      className={`relative w-11 h-6 rounded-full transition-colors ${
                        shareSettings.portfolio_public ? "bg-green-500" : "bg-gray-300 dark:bg-gray-600"
                      }`}
                    >
                      <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                        shareSettings.portfolio_public ? "translate-x-5" : ""
                      }`} />
                    </button>
                  </div>

                  {shareSettings.portfolio_public && (
                    <div className="space-y-2 pl-6">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-500 dark:text-gray-400 whitespace-nowrap">/u/</span>
                        <input
                          type="text"
                          value={slugInput}
                          onChange={(e) => setSlugInput(e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, ""))}
                          placeholder="my-portfolio"
                          className="flex-1 text-sm border rounded-lg px-3 py-1.5 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                        />
                        <Button
                          size="sm"
                          onClick={() => updateShareSettings({ public_slug: slugInput })}
                          disabled={shareLoading || slugInput.length < 3}
                        >
                          저장
                        </Button>
                      </div>
                      {shareSettings.public_url && (
                        <div className="flex items-center gap-2">
                          <code className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded flex-1 truncate dark:text-gray-300">
                            {window.location.origin}{shareSettings.public_url}
                          </code>
                          <button onClick={() => copyUrl("public")} className="text-gray-400 hover:text-blue-500">
                            {copied === "public" ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                          </button>
                        </div>
                      )}
                      <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <input
                          type="checkbox"
                          checked={shareSettings.portfolio_show_email}
                          onChange={(e) => updateShareSettings({ portfolio_show_email: e.target.checked })}
                          className="rounded"
                        />
                        이메일 공개
                      </label>
                    </div>
                  )}
                </div>

                <hr className="dark:border-gray-700" />

                {/* Private Share Link */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Link2 className="w-4 h-4 text-blue-500" />
                    <span className="font-medium dark:text-white">비공개 공유 링크</span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 pl-6">
                    링크를 아는 사람만 접근할 수 있습니다. 검색엔진에 노출되지 않습니다.
                  </p>
                  {shareSettings.share_url ? (
                    <div className="space-y-2 pl-6">
                      <div className="flex items-center gap-2">
                        <code className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded flex-1 truncate dark:text-gray-300">
                          {window.location.origin}{shareSettings.share_url}
                        </code>
                        <button onClick={() => copyUrl("private")} className="text-gray-400 hover:text-blue-500">
                          {copied === "private" ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                        </button>
                      </div>
                      {shareSettings.share_token_expires_at && (
                        <p className="text-xs text-amber-600 dark:text-amber-400">
                          만료: {new Date(shareSettings.share_token_expires_at).toLocaleDateString("ko-KR")}
                        </p>
                      )}
                      <button
                        onClick={rotateToken}
                        disabled={shareLoading}
                        className="flex items-center gap-1 text-xs text-blue-500 hover:text-blue-600"
                      >
                        <RefreshCw className="w-3 h-3" /> 새 링크 생성
                      </button>
                    </div>
                  ) : (
                    <div className="pl-6">
                      <Button size="sm" variant="secondary" onClick={rotateToken} disabled={shareLoading}>
                        <Link2 className="w-4 h-4 mr-1" /> 공유 링크 생성
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
