"""Data aggregation for timeline."""
from typing import Dict, Any, List
from datetime import datetime


def aggregate_week_data(commits: List[Any], problems: List[Any], notes: List[Any]) -> Dict[str, Any]:
    """
    Aggregate weekly data into summary JSON.
    
    Args:
        commits: List of commit objects
        problems: List of problem objects
        notes: List of note objects
        
    Returns:
        Aggregated summary dictionary
    """
    summary = {
        "by_day": {},
        "problems_by_tag": {},
        "commits_by_repo": {},
    }
    
    # Aggregate by day
    for commit in commits:
        day_str = commit.committed_at.strftime("%Y-%m-%d")
        if day_str not in summary["by_day"]:
            summary["by_day"][day_str] = {"commits": 0, "problems": 0, "notes": 0}
        summary["by_day"][day_str]["commits"] += 1
    
    for problem in problems:
        day_str = problem.solved_at.strftime("%Y-%m-%d")
        if day_str not in summary["by_day"]:
            summary["by_day"][day_str] = {"commits": 0, "problems": 0, "notes": 0}
        summary["by_day"][day_str]["problems"] += 1
        
        # Aggregate by tag
        for tag in problem.tags or []:
            summary["problems_by_tag"][tag] = summary["problems_by_tag"].get(tag, 0) + 1
    
    for note in notes:
        day_str = note.created_at.strftime("%Y-%m-%d")
        if day_str not in summary["by_day"]:
            summary["by_day"][day_str] = {"commits": 0, "problems": 0, "notes": 0}
        summary["by_day"][day_str]["notes"] += 1
    
    # Aggregate commits by repo
    for commit in commits:
        repo_name = commit.repo.full_name if commit.repo else "Unknown"
        summary["commits_by_repo"][repo_name] = summary["commits_by_repo"].get(repo_name, 0) + 1
    
    return summary
