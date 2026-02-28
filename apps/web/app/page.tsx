import Image from "next/image";

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-4xl mx-auto text-center">
        <Image
          src="/devhistory_logo.png"
          alt="DevHistory"
          width={96}
          height={96}
          className="mx-auto mb-8 rounded-2xl shadow-lg"
        />
        <h1 className="text-5xl font-bold mb-6 text-gray-900 dark:text-white">
          개발 활동을 자동으로 <span className="text-primary-600 dark:text-primary-400">머지</span>하세요
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-400 mb-12">
          GitHub, solved.ac, Velog를 자동 수집해서<br />
          포트폴리오, 블로그, 이력서까지 만들어드립니다
        </p>
        
        <div className="flex gap-4 justify-center mb-16">
          <a
            href="/api/auth/github/login"
            className="bg-primary-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-primary-700 transition shadow-md hover:shadow-lg"
          >
            GitHub로 시작하기
          </a>
          <a
            href="/dashboard"
            className="border border-primary-600 text-primary-600 dark:text-primary-400 dark:border-primary-400 px-8 py-3 rounded-lg font-semibold hover:bg-primary-50 dark:hover:bg-primary-900/20 transition"
          >
            대시보드 둘러보기
          </a>
        </div>

        <div className="grid md:grid-cols-3 gap-6 text-left">
          <div className="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm hover:shadow-md transition">
            <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">🔄 자동 수집</h3>
            <p className="text-gray-600 dark:text-gray-400">
              GitHub 커밋, solved.ac 문제, Velog 포스트를 자동으로 수집합니다
            </p>
          </div>
          <div className="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm hover:shadow-md transition">
            <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">🎓 AI 코칭</h3>
            <p className="text-gray-600 dark:text-gray-400">
              문제 풀이 패턴을 분석하고 맞춤형 퀴즈와 학습 로드맵을 제공합니다
            </p>
          </div>
          <div className="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm hover:shadow-md transition">
            <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">✨ AI 생성</h3>
            <p className="text-gray-600 dark:text-gray-400">
              블로그 글, 주간 리포트, 이력서, 자기소개서를 AI가 작성합니다
            </p>
          </div>
          <div className="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm hover:shadow-md transition">
            <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">✏️ 글쓰기 스타일</h3>
            <p className="text-gray-600 dark:text-gray-400">
              Velog 글을 분석해 나만의 글쓰기 스타일을 학습하고 적용합니다
            </p>
          </div>
          <div className="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm hover:shadow-md transition">
            <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">📊 타임라인</h3>
            <p className="text-gray-600 dark:text-gray-400">
              주간·월간 활동을 시각화하고 성장 트렌드를 한눈에 확인합니다
            </p>
          </div>
          <div className="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm hover:shadow-md transition">
            <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">🌐 포트폴리오</h3>
            <p className="text-gray-600 dark:text-gray-400">
              공개 포트폴리오 링크를 생성하고 PDF로 다운로드할 수 있습니다
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
