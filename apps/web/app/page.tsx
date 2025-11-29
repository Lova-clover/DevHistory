export default function Home() {
  return (
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-4xl mx-auto text-center">
        <h1 className="text-5xl font-bold mb-6">
          개발 활동을 자동으로 <span className="text-primary-600">머지</span>하세요
        </h1>
        <p className="text-xl text-gray-600 mb-12">
          GitHub, solved.ac, 노트를 자동 수집해서<br />
          포트폴리오와 블로그 콘텐츠로 만들어드립니다
        </p>
        
        <div className="flex gap-4 justify-center mb-16">
          <a
            href="/api/auth/github/login"
            className="bg-primary-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-primary-700 transition"
          >
            GitHub로 시작하기
          </a>
          <a
            href="/dashboard"
            className="border border-primary-600 text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-primary-50 transition"
          >
            대시보드 둘러보기
          </a>
        </div>

        <div className="grid md:grid-cols-3 gap-8 text-left">
          <div className="p-6 border rounded-lg">
            <h3 className="text-xl font-bold mb-2">🔄 자동 수집</h3>
            <p className="text-gray-600">
              GitHub 커밋, solved.ac 문제, Velog 포스트를 자동으로 수집합니다
            </p>
          </div>
          <div className="p-6 border rounded-lg">
            <h3 className="text-xl font-bold mb-2">📊 타임라인</h3>
            <p className="text-gray-600">
              주간/월간 활동을 시각화하고 집계 데이터를 제공합니다
            </p>
          </div>
          <div className="p-6 border rounded-lg">
            <h3 className="text-xl font-bold mb-2">✨ AI 생성</h3>
            <p className="text-gray-600">
              LLM으로 블로그 글, 리포트, 포트폴리오를 자동 생성합니다
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
