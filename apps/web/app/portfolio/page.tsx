export default function PortfolioPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">내 포트폴리오</h1>

      {/* Profile Section */}
      <div className="bg-white p-8 rounded-lg shadow mb-8">
        <div className="flex items-center gap-6 mb-6">
          <div className="w-24 h-24 bg-gray-200 rounded-full"></div>
          <div>
            <h2 className="text-2xl font-bold">성주 (Lova-clover)</h2>
            <p className="text-gray-600">Full Stack Developer</p>
          </div>
        </div>
        <div className="grid md:grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-3xl font-bold text-primary-600">12</p>
            <p className="text-gray-600">레포지토리</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-green-600">234</p>
            <p className="text-gray-600">문제 해결</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-purple-600">89</p>
            <p className="text-gray-600">총 커밋</p>
          </div>
        </div>
      </div>

      {/* Featured Repos */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">주요 프로젝트</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-bold mb-2">FreshGuard</h3>
            <p className="text-gray-600 mb-4">
              식품 유통기한 관리 및 알림 시스템
            </p>
            <div className="flex gap-2">
              <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">Python</span>
              <span className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded">FastAPI</span>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-bold mb-2">Path Planning</h3>
            <p className="text-gray-600 mb-4">
              A* 알고리즘 기반 경로 탐색 시뮬레이터
            </p>
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
