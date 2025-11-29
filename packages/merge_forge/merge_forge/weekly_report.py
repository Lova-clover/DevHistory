"""Generate weekly report using LLM."""
from typing import Any, Dict
from merge_core.llm import generate_text


def generate_weekly_report(
    user: Any,
    weekly_summary: Any,
    style_profile: Any,
) -> str:
    """
    Generate weekly report content using LLM.
    
    Args:
        user: User object
        weekly_summary: WeeklySummary object
        style_profile: StyleProfile object
        
    Returns:
        Generated markdown content
    """
    # Build system prompt from style profile
    system_prompt = _build_system_prompt(style_profile, "weekly_report")
    
    # Build user prompt with weekly data
    user_prompt = f"""다음은 {weekly_summary.week_start} ~ {weekly_summary.week_end} 동안의 활동 집계 데이터다.

1) 요약 통계:
- 커밋 수: {weekly_summary.commit_count}
- 푼 문제 수: {weekly_summary.problem_count}
- 작성한 노트 수: {weekly_summary.note_count}

2) 날짜별 활동:
{_format_daily_activities(weekly_summary.summary_json.get("by_day", {}))}

3) 문제 태그별 분포:
{_format_tag_distribution(weekly_summary.summary_json.get("problems_by_tag", {}))}

4) 레포별 커밋 분포:
{_format_repo_distribution(weekly_summary.summary_json.get("commits_by_repo", {}))}

위 정보를 바탕으로 이번 주 개발/공부 회고를 작성해줘.
- 실제 한 일을 중심으로 정리하되 과장하지 말 것
- 새로 배운 점, 아쉬운 점, 다음 주에 이어서 할 일을 포함
- Markdown 형식으로 작성
"""
    
    return generate_text(system_prompt, user_prompt)


def _build_system_prompt(style_profile: Any, output_type: str) -> str:
    """Build system prompt based on style profile."""
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
    
    if style_profile.extra_instructions:
        base.append("추가 지침: " + style_profile.extra_instructions)
    
    return "\n".join(base)


def _format_daily_activities(by_day: Dict[str, Dict[str, int]]) -> str:
    """Format daily activities for prompt."""
    lines = []
    for day, counts in sorted(by_day.items()):
        lines.append(f"- {day}: 커밋 {counts['commits']}개, 문제 {counts['problems']}개, 노트 {counts['notes']}개")
    return "\n".join(lines) if lines else "(활동 없음)"


def _format_tag_distribution(tags: Dict[str, int]) -> str:
    """Format tag distribution for prompt."""
    if not tags:
        return "(태그 정보 없음)"
    sorted_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)
    return ", ".join([f"{tag}({count})" for tag, count in sorted_tags[:10]])


def _format_repo_distribution(repos: Dict[str, int]) -> str:
    """Format repo distribution for prompt."""
    if not repos:
        return "(레포 정보 없음)"
    sorted_repos = sorted(repos.items(), key=lambda x: x[1], reverse=True)
    return "\n".join([f"- {repo}: {count}개" for repo, count in sorted_repos])
