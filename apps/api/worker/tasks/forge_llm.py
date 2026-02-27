import sys
sys.path.insert(0, '/app/packages/merge_forge')
sys.path.insert(0, '/app/packages/merge_styler')
sys.path.insert(0, '/app/packages/merge_core')

from worker.celery_app import celery_app
from app.database import SessionLocal
from app.models.user import User
from app.models.weekly_summary import WeeklySummary
from app.models.repo import Repo
from app.models.style_profile import StyleProfile
from app.models.generated_content import GeneratedContent
from app.models.llm_credential import LlmCredential
from app.crypto import decrypt_value
from datetime import datetime


def _get_user_llm_key(db, user_id: str) -> tuple[str | None, str]:
    """Return (api_key, model) for a user. Falls back to None (env var)."""
    cred = db.query(LlmCredential).filter(LlmCredential.user_id == user_id).first()
    if cred and cred.encrypted_api_key:
        try:
            api_key = decrypt_value(cred.encrypted_api_key)
            cred.last_used_at = datetime.utcnow()
            db.commit()
            return api_key, cred.model or "gpt-4o-mini"
        except Exception:
            pass
    return None, "gpt-4o-mini"


@celery_app.task
def generate_weekly_report_llm(user_id: str, weekly_summary_id: str):
    """Generate LLM-based weekly report."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        weekly_summary = db.query(WeeklySummary).filter(WeeklySummary.id == weekly_summary_id).first()
        if not weekly_summary:
            return {"error": "Weekly summary not found"}
        
        style_profile = db.query(StyleProfile).filter(StyleProfile.user_id == user_id).first()
        if not style_profile:
            style_profile = StyleProfile(
                user_id=user_id,
                language="ko",
                tone="technical",
                blog_structure=["Summary", "What I did", "Learned", "Next"],
                report_structure=["Summary", "What I did", "Learned", "Next"],
                extra_instructions=None
            )
            db.add(style_profile)
            db.commit()
            db.refresh(style_profile)
        
        api_key, model = _get_user_llm_key(db, user_id)

        from merge_forge.weekly_report import generate_weekly_report
        content = generate_weekly_report(user, weekly_summary, style_profile, api_key=api_key, model=model)
        
        generated = GeneratedContent(
            user_id=user_id,
            content_type="weekly_report",
            source_ref=f"weekly:{weekly_summary_id}",
            content=content,
            status="completed",
        )
        db.add(generated)
        db.commit()
        
        return {"status": "success", "user_id": user_id, "weekly_id": weekly_summary_id, "content_id": str(generated.id)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task
def generate_repo_blog_llm(user_id: str, repo_id: str):
    """Generate LLM-based repo blog post."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        repo = db.query(Repo).filter(Repo.id == repo_id).first()
        if not repo:
            return {"error": "Repo not found"}
        
        style_profile = db.query(StyleProfile).filter(StyleProfile.user_id == user_id).first()
        if not style_profile:
            style_profile = StyleProfile(
                user_id=user_id,
                language="ko",
                tone="technical",
                blog_structure=["Intro", "Problem", "Approach", "Result", "Next"],
                report_structure=["Summary", "What I did", "Learned", "Next"],
                extra_instructions=None
            )
            db.add(style_profile)
            db.commit()
            db.refresh(style_profile)
        
        api_key, model = _get_user_llm_key(db, user_id)

        from merge_forge.repo_blog import generate_repo_blog
        content = generate_repo_blog(user, repo, style_profile, api_key=api_key, model=model)
        
        generated = GeneratedContent(
            user_id=user_id,
            content_type="repo_blog",
            source_ref=f"repo:{repo_id}",
            content=content,
            status="completed",
        )
        db.add(generated)
        db.commit()
        
        return {"status": "success", "user_id": user_id, "repo_id": repo_id, "content_id": str(generated.id)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task
def generate_content_llm(user_id: str, content_id: str):
    """Generic content generation task (used by POST /content and /regenerate)."""
    db = SessionLocal()
    try:
        content = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
        if not content:
            return {"error": "Content record not found"}

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            content.status = "failed"
            content.error_message = "User not found"
            db.commit()
            return {"error": "User not found"}

        # Mark as generating
        content.status = "generating"
        content.started_at = datetime.utcnow()
        db.commit()

        # Read metadata stored by the router
        meta = content.metadata or {}
        context_text = meta.get("context") or ""
        use_style = meta.get("use_style_profile", True)
        date_start = meta.get("date_range_start")
        date_end = meta.get("date_range_end")

        # Resolve style profile if requested
        style_profile = None
        if use_style:
            style_profile = db.query(StyleProfile).filter(StyleProfile.user_id == user_id).first()

        # Build LLM prompts
        system_prompt = _build_content_system_prompt(content.content_type, style_profile)
        user_prompt = _build_content_user_prompt(
            content.content_type, content.title, context_text, date_start, date_end
        )

        # Resolve API key (BYO or fallback)
        api_key, model = _get_user_llm_key(db, user_id)

        from merge_core.llm import generate_text
        generated_text = generate_text(
            system_prompt, user_prompt, model=model, api_key=api_key
        )

        now = datetime.utcnow()
        content.content = generated_text
        content.status = "completed"
        content.updated_at = now
        content.completed_at = now
        if content.started_at:
            content.generation_seconds = (now - content.started_at).total_seconds()
        db.commit()

        return {"status": "success", "content_id": content_id}
    except Exception as e:
        # Best-effort: mark failed
        try:
            content = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
            if content:
                content.status = "failed"
                content.error_message = str(e)[:2000]
                content.updated_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
        return {"error": str(e)}
    finally:
        db.close()


# ── Prompt helpers for generic content generation ────────────────

def _build_content_system_prompt(content_type: str, style_profile=None) -> str:
    parts = [
        "너는 사용자의 개발 활동을 멋진 글로 정리해주는 AI 편집자다.",
        f"생성할 콘텐츠 유형: {content_type}",
    ]
    if style_profile:
        parts.append(f"출력 언어: {style_profile.language}")
        parts.append(f"톤: {style_profile.tone}")
        if content_type in ("blog_post",) and style_profile.blog_structure:
            parts.append("글 구조: " + " > ".join(style_profile.blog_structure))
        if content_type in ("report", "summary") and style_profile.report_structure:
            parts.append("리포트 구조: " + " > ".join(style_profile.report_structure))
        if style_profile.extra_instructions:
            parts.append(f"추가 지침: {style_profile.extra_instructions}")
    else:
        parts.append("출력 언어: ko")
        parts.append("톤: technical")
    return "\n".join(parts)


def _build_content_user_prompt(
    content_type: str, title: str, context: str,
    date_start: str | None, date_end: str | None,
) -> str:
    lines = []
    if title:
        lines.append(f"제목: {title}")
    if date_start or date_end:
        lines.append(f"기간: {date_start or '?'} ~ {date_end or '?'}")
    if context:
        lines.append(f"참고 맥락 / 추가 지시:\n{context}")
    lines.append("\n위 정보를 바탕으로 Markdown 형식의 글을 작성해줘.")
    return "\n".join(lines)


@celery_app.task
def learn_velog_style(user_id: str):
    """Analyze user's Velog posts and learn their writing style."""
    db = SessionLocal()
    try:
        from app.models.blog_post import BlogPost
        from app.models.user_profile import UserProfile
        import httpx
        import feedparser

        # Get user's velog ID
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not user_profile or not user_profile.velog_id:
            return {"error": "Velog ID not configured"}

        clean_id = user_profile.velog_id.lstrip("@")

        # Fetch RSS with full content
        try:
            resp = httpx.get(f"https://api.velog.io/rss/@{clean_id}", timeout=30.0)
            resp.raise_for_status()
        except Exception as e:
            return {"error": f"Failed to fetch Velog RSS: {str(e)}"}

        feed = feedparser.parse(resp.text)
        if not hasattr(feed, "entries") or len(feed.entries) == 0:
            return {"error": "No blog posts found"}

        # Collect post samples (up to 5 most recent with content)
        samples = []
        for entry in feed.entries[:5]:
            title = entry.get("title", "")
            # RSS description/content contains the post body
            body = entry.get("description", "") or entry.get("content", [{}])[0].get("value", "")
            # Strip HTML tags for cleaner analysis
            import re
            clean_body = re.sub(r"<[^>]+>", "", body)[:2000]
            if clean_body:
                samples.append(f"### {title}\n{clean_body}")

        if not samples:
            return {"error": "No post content available for analysis"}

        combined_samples = "\n\n---\n\n".join(samples)

        # Use LLM to analyze writing style
        api_key, model = _get_user_llm_key(db, user_id)
        from merge_core.llm import generate_text

        system_prompt = """너는 블로그 글쓰기 스타일 분석 전문가다.
사용자의 블로그 글 샘플을 분석하여, 다른 AI가 이 사용자의 스타일로 글을 쓸 수 있도록 하는 '스타일 프롬프트'를 생성해야 한다.

분석할 항목:
1. 문체/어투 (존댓말/반말, 격식 수준)
2. 글 구조 패턴 (서론-본론-결론, 이미지 활용, 코드 블록 스타일 등)
3. 자주 사용하는 표현이나 관용구
4. 기술 용어 사용 방식 (한글화 vs 영어 그대로)
5. 독자와의 소통 방식 (질문형, 설명형 등)
6. 특이한 습관이나 패턴

결과물은 다른 AI 모델에게 줄 '시스템 프롬프트' 형태로 작성해라.
"이 사용자의 블로그 스타일로 글을 작성해라. 스타일 특성은 다음과 같다:"로 시작해라.
한국어로 작성하고, 500자 내외로 간결하게 정리해라."""

        user_prompt = f"""다음은 사용자 @{clean_id}의 최근 블로그 글 {len(samples)}개입니다.
이 글들을 분석하여 사용자의 글쓰기 스타일 프롬프트를 생성해주세요.

{combined_samples}"""

        learned_prompt = generate_text(system_prompt, user_prompt, model=model, api_key=api_key)

        # Save to StyleProfile
        style = db.query(StyleProfile).filter(StyleProfile.user_id == user_id).first()
        if not style:
            style = StyleProfile(
                user_id=user_id,
                language="ko",
                tone="technical",
                blog_structure=["Intro", "Problem", "Approach", "Result", "Next"],
                report_structure=["Summary", "What I did", "Learned", "Next"],
            )
            db.add(style)

        style.learned_style_prompt = learned_prompt
        style.learned_at = datetime.utcnow()
        db.commit()

        return {"status": "success", "learned_prompt": learned_prompt}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task
def generate_coach_analysis(user_id: str):
    """Analyze user's solved.ac problems and provide coaching insights."""
    db = SessionLocal()
    try:
        from app.models.problem import Problem
        from sqlalchemy import func

        problems = db.query(Problem).filter(Problem.user_id == user_id).all()
        if not problems:
            return {"error": "No solved problems found"}

        # Aggregate stats
        total = len(problems)
        by_level = {}
        all_tags = {}
        for p in problems:
            lvl = p.level or 0
            by_level[lvl] = by_level.get(lvl, 0) + 1
            for tag in (p.tags or []):
                all_tags[tag] = all_tags.get(tag, 0) + 1

        # Sort tags by count
        sorted_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)
        top_tags = sorted_tags[:10]
        weak_tags = [t for t, c in sorted_tags if c <= 2][:10]

        stats_text = f"""총 풀이 수: {total}
난이도별 분포: {dict(sorted(by_level.items()))}
자주 푸는 유형 (상위 10): {top_tags}
적게 푸는 유형 (2문제 이하): {weak_tags}"""

        api_key, model = _get_user_llm_key(db, user_id)
        from merge_core.llm import generate_text

        system_prompt = """너는 알고리즘 코딩 코치이자 CS 교육 전문가다.
사용자의 solved.ac 문제 풀이 데이터를 분석하여 맞춤형 조언을 제공한다.

다음 형식으로 분석 결과를 작성해라:

## 🏆 현재 실력 요약
(전체적인 수준 평가)

## 💪 강점 분야
(잘하는 알고리즘 유형과 왜 강점인지)

## 🎯 보완이 필요한 분야
(부족한 부분과 구체적인 개선 방법)

## 📚 추천 학습 로드맵
(단계별로 어떤 유형의 문제를 풀면 좋을지)

## 💡 오늘의 도전 과제
(바로 도전할 만한 문제 유형 3가지)

한국어로 작성하고, 실질적이고 구체적인 조언을 해라."""

        user_prompt = f"""다음은 사용자의 알고리즘 문제 풀이 통계입니다:

{stats_text}

이 데이터를 바탕으로 맞춤형 코딩 코치 분석을 해주세요."""

        analysis = generate_text(system_prompt, user_prompt, model=model, api_key=api_key)

        # Store as generated content
        content = GeneratedContent(
            user_id=user_id,
            content_type="coach_analysis",
            title="알고리즘 코칭 분석",
            content=analysis,
            status="completed",
            metadata={"total_problems": total, "top_tags": dict(top_tags)},
        )
        db.add(content)
        db.commit()

        return {"status": "success", "content_id": str(content.id), "analysis": analysis}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task
def generate_coach_quiz(user_id: str, topic: str = ""):
    """Generate a coding quiz targeting weak areas."""
    db = SessionLocal()
    try:
        from app.models.problem import Problem

        problems = db.query(Problem).filter(Problem.user_id == user_id).all()
        all_tags = {}
        for p in problems:
            for tag in (p.tags or []):
                all_tags[tag] = all_tags.get(tag, 0) + 1

        sorted_tags = sorted(all_tags.items(), key=lambda x: x[1])
        weak_areas = [t for t, c in sorted_tags[:5]]
        target = topic if topic else ", ".join(weak_areas) if weak_areas else "일반 알고리즘"

        api_key, model = _get_user_llm_key(db, user_id)
        from merge_core.llm import generate_text

        system_prompt = """너는 알고리즘 퀴즈 출제자다. 사용자의 취약 분야를 기반으로 학습에 도움이 되는 퀴즈를 출제한다.

다음 형식으로 퀴즈 3문제를 출제해라:

## 퀴즈 1: (난이도)
**문제:** (문제 설명)
**힌트:** (접근 방법 힌트)

<details>
<summary>정답 보기</summary>

**풀이:** (상세한 풀이 과정)
**핵심 개념:** (이 문제에서 배울 수 있는 핵심 개념)
**유사 문제 추천:** (백준/프로그래머스 문제 번호)
</details>

각 문제는 서로 다른 난이도(쉬움/보통/어려움)로 출제해라.
한국어로 작성하고, 실제 코딩 인터뷰에 나올 법한 실용적인 문제를 내라."""

        user_prompt = f"""타겟 주제: {target}
현재 풀이 통계: {dict(list(all_tags.items())[:15])}

이 사용자의 취약 분야를 보완할 수 있는 퀴즈 3문제를 출제해주세요."""

        quiz = generate_text(system_prompt, user_prompt, model=model, api_key=api_key)

        content = GeneratedContent(
            user_id=user_id,
            content_type="coach_quiz",
            title=f"코딩 퀴즈 — {target}",
            content=quiz,
            status="completed",
            metadata={"topic": target},
        )
        db.add(content)
        db.commit()

        return {"status": "success", "content_id": str(content.id), "quiz": quiz}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task
def generate_resume(user_id: str, resume_type: str = "resume", extra_context: str = ""):
    """Generate resume or cover letter from portfolio data."""
    db = SessionLocal()
    try:
        from app.models.repo import Repo
        from app.models.commit import Commit
        from app.models.problem import Problem
        from app.models.blog_post import BlogPost
        from app.models.user_profile import UserProfile
        from sqlalchemy import func, desc

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}

        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

        # Gather portfolio data
        repos = db.query(Repo).filter(Repo.user_id == user_id).order_by(desc(Repo.stars)).limit(10).all()
        total_commits = db.query(func.count(Commit.id)).filter(Commit.user_id == user_id).scalar() or 0
        total_problems = db.query(func.count(Problem.id)).filter(Problem.user_id == user_id).scalar() or 0
        total_blogs = db.query(func.count(BlogPost.id)).filter(BlogPost.user_id == user_id).scalar() or 0

        # Language stats
        lang_stats = {}
        for r in repos:
            if r.language:
                lang_stats[r.language] = lang_stats.get(r.language, 0) + 1

        # Problem tags
        problems = db.query(Problem).filter(Problem.user_id == user_id).all()
        tag_counts = {}
        for p in problems:
            for t in (p.tags or []):
                tag_counts[t] = tag_counts.get(t, 0) + 1

        portfolio_text = f"""이름: {profile.portfolio_name or user.name or "개발자"}
이메일: {profile.portfolio_email or user.email}
자기소개: {profile.portfolio_bio or ""}

GitHub 프로젝트 ({len(repos)}개):
""" + "\n".join([
            f"- {r.full_name}: {r.description or '설명 없음'} ({r.language or '?'}, ⭐{r.stars or 0})"
            for r in repos
        ]) + f"""

총 커밋 수: {total_commits}
알고리즘 풀이 수: {total_problems}
블로그 글 수: {total_blogs}
주요 언어: {dict(sorted(lang_stats.items(), key=lambda x: x[1], reverse=True)[:5])}
알고리즘 유형: {dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10])}"""

        api_key, model = _get_user_llm_key(db, user_id)
        from merge_core.llm import generate_text

        if resume_type == "cover_letter":
            system_prompt = """너는 IT/개발자 채용 전문 자기소개서 작성 도우미다.
사용자의 포트폴리오 데이터를 기반으로 실제 채용에 사용할 수 있는 자기소개서를 작성한다.

다음 구조로 작성해라:
## 자기소개서

### 1. 성장 과정 및 지원 동기
(개발을 시작하게 된 계기와 성장 과정)

### 2. 기술 역량
(주요 기술 스택과 프로젝트 경험을 구체적으로)

### 3. 프로젝트 경험
(가장 의미 있는 프로젝트 2-3개 상세 설명)

### 4. 성장 가능성
(자기 계발 노력과 앞으로의 계획)

한국어로, 구체적인 수치와 경험을 포함하여 작성해라. 분량은 1000-1500자."""
        else:
            system_prompt = """너는 IT/개발자 이력서 작성 전문가다.
사용자의 포트폴리오 데이터를 기반으로 깔끔하고 전문적인 이력서를 Markdown 형식으로 작성한다.

다음 구조로 작성해라:
# 이력서

## 인적사항
(이름, 이메일, GitHub 등)

## 기술 스택
(프로그래밍 언어, 프레임워크, 도구 등을 숙련도 순으로)

## 프로젝트 경험
(각 프로젝트: 이름, 설명, 기술 스택, 주요 기여, 결과/성과)

## 알고리즘/PS
(solved.ac 통계, 주요 알고리즘 유형)

## 기술 블로그
(블로그 활동 소개)

한국어로, 실제 채용 시장에서 통하는 형식으로 작성해라."""

        user_prompt = f"""{portfolio_text}

{f"추가 요청사항: {extra_context}" if extra_context else ""}

위 정보를 바탕으로 {'자기소개서' if resume_type == 'cover_letter' else '이력서'}를 작성해주세요."""

        result = generate_text(system_prompt, user_prompt, model=model, api_key=api_key)

        content = GeneratedContent(
            user_id=user_id,
            content_type=resume_type,
            title="이력서" if resume_type == "resume" else "자기소개서",
            content=result,
            status="completed",
            metadata={"resume_type": resume_type},
        )
        db.add(content)
        db.commit()

        return {"status": "success", "content_id": str(content.id), "content": result}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()
