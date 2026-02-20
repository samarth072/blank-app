"""Dashboard page — view pipeline results and job details."""

import streamlit as st

st.set_page_config(page_title="ApplyPilot - Dashboard", page_icon="🚀", layout="wide")

from models.schemas import JobStatus
from utils.storage import compute_stats, load_jobs

st.title("Dashboard")

jobs = load_jobs()

if not jobs:
    st.info("No jobs in the pipeline yet. Run the pipeline first!")
    st.stop()

# ── Stats Overview ────────────────────────────────────────────
stats = compute_stats()

st.subheader("Pipeline Statistics")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Discovered", stats.total_discovered)
c2.metric("Enriched", stats.total_enriched)
c3.metric("Scored", stats.total_scored)
c4.metric("Above Threshold", stats.total_above_threshold)
c5.metric("Applied", stats.total_applied)
c6.metric("Avg Score", stats.avg_score)

st.markdown("---")

# ── Score Distribution ────────────────────────────────────────
scored_jobs = [j for j in jobs if j.score is not None and j.score > 0]

if scored_jobs:
    st.subheader("Score Distribution")

    try:
        import plotly.express as px

        scores = [j.score for j in scored_jobs]
        fig = px.histogram(
            x=scores,
            nbins=10,
            labels={"x": "Match Score", "y": "Number of Jobs"},
            color_discrete_sequence=["#4CAF50"],
        )
        fig.update_layout(
            xaxis=dict(dtick=1, range=[0.5, 10.5]),
            bargap=0.1,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        # Fallback without plotly
        score_counts = {}
        for j in scored_jobs:
            s = int(j.score)
            score_counts[s] = score_counts.get(s, 0) + 1
        st.bar_chart(score_counts)

# ── Status Breakdown ──────────────────────────────────────────
st.subheader("Jobs by Status")

try:
    import plotly.express as px

    status_counts = {}
    for j in jobs:
        status_counts[j.status.value] = status_counts.get(j.status.value, 0) + 1

    fig = px.pie(
        names=list(status_counts.keys()),
        values=list(status_counts.values()),
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    st.plotly_chart(fig, use_container_width=True)
except ImportError:
    status_counts = {}
    for j in jobs:
        status_counts[j.status.value] = status_counts.get(j.status.value, 0) + 1
    for status, count in sorted(status_counts.items()):
        st.write(f"**{status}**: {count}")

st.markdown("---")

# ── Source Breakdown ──────────────────────────────────────────
st.subheader("Jobs by Source")

try:
    import plotly.express as px

    source_counts = {}
    for j in jobs:
        source_counts[j.source.value] = source_counts.get(j.source.value, 0) + 1

    fig = px.bar(
        x=list(source_counts.keys()),
        y=list(source_counts.values()),
        labels={"x": "Source", "y": "Count"},
        color_discrete_sequence=["#2196F3"],
    )
    st.plotly_chart(fig, use_container_width=True)
except ImportError:
    source_counts = {}
    for j in jobs:
        source_counts[j.source.value] = source_counts.get(j.source.value, 0) + 1
    for source, count in sorted(source_counts.items()):
        st.write(f"**{source}**: {count}")

st.markdown("---")

# ── Top Matches ───────────────────────────────────────────────
st.subheader("Top Matches")

top_jobs = sorted(
    [j for j in jobs if j.score is not None],
    key=lambda j: j.score or 0,
    reverse=True,
)[:20]

if top_jobs:
    for job in top_jobs:
        score_color = "green" if (job.score or 0) >= 8 else "orange" if (job.score or 0) >= 6 else "red"
        with st.expander(
            f"{'🟢' if (job.score or 0) >= 8 else '🟡' if (job.score or 0) >= 6 else '🔴'} "
            f"[{job.score}/10] {job.title} — {job.company} ({job.status.value})"
        ):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Title:** {job.title}")
                st.markdown(f"**Company:** {job.company}")
                st.markdown(f"**Location:** {job.location}")
                st.markdown(f"**Source:** {job.source.value}")
                if job.salary:
                    st.markdown(f"**Salary:** {job.salary}")
                if job.url:
                    st.markdown(f"**URL:** [{job.url[:60]}...]({job.url})")

            with col2:
                st.markdown(f"**Score:** {job.score}/10")
                st.markdown(f"**Status:** {job.status.value}")
                if job.date_posted:
                    st.markdown(f"**Posted:** {job.date_posted}")

            if job.score_rationale:
                st.markdown(f"**Score Rationale:** {job.score_rationale}")

            if job.description:
                with st.expander("Job Description"):
                    st.markdown(job.description[:3000])

            if job.tailored_resume:
                with st.expander("Tailored Resume"):
                    st.markdown(job.tailored_resume)

            if job.cover_letter:
                with st.expander("Cover Letter"):
                    st.markdown(job.cover_letter)
else:
    st.info("No scored jobs yet. Run the pipeline to see results.")

# ── All Jobs Table ────────────────────────────────────────────
st.markdown("---")
st.subheader("All Jobs")

filter_status = st.multiselect(
    "Filter by status",
    options=[s.value for s in JobStatus],
    default=[],
)

filtered = jobs if not filter_status else [j for j in jobs if j.status.value in filter_status]

if filtered:
    table_data = []
    for j in filtered:
        table_data.append({
            "Score": j.score or "-",
            "Title": j.title,
            "Company": j.company,
            "Location": j.location,
            "Source": j.source.value,
            "Status": j.status.value,
            "Salary": j.salary or "-",
        })

    st.dataframe(table_data, use_container_width=True)
    st.caption(f"Showing {len(filtered)} of {len(jobs)} jobs")
else:
    st.info("No jobs match the selected filters.")
