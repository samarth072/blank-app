"""AI integration using Google Gemini API."""

from __future__ import annotations

import google.generativeai as genai

from config.settings import load_config


def get_model() -> genai.GenerativeModel:
    config = load_config()
    genai.configure(api_key=config.gemini_api_key)
    return genai.GenerativeModel(config.llm_model)


def generate(prompt: str, max_tokens: int = 4096) -> str:
    model = get_model()
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.3,
        ),
    )
    return response.text


def score_job(job_description: str, profile_summary: str) -> tuple[int, str]:
    """Score a job 1-10 against a candidate profile. Returns (score, rationale)."""
    prompt = f"""You are an expert job-matching AI. Score how well this candidate matches the job on a scale of 1-10.

SCORING GUIDE:
- 9-10: Strong match — meets nearly all requirements, highly relevant experience
- 7-8: Good match — meets most requirements, relevant background
- 5-6: Moderate match — meets some requirements, transferable skills
- 1-4: Weak match — missing key qualifications

CANDIDATE PROFILE:
{profile_summary}

JOB DESCRIPTION:
{job_description}

Respond in EXACTLY this format (no extra text):
SCORE: <number 1-10>
RATIONALE: <2-3 sentence explanation>"""

    response = generate(prompt, max_tokens=300)
    lines = response.strip().split("\n")

    score = 5
    rationale = ""
    for line in lines:
        if line.startswith("SCORE:"):
            try:
                score = int(line.split(":")[1].strip())
                score = max(1, min(10, score))
            except (ValueError, IndexError):
                score = 5
        elif line.startswith("RATIONALE:"):
            rationale = line.split(":", 1)[1].strip()

    return score, rationale


def tailor_resume(resume_text: str, job_description: str, resume_facts: list[str]) -> str:
    """Generate a tailored resume for a specific job."""
    facts_str = "\n".join(f"- {f}" for f in resume_facts) if resume_facts else "No specific facts provided."

    prompt = f"""You are an expert resume writer. Tailor this resume for the specific job below.

RULES:
1. Reorganize and emphasize experience relevant to this job
2. Incorporate keywords from the job description naturally
3. Preserve all factual information — NEVER fabricate experience, skills, or metrics
4. Keep the same overall structure (contact info, summary, experience, education, skills)
5. Make the summary specific to this role
6. Highlight relevant projects and achievements

RESUME FACTS (must be preserved exactly):
{facts_str}

ORIGINAL RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Return the tailored resume in clean markdown format."""

    return generate(prompt, max_tokens=3000)


def generate_cover_letter(
    profile_summary: str,
    job_title: str,
    company: str,
    job_description: str,
) -> str:
    """Generate a targeted cover letter."""
    prompt = f"""Write a professional, targeted cover letter for this specific job application.

RULES:
1. Address the specific company and role by name
2. Map the candidate's experience directly to job requirements
3. Be specific — reference actual skills, projects, and achievements from the profile
4. Keep it concise — 3-4 paragraphs, under 400 words
5. Professional but genuine tone — avoid generic filler phrases
6. Never fabricate experience or qualifications

CANDIDATE PROFILE:
{profile_summary}

JOB TITLE: {job_title}
COMPANY: {company}

JOB DESCRIPTION:
{job_description}

Write the cover letter now."""

    return generate(prompt, max_tokens=1500)


def extract_job_description(html_text: str) -> str:
    """Use AI to extract a clean job description from messy HTML/text."""
    prompt = f"""Extract the job description from the following webpage content.
Return ONLY the job-relevant information: title, company, location, responsibilities, requirements, qualifications, benefits, and salary if available.
Remove navigation, ads, footers, and other irrelevant content.
Format cleanly in markdown.

WEBPAGE CONTENT:
{html_text[:8000]}"""

    return generate(prompt, max_tokens=2000)
