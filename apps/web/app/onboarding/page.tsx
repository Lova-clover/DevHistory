"use client";

import { useState } from "react";

export default function OnboardingPage() {
  const [formData, setFormData] = useState({
    solvedacHandle: "",
    velogId: "",
    language: "ko",
    tone: "technical",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Update user profile
    await fetch("/api/profile/user", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        solvedac_handle: formData.solvedacHandle,
        velog_id: formData.velogId,
      }),
    });

    // Update style profile
    await fetch("/api/profile/style", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        language: formData.language,
        tone: formData.tone,
        blog_structure: ["Intro", "Problem", "Approach", "Result", "Next"],
        report_structure: ["Summary", "What I did", "Learned", "Next"],
      }),
    });

    // Redirect to dashboard
    window.location.href = "/dashboard";
  };

  return (
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">환영합니다! 🎉</h1>
        <p className="text-gray-600 mb-8">
          DevHistory를 사용하기 위해 몇 가지 정보를 설정해주세요
        </p>

        <form onSubmit={handleSubmit} className="space-y-6 bg-white dark:bg-gray-800 p-8 rounded-lg shadow-lg">
          <div>
            <label className="block text-sm font-medium mb-2">
              solved.ac 핸들 (선택)
            </label>
            <input
              type="text"
              value={formData.solvedacHandle}
              onChange={(e) => setFormData({ ...formData, solvedacHandle: e.target.value })}
              placeholder="예: Lova_clover"
              className="w-full border rounded-lg px-4 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Velog ID (선택)
            </label>
            <input
              type="text"
              value={formData.velogId}
              onChange={(e) => setFormData({ ...formData, velogId: e.target.value })}
              placeholder="예: @username"
              className="w-full border rounded-lg px-4 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              선호하는 언어
            </label>
            <select
              value={formData.language}
              onChange={(e) => setFormData({ ...formData, language: e.target.value })}
              className="w-full border rounded-lg px-4 py-2"
            >
              <option value="ko">한국어</option>
              <option value="en">English</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              글 스타일
            </label>
            <select
              value={formData.tone}
              onChange={(e) => setFormData({ ...formData, tone: e.target.value })}
              className="w-full border rounded-lg px-4 py-2"
            >
              <option value="technical">기술적 (Technical)</option>
              <option value="casual">일상적 (Casual)</option>
              <option value="study-note">공부 노트 (Study Note)</option>
            </select>
          </div>

          <button
            type="submit"
            className="w-full bg-primary-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-700 transition"
          >
            시작하기
          </button>
        </form>
      </div>
    </div>
  );
}
