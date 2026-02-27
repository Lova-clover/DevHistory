"""Generate repository blog post using LLM."""
from typing import Any, Optional
from merge_core.llm import generate_text


def generate_repo_blog(
    user: Any,
    repo: Any,
    style_profile: Any,
    readme_content: str = "",
    commit_summary: str = "",
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
) -> str:
    """
    Generate blog post for a repository using LLM.
    
    Args:
        user: User object
        repo: Repo object
        style_profile: StyleProfile object
        readme_content: README content (optional)
        commit_summary: Recent commit messages (optional)
        
    Returns:
        Generated markdown content
    """
    # Build system prompt from style profile
    system_prompt = _build_system_prompt(style_profile, "repo_blog")
    
    # Build user prompt with repo data
    user_prompt = f"""다음은 GitHub 레포지토리 정보입니다.

**레포지토리 정보**
- 이름: {repo.full_name}
- 설명: {repo.description or '(설명 없음)'}
- 주 언어: {repo.language or '정보 없음'}
- 스타: {repo.stars}
- 생성일: {repo.created_at.strftime('%Y년 %m월') if repo.created_at else '알 수 없음'}
- URL: {repo.html_url}

**README**
```
{readme_content[:3000] if readme_content else '(README 없음)'}
```

{f'''**최근 개발 활동**
{commit_summary}
''' if commit_summary else ''}

위 레포지토리에 대한 Velog 기술 블로그 글을 작성해주세요.

**작성 가이드라인:**

📌 **제목 스타일** (실제 Velog 글 참고)
- "FreshGuard – EfficientNet-B0로 과일 신선도 판별 모델 만들기"
- "YOLO와 PaddleOCR로 상품·성분표 인식 파이프라인 구성해본 경험"
- "Streamlit을 활용한 실시간 빈혈 판별 웹앱 개발"
→ 핵심 기술 스택 + 구체적인 목표를 명시. "~해본 경험", "~만들기", "~개발" 같은 어미 사용

📝 **글의 구조**
```
## 0. 배경 – 왜 시작했는가
- 문제 상황이나 동기를 개인적인 경험과 함께 서술
- "~하다가", "~을 보고", "~가 필요했다" 식의 자연스러운 전개

## 1. 문제 정의
- 해결하려는 문제를 명확히 정의
- 처음 생각했던 접근과 현실의 차이를 솔직하게

## 2. 기술 선택과 아키텍처
- 왜 이 기술을 선택했는지 이유와 함께
- 전체 구조를 간단한 다이어그램이나 설명으로

## 3. 구현 과정 (핵심 부분)
- 실제 코드나 핵심 로직 설명
- 버전별 개선사항 (V1.0 → V1.1 → V1.2)
- 구체적인 라이브러리명, 함수명, 설정값 포함

## 4. 겪은 문제들
- 예상치 못한 버그나 한계
- "처음엔 ~할 줄 알았는데", "막상 해보니~" 같은 솔직한 표현
- 각 문제마다 어떻게 해결했는지

## 5. 결과
- 성능 수치나 스크린샷
- 데모 링크나 실행 결과

## 6. 한계와 개선점
- 아직 부족한 부분을 솔직하게
- 다음에 시도해볼 것들

## 7. 마무리 – 배운 것
- 핵심 포인트 3-4개를 간결하게
- 다음 프로젝트에 활용할 교훈
```

✍️ **작성 톤 (중요!)**
- 반말 사용 (습니다 → 다, 했습니다 → 했다)
- 편하고 친근한 느낌: "근데 막상 해보니", "생각보다 쉽지 않았다", "여기서 삽질을 좀 했는데"
- 완벽하지 않아도 괜찮다는 느낌: "아직 부족하지만", "이 정도면 괜찮은 것 같다"
- 시간 흐름을 자연스럽게: "처음엔", "그러다가", "결국"

💡 **중요 깨달음 표현**
```
> "OCR 모델이 다 해줄 거라고 믿은 순간부터 이미 틀렸구나."
> "정확도보다 먼저 생각해야 할 건 데이터 품질이었다."
```
→ 인용구로 강조. 짧고 임팩트 있게.

🔍 **구체성**
- ❌ "모델을 학습시켰다" 
- ✅ "EfficientNet-B0를 Fine-tuning했고, learning rate는 0.001, batch size 32로 50 epoch 돌렸다"

- ❌ "성능이 좋아졌다"
- ✅ "정확도가 73%에서 89%로 올랐다"

📏 **적절한 길이**
- 너무 짧지 않게: 최소 1500자 이상
- 섹션별로 균형있게: 각 섹션마다 2-4 문단
- 코드가 필요한 부분엔 간단한 스니펫 포함

🎯 **실제 경험 느낌 살리기**
- README나 공식 문서 그대로 옮기지 말 것
- "내가 직접 개발하면서 느낀 것"처럼 써야 함
- "이 프로젝트를 하면서~", "개발 과정에서~" 같은 1인칭 시점

Markdown 형식으로 작성해주세요. 제목(#)부터 시작."""
    
    return generate_text(system_prompt, user_prompt, model=model, api_key=api_key)


def _build_system_prompt(style_profile: Any, output_type: str) -> str:
    """Build system prompt based on style profile."""
    base = [
        "너는 Velog에 기술 블로그를 작성하는 대학생 개발자 '성주(Seongju)'의 글쓰기 도우미다.",
        "사용자의 개발 경험을 친근하고 솔직한 기술 회고록 스타일로 정리해준다.",
        f"출력 언어는 {style_profile.language}이다.",
        "",
        "**글쓰기 특징:**",
        "- 반말 사용 (~다, ~했다, ~같다)",
        "- 친근하고 편안한 톤: '막상 해보니', '생각보다', '근데'",
        "- 시행착오와 삽질 경험도 솔직하게 공유",
        "- '처음엔...했다', '그러다가', '결국' 같은 자연스러운 흐름",
        "- 명확한 섹션 구조 (## 0. 배경, ## 1. 문제 정의 형식)",
        "- 중요한 깨달음은 인용구(> )로 강조",
        "- 구체적인 기술명: 'EfficientNet-B0', 'YOLO', 'PaddleOCR' 등",
        "- 성능 수치와 버전별 개선 과정을 명확히",
        "- 1인칭 시점: '이 프로젝트를 하면서', '개발 과정에서'",
        "- 마무리는 핵심 포인트 3-4개로 간결하게",
    ]
    
    if output_type == "repo_blog":
        base.append("\n**블로그 구조:** 배경(왜) → 문제정의 → 기술선택 → 구현과정(코드 포함) → 겪은 문제들 → 결과(수치) → 한계와 개선점 → 배운 것")
    
    if style_profile.extra_instructions:
        base.append(f"\n추가 지침: {style_profile.extra_instructions}")
    
    return "\n".join(base)
