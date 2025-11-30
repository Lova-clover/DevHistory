"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { RefreshCw, Github, CheckCircle, XCircle, Clock } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { fetchWithAuth } from "@/lib/api";

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

interface SyncStatus {
  source: string;
  status: string;
  last_synced_at: string | null;
  items_synced: number;
}

interface UserProfile {
  solvedac_handle: string | null;
  velog_id: string | null;
  portfolio_email: string | null;
  portfolio_name: string | null;
  portfolio_bio: string | null;
  max_portfolio_repos: number;
}

export default function SettingsPage() {
  const [syncStatuses, setSyncStatuses] = useState<SyncStatus[]>([]);
  const [syncing, setSyncing] = useState<{ [key: string]: boolean }>({});
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<UserProfile>({
    solvedac_handle: null,
    velog_id: null,
    portfolio_email: null,
    portfolio_name: null,
    portfolio_bio: null,
    max_portfolio_repos: 6
  });
  const [editingProfile, setEditingProfile] = useState(false);
  const [tempProfile, setTempProfile] = useState<UserProfile>({
    solvedac_handle: null,
    velog_id: null,
    portfolio_email: null,
    portfolio_name: null,
    portfolio_bio: null,
    max_portfolio_repos: 6
  });

  useEffect(() => {
    fetchSyncStatus();
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await fetchWithAuth("/api/profile/user");
      const data = await res.json();
      setProfile(data);
      setTempProfile(data);
    } catch (error) {
      console.error("Failed to fetch profile:", error);
    }
  };

  const fetchSyncStatus = async () => {
    try {
      const res = await fetchWithAuth("/api/collector/status");
      const data = await res.json();
      setSyncStatuses(data);
    } catch (error) {
      console.error("Failed to fetch sync status:", error);
    } finally {
      setLoading(false);
    }
  };

  const triggerSync = async (source: string) => {
    setSyncing((prev) => ({ ...prev, [source]: true }));
    try {
      await fetchWithAuth("/api/collector/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source, force_full_sync: false }),
      });
      alert(`${getSourceName(source)} 동기화를 시작했습니다`);
      // Wait a bit then refresh status
      setTimeout(fetchSyncStatus, 2000);
    } catch (error) {
      console.error(`Failed to sync ${source}:`, error);
      alert(`${getSourceName(source)} 동기화 실행에 실패했습니다`);
    } finally {
      setSyncing((prev) => ({ ...prev, [source]: false }));
    }
  };

  const saveProfile = async () => {
    try {
      await fetchWithAuth("/api/profile/user", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(tempProfile),
      });
      setProfile(tempProfile);
      setEditingProfile(false);
      alert("프로필이 저장되었습니다. 이제 동기화를 실행하세요.");
      fetchSyncStatus();
    } catch (error) {
      console.error("Failed to save profile:", error);
      alert("프로필 저장에 실패했습니다");
    }
  };

  const getSourceName = (source: string) => {
    const names: { [key: string]: string } = {
      github: "GitHub",
      solvedac: "Solved.ac",
      velog: "Velog",
    };
    return names[source] || source;
  };

  const getSourceIcon = (source: string) => {
    switch (source) {
      case "github":
        return <Github className="w-6 h-6" />;
      case "solvedac":
        return (
          <div className="w-6 h-6 flex items-center justify-center text-lg font-bold">
            🏆
          </div>
        );
      case "velog":
        return (
          <div className="w-6 h-6 flex items-center justify-center text-lg font-bold">
            📝
          </div>
        );
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
            <CheckCircle className="w-5 h-5" />
            <span>연결됨</span>
          </div>
        );
      case "pending":
        return (
          <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
            <Clock className="w-5 h-5" />
            <span>대기 중</span>
          </div>
        );
      case "failed":
        return (
          <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
            <XCircle className="w-5 h-5" />
            <span>실패</span>
          </div>
        );
      default:
        return null;
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "없음";
    return new Date(dateString).toLocaleString("ko-KR");
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">설정을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.div
        initial="hidden"
        animate="visible"
        variants={containerVariants}
        className="space-y-8"
      >
        {/* Header */}
        <motion.div variants={itemVariants}>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            설정
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            데이터 수집 연동 및 동기화 관리
          </p>
        </motion.div>

        {/* Sync Status Cards */}
        <motion.div variants={itemVariants} className="space-y-4">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            계정 연동 설정
          </h2>

          {/* Profile Settings Card */}
          <Card className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  연동 계정 정보
                </h3>
                {!editingProfile ? (
                  <Button onClick={() => setEditingProfile(true)} variant="outline">
                    수정
                  </Button>
                ) : (
                  <div className="flex gap-2">
                    <Button onClick={() => { setEditingProfile(false); setTempProfile(profile); }} variant="ghost">
                      취소
                    </Button>
                    <Button onClick={saveProfile} variant="primary">
                      저장
                    </Button>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    🏆 Solved.ac (백준) 아이디
                  </label>
                  {editingProfile ? (
                    <input
                      type="text"
                      value={tempProfile.solvedac_handle || ""}
                      onChange={(e) => setTempProfile({ ...tempProfile, solvedac_handle: e.target.value })}
                      placeholder="백준 아이디 입력"
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    />
                  ) : (
                    <p className="text-gray-900 dark:text-white px-4 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      {profile.solvedac_handle || "미설정"}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    📝 Velog 아이디
                  </label>
                  {editingProfile ? (
                    <input
                      type="text"
                      value={tempProfile.velog_id || ""}
                      onChange={(e) => setTempProfile({ ...tempProfile, velog_id: e.target.value })}
                      placeholder="Velog 아이디 입력 (예: lova-clover)"
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    />
                  ) : (
                    <p className="text-gray-900 dark:text-white px-4 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      {profile.velog_id || "미설정"}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </Card>

          {/* Portfolio Settings Card */}
          <Card className="p-6">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                💼 포트폴리오 설정
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                포트폴리오 페이지에 표시될 정보를 설정하세요
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    표시 이름
                  </label>
                  {editingProfile ? (
                    <input
                      type="text"
                      value={tempProfile.portfolio_name || ""}
                      onChange={(e) => setTempProfile({ ...tempProfile, portfolio_name: e.target.value })}
                      placeholder="포트폴리오에 표시될 이름"
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    />
                  ) : (
                    <p className="text-gray-900 dark:text-white px-4 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      {profile.portfolio_name || "기본 이름 사용"}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    표시 이메일
                  </label>
                  {editingProfile ? (
                    <input
                      type="email"
                      value={tempProfile.portfolio_email || ""}
                      onChange={(e) => setTempProfile({ ...tempProfile, portfolio_email: e.target.value })}
                      placeholder="포트폴리오에 표시될 이메일"
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    />
                  ) : (
                    <p className="text-gray-900 dark:text-white px-4 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      {profile.portfolio_email || "기본 이메일 사용"}
                    </p>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  자기소개
                </label>
                {editingProfile ? (
                  <textarea
                    value={tempProfile.portfolio_bio || ""}
                    onChange={(e) => setTempProfile({ ...tempProfile, portfolio_bio: e.target.value })}
                    placeholder="포트폴리오에 표시될 자기소개"
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                  />
                ) : (
                  <p className="text-gray-900 dark:text-white px-4 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg min-h-[80px]">
                    {profile.portfolio_bio || "미설정"}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  표시할 프로젝트 개수
                </label>
                {editingProfile ? (
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={tempProfile.max_portfolio_repos}
                    onChange={(e) => setTempProfile({ ...tempProfile, max_portfolio_repos: parseInt(e.target.value) || 6 })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                  />
                ) : (
                  <p className="text-gray-900 dark:text-white px-4 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    {profile.max_portfolio_repos}개 (커밋 수 기준 상위)
                  </p>
                )}
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  포트폴리오에 표시될 프로젝트는 커밋 수가 많은 순서로 선택됩니다.
                </p>
              </div>
            </div>
          </Card>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 mt-8">
            데이터 동기화
          </h2>

          {syncStatuses.map((sync) => (
            <Card key={sync.source} className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
                    {getSourceIcon(sync.source)}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {getSourceName(sync.source)}
                    </h3>
                    <div className="flex items-center gap-4 mt-1 text-sm text-gray-600 dark:text-gray-400">
                      <span>수집된 항목: {sync.items_synced}개</span>
                      <span>마지막 동기화: {formatDate(sync.last_synced_at)}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  {getStatusBadge(sync.status)}
                  <Button
                    onClick={() => triggerSync(sync.source)}
                    disabled={syncing[sync.source]}
                    variant="primary"
                  >
                    <RefreshCw
                      className={`w-4 h-4 mr-2 ${
                        syncing[sync.source] ? "animate-spin" : ""
                      }`}
                    />
                    {syncing[sync.source] ? "동기화 중..." : "동기화"}
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </motion.div>

        {/* Instructions */}
        <motion.div variants={itemVariants}>
          <Card className="p-6 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
            <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">
              💡 동기화 안내
            </h3>
            <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
              <li>
                • <strong>GitHub</strong>: GitHub 계정으로 로그인하면 자동으로 연동됩니다.
              </li>
              <li>
                • <strong>Solved.ac</strong>: 온보딩에서 백준 아이디를 입력하면 문제 풀이 기록을 수집합니다.
              </li>
              <li>
                • <strong>Velog</strong>: 온보딩에서 Velog 아이디를 입력하면 블로그 포스트를 수집합니다.
              </li>
              <li>
                • 동기화 버튼을 클릭하면 최신 데이터를 가져옵니다.
              </li>
              <li>
                • 대량의 데이터는 백그라운드에서 처리되므로 시간이 걸릴 수 있습니다.
              </li>
            </ul>
          </Card>
        </motion.div>
      </motion.div>
    </div>
  );
}
