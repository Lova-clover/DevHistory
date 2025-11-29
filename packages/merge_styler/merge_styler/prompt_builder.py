"""System prompt builder based on style profile."""
from typing import Any


def build_system_prompt(style_profile: Any, output_type: str) -> str:
    """
    Build LLM system prompt based on user's style profile.
    
    Args:
        style_profile: StyleProfile object
        output_type: Type of output ('weekly_report', 'repo_blog', 'portfolio_section')
        
    Returns:
        System prompt string
    """
    base = [
        "너는 사용자의 개발/공부 활동을 정리해주는 개인 비서이자 편집자다.",
        f"출력 언어는 {style_profile.language}이다.",
        f"톤은 {style_profile.tone} 스타일이다."
    ]
    
    if output_type == "weekly_report":
        base.append(
            "가능하면 다음 섹션 구조를 유지해라: " +
            " > ".join(style_profile.report_structure)
        )
    elif output_type == "repo_blog":
        base.append(
            "가능하면 다음 섹션 구조를 유지해라: " +
            " > ".join(style_profile.blog_structure)
        )
    elif output_type == "portfolio_section":
        base.append("간결하고 임팩트 있는 bullet point 형식으로 작성해라.")
    
    if style_profile.extra_instructions:
        base.append("추가 지침: " + style_profile.extra_instructions)
    
    return "\n".join(base)


def get_default_blog_structure() -> list[str]:
    """Get default blog structure."""
    return ["Intro", "Problem", "Approach", "Result", "Next"]


def get_default_report_structure() -> list[str]:
    """Get default report structure."""
    return ["Summary", "What I did", "Learned", "Next"]
