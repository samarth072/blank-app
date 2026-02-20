"""Resume parsing utilities."""

from __future__ import annotations

import io

from models.schemas import Profile


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text content from a PDF file."""
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(pdf_bytes))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n".join(text_parts)
    except Exception as e:
        return f"Error extracting PDF text: {e}"


def build_profile_summary(profile: Profile) -> str:
    """Build a text summary of the profile for AI prompts."""
    parts = []

    if profile.summary:
        parts.append(f"Summary: {profile.summary}")

    if profile.skills:
        parts.append(f"Skills: {', '.join(profile.skills)}")

    parts.append(f"Years of experience: {profile.years_of_experience}")

    if profile.work_experience:
        parts.append("\nWork Experience:")
        for exp in profile.work_experience:
            parts.append(f"  - {exp.title} at {exp.company} ({exp.start_date} - {exp.end_date})")
            if exp.description:
                parts.append(f"    {exp.description}")
            for h in exp.highlights:
                parts.append(f"    * {h}")

    if profile.education:
        parts.append("\nEducation:")
        for edu in profile.education:
            parts.append(f"  - {edu.degree} in {edu.field} from {edu.institution}")

    if profile.resume_facts:
        parts.append("\nKey Facts:")
        for fact in profile.resume_facts:
            parts.append(f"  - {fact}")

    if profile.work_authorization:
        parts.append(f"\nWork Authorization: {profile.work_authorization}")

    if profile.desired_salary_min and profile.desired_salary_max:
        parts.append(f"Desired Salary: ${profile.desired_salary_min:,} - ${profile.desired_salary_max:,}")

    return "\n".join(parts)
