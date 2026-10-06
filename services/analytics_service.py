"""
Admin Question Performance Analytics Service (Phase 16).
Calculates per-question empirical metrics:
- attempts
- correct count
- incorrect count
- accuracy percentage

Provides:
- Most frequently attempted questions
- Highest accuracy questions
- Lowest accuracy questions
- Filtering by category, topic, and difficulty
- Separate presentation of assigned difficulty vs observed performance
- Admin review notes when observed variance justifies review (without automated changes or unsupported quality claims)
- Plotly visualization builders
"""

from typing import Optional, Any
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px

from database.db import get_connection
from database import queries


NO_DATA_NOTE = "No participant response data recorded yet."
HAS_DATA_NOTE = "Empirical accuracy calculated from participant responses."


def fetch_question_analytics(
    category: Optional[str] = None,
    topic: Optional[str] = None,
    skill_number: Optional[int] = None,
    status: str = "Active",
    db_path: Optional[str | Path] = None,
) -> list[dict[str, Any]]:
    """
    Retrieve question performance analytics with per-item response stats.
    """
    with get_connection(db_path) as conn:
        items = queries.get_question_analytics_data(
            conn=conn,
            category=category,
            topic=topic,
            skill_number=skill_number,
            status=status,
        )

    for item in items:
        if item["attempts"] < 1:
            item["admin_note"] = NO_DATA_NOTE
            item["needs_review"] = False
        else:
            item["admin_note"] = f"Accuracy: {item['accuracy']}% from {item['attempts']} attempt(s)."
            # Flag item if accuracy is very low (< 40%) with at least 2 attempts
            item["needs_review"] = (item["attempts"] >= 2 and item["accuracy"] < 40.0)

    return items


def get_top_frequently_attempted(
    items: list[dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Return questions with the highest number of attempts."""
    return sorted(items, key=lambda x: (x["attempts"], x["accuracy"]), reverse=True)[:limit]


def get_highest_accuracy_questions(
    items: list[dict[str, Any]],
    min_attempts: int = 1,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Return questions with the highest accuracy among attempted questions."""
    attempted = [x for x in items if x["attempts"] >= min_attempts]
    return sorted(attempted, key=lambda x: (x["accuracy"], x["attempts"]), reverse=True)[:limit]


def get_lowest_accuracy_questions(
    items: list[dict[str, Any]],
    min_attempts: int = 1,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Return questions with the lowest accuracy among attempted questions."""
    attempted = [x for x in items if x["attempts"] >= min_attempts]
    return sorted(attempted, key=lambda x: (x["accuracy"], -x["attempts"]))[:limit]


# ==========================================
# PLOTLY VISUALIZATIONS
# ==========================================

def build_accuracy_distribution_chart(items: list[dict[str, Any]]) -> go.Figure:
    """Build histogram showing distribution of question accuracy percentages."""
    attempted = [x for x in items if x["attempts"] > 0]
    if not attempted:
        fig = go.Figure()
        fig.add_annotation(text="No attempted question data available yet", showarrow=False, font=dict(size=14, color="#64748B"))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
        return fig

    accuracies = [x["accuracy"] for x in attempted]
    fig = px.histogram(
        x=accuracies,
        nbins=10,
        labels={"x": "Observed Accuracy (%)"},
        title="Distribution of Question Accuracy",
        color_discrete_sequence=["#3B82F6"],
    )
    fig.update_layout(
        bargap=0.08,
        yaxis_title="Question Count",
        xaxis_title="Observed Accuracy (%)",
        xaxis=dict(range=[0, 105]),
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
    )
    return fig


def build_attempts_vs_accuracy_scatter(items: list[dict[str, Any]]) -> go.Figure:
    """Build scatter plot of Attempts vs Accuracy, categorized by Category."""
    attempted = [x for x in items if x["attempts"] > 0]
    if not attempted:
        fig = go.Figure()
        fig.add_annotation(text="No attempted question data available yet", showarrow=False, font=dict(size=14, color="#64748B"))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
        return fig

    color_map = {"Grammar": "#4F46E5", "Reading": "#059669", "Listening": "#D97706"}

    fig = px.scatter(
        data_frame=attempted,
        x="attempts",
        y="accuracy",
        color="category",
        hover_data=["id", "category", "skill_number", "skill_name", "correct_count", "incorrect_count"],
        color_discrete_map=color_map,
        labels={
            "attempts": "Total Attempts",
            "accuracy": "Observed Accuracy (%)",
            "category": "Category",
        },
        title="Attempts vs. Observed Accuracy by Category",
    )
    fig.update_traces(marker=dict(size=10, opacity=0.85, line=dict(width=1, color="DarkSlateGrey")))
    fig.update_layout(
        yaxis=dict(range=[0, 105], title="Observed Accuracy (%)"),
        xaxis=dict(title="Total Attempts"),
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def build_top_bottom_accuracy_chart(
    top_items: list[dict[str, Any]],
    bottom_items: list[dict[str, Any]],
) -> go.Figure:
    """Build horizontal comparison bar chart of highest vs lowest accuracy questions."""
    if not top_items and not bottom_items:
        fig = go.Figure()
        fig.add_annotation(text="No attempted question data available yet", showarrow=False, font=dict(size=14, color="#64748B"))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
        return fig

    labels = []
    scores = []
    colors = []

    # Highest accuracy items
    for item in top_items[:4]:
        qid = f"Q#{item['id']} ({item['category'][:4]})"
        labels.append(qid)
        scores.append(item["accuracy"])
        colors.append("#10B981")  # green

    # Lowest accuracy items
    for item in bottom_items[:4]:
        qid = f"Q#{item['id']} ({item['category'][:4]})"
        if qid not in labels:
            labels.append(qid)
            scores.append(item["accuracy"])
            colors.append("#EF4444")  # red

    fig = go.Figure(go.Bar(
        x=scores,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{s:.1f}%" for s in scores],
        textposition="outside",
    ))
    fig.update_layout(
        title="High vs. Low Accuracy Questions (Top & Bottom)",
        xaxis=dict(range=[0, 115], title="Observed Accuracy (%)"),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
    )
    return fig
