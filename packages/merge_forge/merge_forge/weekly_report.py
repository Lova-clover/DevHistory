"""Generate weekly report using LLM with data-quality aware prompting."""
from __future__ import annotations

from typing import Any, Dict, Optional

from merge_core.llm import generate_text


def generate_weekly_report(
    user: Any,
    weekly_summary: Any,
    style_profile: Any,
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
) -> str:
    """
    Generate weekly report content using LLM.

    The prompt includes data-quality guidance so the model does not over-interpret
    sparse/uncertain signals (especially problem timestamps and notes volume).
    """
    summary_json = weekly_summary.summary_json or {}
    by_day = summary_json.get("by_day", {}) or {}
    problems_by_tag = summary_json.get("problems_by_tag", {}) or {}
    commits_by_repo = summary_json.get("commits_by_repo", {}) or {}

    quality = _assess_signal_quality(
        commit_count=int(weekly_summary.commit_count or 0),
        problem_count=int(weekly_summary.problem_count or 0),
        note_count=int(weekly_summary.note_count or 0),
        by_day=by_day,
        problems_by_tag=problems_by_tag,
    )

    system_prompt = _build_system_prompt(style_profile, quality)
    user_prompt = _build_user_prompt(weekly_summary, by_day, problems_by_tag, commits_by_repo, quality)
    return generate_text(system_prompt, user_prompt, model=model, api_key=api_key)


def _build_system_prompt(style_profile: Any, quality: Dict[str, Any]) -> str:
    language = getattr(style_profile, "language", "ko") or "ko"
    tone = getattr(style_profile, "tone", "technical") or "technical"
    report_structure = getattr(style_profile, "report_structure", None) or [
        "Summary",
        "What I did",
        "Learned",
        "Next",
    ]

    lines = [
        "You are a factual engineering writing assistant.",
        f"Output language: {language}",
        f"Tone: {tone}",
        "Output format: Markdown",
        "Do not invent activities, numbers, tools, or outcomes.",
        "Use only the evidence in the input data.",
        "When evidence is weak, explicitly state uncertainty instead of guessing.",
        "Always include a short 'Data Confidence' section with confidence labels for commits/problems/notes.",
        "Confidence labels must be one of: high, medium, low, none.",
        "Important constraint for problems data: solved_at may represent sync time, not exact solve time.",
        "If problem confidence is low/medium, avoid date-level claims about problem solving pace.",
        "If notes confidence is none/low, avoid inferring deep learning outcomes from notes.",
        "Prefer concrete, measurable wording over generic praise.",
        "Recommended section order: " + " > ".join(report_structure),
    ]

    extra = getattr(style_profile, "extra_instructions", None)
    if extra:
        lines.append(f"Extra instruction: {extra}")

    lines.append(
        "Current quality hints: "
        f"commits={quality['commit_signal']}, "
        f"problems={quality['problem_signal']}, "
        f"notes={quality['note_signal']}."
    )
    return "\n".join(lines)


def _build_user_prompt(
    weekly_summary: Any,
    by_day: Dict[str, Dict[str, int]],
    problems_by_tag: Dict[str, int],
    commits_by_repo: Dict[str, int],
    quality: Dict[str, Any],
) -> str:
    return f"""Weekly window: {weekly_summary.week_start} ~ {weekly_summary.week_end}

[Aggregated counts]
- commits: {weekly_summary.commit_count}
- problems: {weekly_summary.problem_count}
- notes: {weekly_summary.note_count}

[Daily activity]
{_format_daily_activities(by_day)}

[Problem tags]
{_format_tag_distribution(problems_by_tag)}

[Commits by repository]
{_format_repo_distribution(commits_by_repo)}

[Data quality assessment]
- commits: {quality['commit_signal']} ({quality['commit_reason']})
- problems: {quality['problem_signal']} ({quality['problem_reason']})
- notes: {quality['note_signal']} ({quality['note_reason']})
- guidance: {quality['global_guidance']}

Write a weekly retrospective using only this evidence.
Required constraints:
1) Start with one-paragraph summary.
2) Include what was done, what was learned, what was difficult, and concrete next actions.
3) Include a 'Data Confidence' section that explains which conclusions are strong vs weak.
4) Do not overstate problems/notes if their confidence is not high.
5) End with 3-5 actionable tasks for next week.
"""


def _assess_signal_quality(
    commit_count: int,
    problem_count: int,
    note_count: int,
    by_day: Dict[str, Dict[str, int]],
    problems_by_tag: Dict[str, int],
) -> Dict[str, str]:
    active_days = sum(1 for v in by_day.values() if (v.get("commits", 0) + v.get("problems", 0) + v.get("notes", 0)) > 0)

    # Commits: usually the most reliable signal in this system.
    if commit_count == 0:
        commit_signal = "none"
        commit_reason = "No commit events were captured in this week."
    elif commit_count < 5:
        commit_signal = "medium"
        commit_reason = "Commit volume is low; trend interpretation is limited."
    else:
        commit_signal = "high"
        commit_reason = "Commit volume is sufficient for weekly trend statements."

    # Problems: solved_at may be sync time; tag distribution improves confidence.
    if problem_count == 0:
        problem_signal = "none"
        problem_reason = "No solved problem entries were captured."
    elif problem_count <= 2 or not problems_by_tag:
        problem_signal = "low"
        problem_reason = (
            "Sparse problem data and/or missing tag spread. "
            "Also, solved_at may reflect sync timing."
        )
    elif problem_count < 8:
        problem_signal = "medium"
        problem_reason = "Usable signal, but date-level pace claims may still be noisy."
    else:
        problem_signal = "medium"
        problem_reason = (
            "Volume is solid, but solved_at can still be sync-derived; "
            "avoid over-precise temporal claims."
        )

    # Notes: often sparse, so require enough volume for strong conclusions.
    if note_count == 0:
        note_signal = "none"
        note_reason = "No notes were captured this week."
    elif note_count <= 2:
        note_signal = "low"
        note_reason = "Very few notes; use as anecdotal signal only."
    elif note_count < 6:
        note_signal = "medium"
        note_reason = "Moderate note volume; inference should stay conservative."
    else:
        note_signal = "high"
        note_reason = "Sufficient note volume for recurring pattern discussion."

    if active_days <= 1:
        global_guidance = "Activity is concentrated in very few days. Avoid broad productivity claims."
    elif problem_signal in ("low", "none") and note_signal in ("low", "none"):
        global_guidance = "Lean more on commits and clearly mark weak evidence areas."
    else:
        global_guidance = "Balance repo activity with study signals, and label uncertainty explicitly."

    return {
        "commit_signal": commit_signal,
        "commit_reason": commit_reason,
        "problem_signal": problem_signal,
        "problem_reason": problem_reason,
        "note_signal": note_signal,
        "note_reason": note_reason,
        "global_guidance": global_guidance,
    }


def _format_daily_activities(by_day: Dict[str, Dict[str, int]]) -> str:
    if not by_day:
        return "(no daily activity data)"
    lines = []
    for day, counts in sorted(by_day.items()):
        lines.append(
            f"- {day}: commits {counts.get('commits', 0)}, "
            f"problems {counts.get('problems', 0)}, notes {counts.get('notes', 0)}"
        )
    return "\n".join(lines)


def _format_tag_distribution(tags: Dict[str, int]) -> str:
    if not tags:
        return "(no problem tags)"
    sorted_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)
    return ", ".join([f"{tag}({count})" for tag, count in sorted_tags[:15]])


def _format_repo_distribution(repos: Dict[str, int]) -> str:
    if not repos:
        return "(no repository commit split)"
    sorted_repos = sorted(repos.items(), key=lambda x: x[1], reverse=True)
    return "\n".join([f"- {repo}: {count}" for repo, count in sorted_repos[:20]])
