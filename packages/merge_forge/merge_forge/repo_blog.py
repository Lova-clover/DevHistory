"""Generate repository blog post using LLM."""
from typing import Any
from merge_core.llm import generate_text


def generate_repo_blog(
    user: Any,
    repo: Any,
    style_profile: Any,
    readme_content: str = "",
) -> str:
    """
    Generate blog post for a repository using LLM.
    
    Args:
        user: User object
        repo: Repo object
        style_profile: StyleProfile object
        readme_content: README content (optional)
        
    Returns:
        Generated markdown content
    """
    # Build system prompt from style profile
    system_prompt = _build_system_prompt(style_profile, "repo_blog")
    
    # Build user prompt with repo data
    user_prompt = f"""다음은 GitHub 레포지토리 정보다.

- 이름: {repo.full_name}
- 설명: {repo.description or '(설명 없음)'}
- 주 언어: {repo.language or '정보 없음'}
- 스타: {repo.stars}
- URL: {repo.html_url}

README 내용 (일부 발췌):
-------------------
{readme_content[:1000] if readme_content else '(README 없음)'}

위 정보를 바탕으로, Velog에 올릴 수 있는 기술 블로그 글 초안을 작성해줘.
- 이 프로젝트가 해결하려는 문제
- 사용한 기술 스택
- 핵심 아이디어/알고리즘
- 시행착오/개선 포인트
- 정리 및 다음 계획
을 포함해ra.
Markdown으로 작성.
"""
    
    return generate_text(system_prompt, user_prompt)


def _build_system_prompt(style_profile: Any, output_type: str) -> str:
    """Build system prompt based on style profile."""
    base = [
        "너는 사용자의 개발/공부 활동을 정리해주는 개인 비서이자 편집자다.",
        f"출력 언어는 {style_profile.language}이다.",
        f"톤은 {style_profile.tone} 스타일이다."
    ]
    
    if output_type == "repo_blog":
        base.append(
            "가능하면 다음 섹션 구조를 유지해라: " +
            " > ".join(style_profile.blog_structure)
        )
    
    if style_profile.extra_instructions:
        base.append("추가 지침: " + style_profile.extra_instructions)
    
    return "\n".join(base)
