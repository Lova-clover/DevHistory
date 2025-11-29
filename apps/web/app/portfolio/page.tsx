"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Download, Share2, User, Code2, Award, BookOpen, Calendar, Github, Mail, Linkedin, ExternalLink } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs } from "@/components/ui/tabs";

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

export default function PortfolioPage() {
  const [activeTab, setActiveTab] = useState("overview");

  const tabs = [
    { id: "overview", label: "개요", icon: User },
    { id: "projects", label: "프로젝트", icon: Code2 },
    { id: "skills", label: "스킬", icon: Award },
    { id: "activity", label: "활동", icon: Calendar },
  ];

  const handleExport = () => {
    alert("포트폴리오를 PDF로 내보내는 기능은 곧 추가됩니다!");
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    alert("포트폴리오 링크가 클립보드에 복사되었습니다!");
  };

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
              내 포트폴리오
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              개발 활동을 기반으로 자동 생성된 포트폴리오
            </p>
          </div>
          <div className="flex gap-3">
            <Button onClick={handleShare} variant="ghost">
              <Share2 className="w-5 h-5 mr-2" />
              공유
            </Button>
            <Button onClick={handleExport}>
              <Download className="w-5 h-5 mr-2" />
              PDF 내보내기
            </Button>
          </div>
        </motion.div>

        {/* Profile Card */}
        <motion.div variants={itemVariants}>
          <Card className="p-8 bg-gradient-to-br from-primary-50 to-indigo-50 dark:from-primary-900/20 dark:to-indigo-900/20">
            <div className="flex items-start gap-8">
              {/* Avatar */}
              <div className="flex-shrink-0">
                <div className="w-32 h-32 bg-gradient-to-br from-primary-400 to-indigo-500 rounded-full flex items-center justify-center text-white text-5xl font-bold">
                  L
                </div>
              </div>

              {/* Profile Info */}
              <div className="flex-1">
                <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                  성주 (Lova-clover)
                </h2>
                <p className="text-lg text-gray-600 dark:text-gray-400 mb-4">
                  Full Stack Developer
                </p>
                <p className="text-gray-700 dark:text-gray-300 mb-6 max-w-2xl">
                  문제 해결과 효율적인 시스템 설계에 관심이 많은 개발자입니다. 
                  백엔드부터 프론트엔드까지 다양한 기술 스택을 활용하여 완성도 높은 서비스를 만듭니다.
                </p>

                {/* Social Links */}
                <div className="flex gap-4">
                  <motion.a
                    href="https://github.com/Lova-clover"
                    target="_blank"
                    rel="noopener noreferrer"
                    whileHover={{ scale: 1.1 }}
                    className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-all"
                  >
                    <Github className="w-5 h-5" />
                    <span>GitHub</span>
                  </motion.a>
                  <motion.a
                    href="mailto:your-email@example.com"
                    whileHover={{ scale: 1.1 }}
                    className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-all"
                  >
                    <Mail className="w-5 h-5" />
                    <span>Email</span>
                  </motion.a>
                </div>
              </div>

              {/* Stats */}
              <div className="flex-shrink-0 grid grid-cols-1 gap-4 text-center">
                <div className="bg-white dark:bg-gray-800 rounded-lg p-4 min-w-[120px]">
                  <p className="text-3xl font-bold text-primary-600 dark:text-primary-400">12</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">레포지토리</p>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                  <p className="text-3xl font-bold text-green-600 dark:text-green-400">234</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">문제 해결</p>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                  <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">1,289</p>
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
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">8</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">활성 프로젝트</p>
                    </div>
                    <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                      <Award className="w-8 h-8 mx-auto mb-2 text-green-600 dark:text-green-400" />
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">15</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">기술 스택</p>
                    </div>
                    <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                      <BookOpen className="w-8 h-8 mx-auto mb-2 text-purple-600 dark:text-purple-400" />
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">45</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">기술 블로그</p>
                    </div>
                    <div className="text-center p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                      <Calendar className="w-8 h-8 mx-auto mb-2 text-orange-600 dark:text-orange-400" />
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">365+</p>
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
              {[
                {
                  name: "FreshGuard",
                  description: "식품 유통기한 관리 및 알림 시스템",
                  tags: ["Python", "FastAPI", "PostgreSQL"],
                  stars: 12,
                  url: "https://github.com/Lova-clover/FreshGuard",
                },
                {
                  name: "DevHistory",
                  description: "개발 활동 자동 수집 및 포트폴리오 생성 플랫폼",
                  tags: ["TypeScript", "Next.js", "FastAPI"],
                  stars: 8,
                  url: "#",
                },
                {
                  name: "Path Planning",
                  description: "A* 알고리즘 기반 경로 탐색 시뮬레이터",
                  tags: ["Python", "Algorithm", "Visualization"],
                  stars: 5,
                  url: "#",
                },
                {
                  name: "AI Study Assistant",
                  description: "LLM 기반 학습 도우미 챗봇",
                  tags: ["Python", "OpenAI", "LangChain"],
                  stars: 15,
                  url: "#",
                },
              ].map((project, index) => (
                <motion.div key={index} variants={itemVariants} whileHover={{ scale: 1.02 }}>
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
                      {project.description}
                    </p>
                    <div className="flex flex-wrap gap-2 mb-4">
                      {project.tags.map((tag) => (
                        <Badge key={tag} variant="info" size="sm">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                    <a
                      href={project.url}
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
              {[
                {
                  category: "프론트엔드",
                  skills: [
                    { name: "React", level: 90 },
                    { name: "Next.js", level: 85 },
                    { name: "TypeScript", level: 88 },
                    { name: "Tailwind CSS", level: 92 },
                  ],
                },
                {
                  category: "백엔드",
                  skills: [
                    { name: "FastAPI", level: 90 },
                    { name: "Python", level: 95 },
                    { name: "PostgreSQL", level: 80 },
                    { name: "Redis", level: 75 },
                  ],
                },
                {
                  category: "DevOps",
                  skills: [
                    { name: "Docker", level: 85 },
                    { name: "GitHub Actions", level: 80 },
                    { name: "AWS", level: 70 },
                    { name: "Nginx", level: 75 },
                  ],
                },
              ].map((category, index) => (
                <motion.div key={index} variants={itemVariants}>
                  <Card className="p-6">
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                      {category.category}
                    </h3>
                    <div className="space-y-4">
                      {category.skills.map((skill) => (
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
                              transition={{ duration: 1, delay: index * 0.1 }}
                              className="bg-gradient-to-r from-primary-500 to-primary-600 h-2 rounded-full"
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                </motion.div>
              ))}
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
                    {[
                      { date: "2024-01-20", activity: "DevHistory 프로젝트 시작", type: "project" },
                      { date: "2024-01-18", activity: "알고리즘 문제 15개 해결", type: "problem" },
                      { date: "2024-01-15", activity: "Next.js 14 학습 블로그 작성", type: "blog" },
                      { date: "2024-01-12", activity: "FreshGuard v2.0 릴리즈", type: "release" },
                      { date: "2024-01-10", activity: "FastAPI 성능 최적화 완료", type: "commit" },
                    ].map((item, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="flex items-center gap-4 p-4 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                      >
                        <div
                          className={`w-3 h-3 rounded-full ${
                            item.type === "project"
                              ? "bg-blue-500"
                              : item.type === "problem"
                              ? "bg-green-500"
                              : item.type === "blog"
                              ? "bg-purple-500"
                              : item.type === "release"
                              ? "bg-orange-500"
                              : "bg-gray-500"
                          }`}
                        />
                        <div className="flex-1">
                          <p className="font-medium text-gray-900 dark:text-white">
                            {item.activity}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {item.date}
                          </p>
                        </div>
                        <Badge
                          variant={
                            item.type === "project" || item.type === "release"
                              ? "success"
                              : "info"
                          }
                          size="sm"
                        >
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
    </div>
  );
}
            <div className="flex gap-2">
              <span className="text-sm bg-yellow-100 text-yellow-800 px-2 py-1 rounded">JavaScript</span>
              <span className="text-sm bg-red-100 text-red-800 px-2 py-1 rounded">Canvas</span>
            </div>
          </div>
        </div>
      </div>

      {/* Skills & Stats */}
      <div className="bg-white p-8 rounded-lg shadow">
        <h2 className="text-2xl font-bold mb-6">기술 스택</h2>
        <div className="flex flex-wrap gap-3">
          <span className="px-4 py-2 bg-gray-100 rounded-full">Python</span>
          <span className="px-4 py-2 bg-gray-100 rounded-full">TypeScript</span>
          <span className="px-4 py-2 bg-gray-100 rounded-full">React</span>
          <span className="px-4 py-2 bg-gray-100 rounded-full">FastAPI</span>
          <span className="px-4 py-2 bg-gray-100 rounded-full">PostgreSQL</span>
          <span className="px-4 py-2 bg-gray-100 rounded-full">Docker</span>
        </div>
      </div>

      {/* Public Link */}
      <div className="mt-8 text-center">
        <button className="border border-primary-600 text-primary-600 px-6 py-3 rounded-lg hover:bg-primary-50">
          공개 링크 생성
        </button>
      </div>
    </div>
  );
}
