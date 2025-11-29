'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api, useAsync } from '@/lib/api-client';
import { useToast, useCommonToasts } from '@/components/ui/toast';
import { LoadingOverlay, Skeleton } from '@/components/ui/loading';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { GitBranch, Code, Award, FileText, TrendingUp, Calendar, Flame } from 'lucide-react';

interface DashboardStats {
  total_repos: number;
  total_commits: number;
  total_problems_solved: number;
  total_blog_posts: number;
  commits_this_week: number;
  commits_this_month: number;
  problems_this_week: number;
  problems_this_month: number;
  current_streak: number;
  longest_streak: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const toast = useCommonToasts();
  const statsState = useAsync<DashboardStats>();
  const syncState = useAsync<any>();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      await statsState.execute(api.dashboard.getStats());
    } catch (error: any) {
      if (error.status === 401) {
        router.push('/login');
      } else {
        toast.apiError(error);
      }
    }
  };

  const handleSync = async (source: 'github' | 'solvedac' | 'velog') => {
    try {
      await syncState.execute(api.collector.sync(source));
      toast.syncSuccess(source, 0);
      // Reload data after sync
      setTimeout(() => loadDashboardData(), 2000);
    } catch (error: any) {
      toast.syncError(source);
    }
  };

  const { data: stats, loading, error } = statsState;

  if (loading && !stats) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          <Skeleton className="h-12 w-64" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <Card padding="lg" className="max-w-md text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Failed to load dashboard</h2>
          <p className="text-gray-600 mb-6">{error?.message || 'Unknown error occurred'}</p>
          <Button onClick={loadDashboardData}>Retry</Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <LoadingOverlay visible={syncState.loading} message="Syncing data..." />
      
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
              <p className="text-gray-600 mt-1">Welcome back! Here's your development overview.</p>
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleSync('github')}
                leftIcon={<GitBranch className="w-4 h-4" />}
              >
                Sync GitHub
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleSync('solvedac')}
                leftIcon={<Code className="w-4 h-4" />}
              >
                Sync solved.ac
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleSync('velog')}
                leftIcon={<FileText className="w-4 h-4" />}
              >
                Sync Velog
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Total Repos */}
          <StatsCard
            title="Total Repositories"
            value={stats.total_repos}
            icon={<GitBranch className="w-6 h-6" />}
            color="blue"
          />

          {/* Total Commits */}
          <StatsCard
            title="Total Commits"
            value={stats.total_commits}
            icon={<Code className="w-6 h-6" />}
            color="green"
            subtitle={`${stats.commits_this_week} this week`}
          />

          {/* Problems Solved */}
          <StatsCard
            title="Problems Solved"
            value={stats.total_problems_solved}
            icon={<Award className="w-6 h-6" />}
            color="purple"
            subtitle={`${stats.problems_this_week} this week`}
          />

          {/* Blog Posts */}
          <StatsCard
            title="Blog Posts"
            value={stats.total_blog_posts}
            icon={<FileText className="w-6 h-6" />}
            color="orange"
          />
        </div>

        {/* Activity Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          {/* This Week */}
          <Card hoverable>
            <CardHeader>
              <CardTitle>This Week</CardTitle>
              <CardDescription>Your activity in the past 7 days</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <ActivityRow
                  label="Commits"
                  value={stats.commits_this_week}
                  total={stats.commits_this_month}
                  icon={<Code className="w-5 h-5 text-green-600" />}
                />
                <ActivityRow
                  label="Problems"
                  value={stats.problems_this_week}
                  total={stats.problems_this_month}
                  icon={<Award className="w-5 h-5 text-purple-600" />}
                />
              </div>
            </CardContent>
          </Card>

          {/* Streaks */}
          <Card hoverable>
            <CardHeader>
              <CardTitle>Activity Streaks</CardTitle>
              <CardDescription>Keep the momentum going!</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                      <Flame className="w-6 h-6 text-orange-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Current Streak</p>
                      <p className="text-2xl font-bold text-gray-900">{stats.current_streak} days</p>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                      <TrendingUp className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Longest Streak</p>
                      <p className="text-2xl font-bold text-gray-900">{stats.longest_streak} days</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Generate content and manage your data</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Button
                variant="outline"
                fullWidth
                onClick={() => router.push('/weekly')}
                leftIcon={<Calendar className="w-4 h-4" />}
              >
                Create Weekly Summary
              </Button>
              <Button
                variant="outline"
                fullWidth
                onClick={() => router.push('/portfolio')}
                leftIcon={<FileText className="w-4 h-4" />}
              >
                Generate Portfolio
              </Button>
              <Button
                variant="outline"
                fullWidth
                onClick={() => router.push('/repos')}
                leftIcon={<GitBranch className="w-4 h-4" />}
              >
                View Repositories
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

interface StatsCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'purple' | 'orange';
  subtitle?: string;
}

function StatsCard({ title, value, icon, color, subtitle }: StatsCardProps) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    orange: 'bg-orange-100 text-orange-600',
  };

  return (
    <Card hoverable>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">{title}</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">{value.toLocaleString()}</p>
            {subtitle && (
              <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
            )}
          </div>
          <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${colorClasses[color]}`}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface ActivityRowProps {
  label: string;
  value: number;
  total: number;
  icon: React.ReactNode;
}

function ActivityRow({ label, value, total, icon }: ActivityRowProps) {
  const percentage = total > 0 ? (value / total) * 100 : 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-sm font-medium text-gray-700">{label}</span>
        </div>
        <span className="text-sm font-semibold text-gray-900">{value}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-primary-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-gray-500 mt-1">
        {percentage.toFixed(0)}% of this month
      </p>
    </div>
  );
}
