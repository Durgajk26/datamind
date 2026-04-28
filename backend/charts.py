"""
Chart Generation Engine
------------------------
Automatically generates interactive Plotly charts
based on data types and AI recommendations.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json


def fig_to_json(fig) -> str:
    """Convert Plotly figure to JSON for frontend."""
    return fig.to_json()


def auto_generate_charts(df: pd.DataFrame) -> list[dict]:
    """
    Automatically generate the most relevant charts for a dataset.
    Detects column types and picks appropriate chart types.
    Returns list of chart JSONs.
    """
    charts = []
    numeric_cols     = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

    # Chart 1: Distribution of first numeric column
    if numeric_cols:
        col = numeric_cols[0]
        fig = px.histogram(
            df, x=col,
            title=f"Distribution of {col}",
            template="plotly_white",
            color_discrete_sequence=["#6366f1"]
        )
        fig.update_layout(bargap=0.1)
        charts.append({
            "title": f"Distribution of {col}",
            "type":  "histogram",
            "json":  fig_to_json(fig)
        })

    # Chart 2: Bar chart of top categorical column
    if categorical_cols and numeric_cols:
        cat_col  = categorical_cols[0]
        num_col  = numeric_cols[0]
        n_unique = df[cat_col].nunique()

        if n_unique <= 20:
            grouped = df.groupby(cat_col)[num_col].mean().reset_index()
            grouped = grouped.sort_values(num_col, ascending=False).head(15)
            fig = px.bar(
                grouped, x=cat_col, y=num_col,
                title=f"Average {num_col} by {cat_col}",
                template="plotly_white",
                color=num_col,
                color_continuous_scale="Viridis"
            )
            charts.append({
                "title": f"Average {num_col} by {cat_col}",
                "type":  "bar",
                "json":  fig_to_json(fig)
            })

    # Chart 3: Correlation heatmap
    if len(numeric_cols) >= 3:
        corr = df[numeric_cols[:10]].corr()
        fig  = px.imshow(
            corr,
            title="Correlation Heatmap",
            template="plotly_white",
            color_continuous_scale="RdBu",
            aspect="auto"
        )
        charts.append({
            "title": "Correlation Heatmap",
            "type":  "heatmap",
            "json":  fig_to_json(fig)
        })

    # Chart 4: Scatter plot of top 2 correlated numeric columns
    if len(numeric_cols) >= 2:
        corr      = df[numeric_cols].corr()
        corr_vals = corr.to_numpy().copy()
        np.fill_diagonal(corr_vals, 0)
        idx  = np.unravel_index(np.argmax(np.abs(corr_vals)), corr_vals.shape)
        col1 = numeric_cols[idx[0]]
        col2 = numeric_cols[idx[1]]

        color_col = None
        if categorical_cols and df[categorical_cols[0]].nunique() <= 10:
            color_col = categorical_cols[0]

        fig = px.scatter(
            df, x=col1, y=col2,
            title=f"{col1} vs {col2}",
            template="plotly_white",
            color=color_col,
            opacity=0.7,
            trendline="ols" if not color_col else None
        )
        charts.append({
            "title": f"{col1} vs {col2} Scatter",
            "type":  "scatter",
            "json":  fig_to_json(fig)
        })

    # Chart 5: Box plots for numeric columns
    if len(numeric_cols) >= 2:
        cols_to_plot = numeric_cols[:6]
        fig = go.Figure()
        for col in cols_to_plot:
            fig.add_trace(go.Box(y=df[col].dropna(), name=col))
        fig.update_layout(
            title="Distribution Overview (Box Plots)",
            template="plotly_white",
            showlegend=False
        )
        charts.append({
            "title": "Distribution Overview",
            "type":  "box",
            "json":  fig_to_json(fig)
        })

    # Chart 6: Pie chart for categorical column
    if categorical_cols:
        cat_col  = categorical_cols[0]
        n_unique = df[cat_col].nunique()
        if 2 <= n_unique <= 10:
            vc  = df[cat_col].value_counts().head(8)
            fig = px.pie(
                values=vc.values,
                names=vc.index,
                title=f"Breakdown by {cat_col}",
                template="plotly_white",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            charts.append({
                "title": f"Breakdown by {cat_col}",
                "type":  "pie",
                "json":  fig_to_json(fig)
            })

    return charts


def generate_custom_chart(df: pd.DataFrame, chart_type: str,
                           x_col: str, y_col: str, title: str) -> str:
    """
    Generate a specific chart based on user/AI request.
    Returns Plotly JSON.
    """
    try:
        if chart_type == "bar":
            if df[x_col].nunique() <= 30:
                grouped = df.groupby(x_col)[y_col].mean().reset_index()
                fig = px.bar(
                    grouped, x=x_col, y=y_col,
                    title=title, template="plotly_white",
                    color_discrete_sequence=["#6366f1"]
                )
            else:
                fig = px.bar(
                    df.head(30), x=x_col, y=y_col,
                    title=title, template="plotly_white"
                )

        elif chart_type == "line":
            fig = px.line(
                df, x=x_col, y=y_col,
                title=title, template="plotly_white",
                color_discrete_sequence=["#6366f1"]
            )

        elif chart_type == "scatter":
            fig = px.scatter(
                df, x=x_col, y=y_col,
                title=title, template="plotly_white",
                opacity=0.7,
                color_discrete_sequence=["#6366f1"]
            )

        elif chart_type == "histogram":
            fig = px.histogram(
                df, x=x_col,
                title=title, template="plotly_white",
                color_discrete_sequence=["#6366f1"]
            )

        elif chart_type == "pie":
            vc  = df[x_col].value_counts().head(8)
            fig = px.pie(
                values=vc.values, names=vc.index,
                title=title, template="plotly_white"
            )

        else:
            fig = px.bar(
                df.head(20), x=x_col, y=y_col,
                title=title, template="plotly_white"
            )

        return fig_to_json(fig)

    except Exception as e:
        fig = go.Figure()
        fig.update_layout(title=f"Could not generate chart: {str(e)}")
        return fig_to_json(fig)