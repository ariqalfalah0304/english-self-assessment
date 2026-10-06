"""
Admin Dashboard and User Analytics Service for English Self-Assessment.
Handles:
- Aggregating dashboard overview metrics (users, attempts, questions, category breakdown)
- Generating interactive Plotly charts (category distribution, difficulty breakdown)
- Searching and retrieving user directories with assessment performance
- Loading detailed user history
- Filtering assessment results by category, level, and date
- Enforcing read-only data access (admins cannot modify participant scores)
"""

from typing import Optional, Any
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

from database.db import get_connection
from database.models import User
from database import queries


def fetch_dashboard_summary(db_path: Optional[str | Path] = None) -> dict[str, Any]:
    """
    Retrieve top-level statistics and aggregated breakdowns for the Admin Dashboard.
    """
    with get_connection(db_path) as conn:
        return queries.get_dashboard_metrics(conn)


def fetch_users_directory(
    search_query: Optional[str] = None,
    db_path: Optional[str | Path] = None,
) -> list[dict[str, Any]]:
    """
    Retrieve registered participants with aggregated attempt counters and average scores.
    """
    with get_connection(db_path) as conn:
        return queries.get_users_with_stats(conn, search_query=search_query)


def fetch_user_details_and_history(
    user_id: int,
    db_path: Optional[str | Path] = None,
) -> tuple[Optional[User], list[dict[str, Any]]]:
    """
    Retrieve participant profile record alongside full assessment attempt logs.
    """
    with get_connection(db_path) as conn:
        user = queries.get_user_by_id(conn, user_id)
        history = queries.get_user_assessment_history(conn, user_id)
        return user, history


def delete_user_account(
    user_id: int,
    db_path: Optional[str | Path] = None,
) -> bool:
    """
    Permanently delete a participant account and associated attempt logs.
    """
    with get_connection(db_path) as conn:
        return queries.delete_user(conn, user_id)


def fetch_assessment_results(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 200,
    db_path: Optional[str | Path] = None,
) -> list[dict[str, Any]]:
    """
    Retrieve historical attempts filtered by category, level, or date range.
    Read-only operation; scores cannot be modified through this view.
    """
    with get_connection(db_path) as conn:
        return queries.get_filtered_attempts(
            conn=conn,
            category=category,
            difficulty=difficulty,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )


# ==========================================
# PLOTLY CHART BUILDERS
# ==========================================

def build_category_distribution_chart(category_counts: dict[str, int]) -> go.Figure:
    """
    Generate an interactive Plotly donut chart showing attempt distribution across categories.
    """
    labels = list(category_counts.keys())
    values = list(category_counts.values())

    # Curated theme colors for categories: Grammar (Indigo), Reading (Emerald), Listening (Amber)
    color_map = {
        "Grammar": "#4F46E5",
        "Reading": "#059669",
        "Listening": "#D97706",
    }
    colors = [color_map.get(label, "#3B82F6") for label in labels]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
                textinfo="label+percent+value",
                hoverinfo="label+value+percent",
            )
        ]
    )
    fig.update_layout(
        title=dict(text="<b>Attempts by Category</b>", font=dict(size=16, color="#1E293B")),
        margin=dict(t=45, b=20, l=20, r=20),
        height=320,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def build_difficulty_distribution_chart(difficulty_counts: dict[str, int]) -> go.Figure:
    """
    Generate an interactive Plotly bar chart displaying attempt volume by difficulty level.
    """
    order = ["Easy", "Medium", "Hard"]
    labels = [d for d in order if d in difficulty_counts or True]
    values = [difficulty_counts.get(d, 0) for d in labels]
    colors = ["#16A34A", "#EAB308", "#DC2626"]  # Green, Yellow, Red

    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker=dict(color=colors, line=dict(color="#FFFFFF", width=1.5)),
                text=values,
                textposition="auto",
                hoverinfo="x+y",
            )
        ]
    )
    fig.update_layout(
        title=dict(text="<b>Attempts by Difficulty Level</b>", font=dict(size=16, color="#1E293B")),
        xaxis=dict(title="Difficulty Level", showgrid=False),
        yaxis=dict(title="Number of Attempts", showgrid=True, gridcolor="#E2E8F0"),
        margin=dict(t=45, b=20, l=20, r=20),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig
