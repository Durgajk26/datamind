"""
AI Data Analysis Engine — Local & Private
------------------------------------------
Uses Ollama (local LLM) to analyse datasets.
100% private — no data leaves your machine.
No API keys, no costs, no rate limits.

Model: gemma3 (Google's open source model, runs locally)
"""

import json
import pandas as pd
import numpy as np
import ollama
from dotenv import load_dotenv

load_dotenv()

MODEL = "gemma3"


def safe_json(obj):
    """Convert numpy types to Python native for JSON serialisation."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return str(obj)
    return str(obj)


def get_dataframe_profile(df: pd.DataFrame) -> dict:
    """
    Generate a statistical profile of the dataframe.
    This is what we send to the LLM so it understands the data.
    """
    numeric_cols     = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_cols    = df.select_dtypes(include=["datetime"]).columns.tolist()

    profile = {
        "shape":               {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
        "columns":             df.columns.tolist(),
        "dtypes":              {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values":      {col: int(df[col].isna().sum()) for col in df.columns},
        "numeric_columns":     numeric_cols,
        "categorical_columns": categorical_cols,
        "datetime_columns":    datetime_cols,
    }

    # Stats for numeric columns
    if numeric_cols:
        desc = df[numeric_cols].describe()
        profile["numeric_stats"] = {
            col: {stat: safe_json(val) for stat, val in desc[col].items()}
            for col in numeric_cols
        }

    # Top values for categorical columns
    if categorical_cols:
        profile["categorical_stats"] = {}
        for col in categorical_cols[:5]:
            vc = df[col].value_counts().head(5)
            profile["categorical_stats"][col] = {
                str(k): int(v) for k, v in vc.items()
            }

    # Top correlations
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr()
        correlations = []
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                correlations.append({
                    "col1":        numeric_cols[i],
                    "col2":        numeric_cols[j],
                    "correlation": round(float(corr.iloc[i, j]), 3)
                })
        correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        profile["top_correlations"] = correlations[:5]

    # Sample rows
    profile["sample"] = df.head(3).to_dict(orient="records")

    return profile


def call_llm(prompt: str) -> str:
    """
    Call the local Ollama model.
    Returns the response text.
    """
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]


def clean_json_response(text: str) -> str:
    """
    Clean up LLM response to extract valid JSON.
    Local models sometimes wrap JSON in markdown.
    """
    text = text.strip()

    # Remove markdown code blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    # Find JSON object boundaries
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]

    return text.strip()


def generate_ai_insights(df: pd.DataFrame, filename: str) -> dict:
    """
    Analyse dataset and generate structured insights using local LLM.
    """
    profile = get_dataframe_profile(df)

    prompt = f"""You are an expert data analyst. Analyse this dataset and provide insights.

Dataset: {filename}
Profile: {json.dumps(profile, default=safe_json, indent=2)}

You MUST respond with ONLY a valid JSON object. No explanation, no markdown, no backticks.
Start your response with {{ and end with }}.

{{
    "dataset_description": "2-3 sentence description of what this dataset is about",
    "key_insights": [
        "specific insight with numbers from the data",
        "specific insight 2",
        "specific insight 3",
        "specific insight 4",
        "specific insight 5"
    ],
    "data_quality": {{
        "score": 85,
        "issues": ["issue 1", "issue 2"],
        "strengths": ["strength 1", "strength 2"]
    }},
    "recommended_analyses": [
        {{
            "title": "Analysis title",
            "description": "What this would reveal",
            "chart_type": "bar"
        }}
    ],
    "interesting_questions": [
        "Question 1?",
        "Question 2?",
        "Question 3?"
    ],
    "business_implications": "2-3 sentences on decision-making implications"
}}"""

    text = call_llm(prompt)
    text = clean_json_response(text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Return a safe fallback if JSON parsing fails
        return {
            "dataset_description": f"Dataset '{filename}' with {df.shape[0]} rows and {df.shape[1]} columns.",
            "key_insights": [
                f"Dataset contains {df.shape[0]:,} rows and {df.shape[1]} columns.",
                f"Numeric columns: {', '.join(df.select_dtypes(include=[np.number]).columns.tolist()[:3])}",
                f"Missing values detected in {sum(1 for v in df.isna().sum() if v > 0)} columns.",
            ],
            "data_quality": {
                "score": 75,
                "issues":    ["Could not parse full AI analysis"],
                "strengths": ["Data loaded successfully"]
            },
            "recommended_analyses": [
                {
                    "title":       "Distribution Analysis",
                    "description": "Check the spread of numeric columns",
                    "chart_type":  "histogram"
                }
            ],
            "interesting_questions": [
                "What are the key trends in this data?",
                "Are there any outliers?",
                "What columns are most correlated?"
            ],
            "business_implications": "Further analysis needed to derive business implications."
        }


def answer_data_question(df: pd.DataFrame, question: str, filename: str) -> dict:
    """
    Answer a natural language question about the dataset.
    """
    profile = get_dataframe_profile(df)
    sample  = df.head(10).to_string()

    prompt = f"""You are an expert data analyst answering a question about a dataset.

Dataset: {filename}
Columns: {df.columns.tolist()}
Shape: {df.shape[0]} rows x {df.shape[1]} columns
Sample data:
{sample}

Statistical profile:
{json.dumps(profile.get('numeric_stats', {}), default=safe_json, indent=2)}

Question: {question}

Respond with ONLY a valid JSON object. Start with {{ and end with }}.

{{
    "answer": "Clear specific answer with numbers where possible",
    "methodology": "Brief explanation of how you derived this",
    "chart_suggestion": {{
        "type": "bar",
        "x_column": "column_name_or_null",
        "y_column": "column_name_or_null",
        "title": "chart title"
    }},
    "follow_up_questions": ["follow up question 1?", "follow up question 2?"]
}}"""

    text = call_llm(prompt)
    text = clean_json_response(text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "answer":      text if text else "Could not parse response.",
            "methodology": "Local LLM analysis",
            "chart_suggestion": {
                "type":     None,
                "x_column": None,
                "y_column": None,
                "title":    ""
            },
            "follow_up_questions": []
        }


def detect_anomalies(df: pd.DataFrame) -> list[dict]:
    """
    Automatically detect anomalies using IQR method.
    Pure Python — no LLM needed.
    """
    anomalies    = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 10:
            continue

        Q1  = series.quantile(0.25)
        Q3  = series.quantile(0.75)
        IQR = Q3 - Q1

        lower    = Q1 - 1.5 * IQR
        upper    = Q3 + 1.5 * IQR
        outliers = series[(series < lower) | (series > upper)]

        if len(outliers) > 0:
            anomalies.append({
                "column":        col,
                "outlier_count": int(len(outliers)),
                "outlier_pct":   round(len(outliers) / len(series) * 100, 1),
                "lower_bound":   round(float(lower), 2),
                "upper_bound":   round(float(upper), 2),
                "min_outlier":   round(float(outliers.min()), 2),
                "max_outlier":   round(float(outliers.max()), 2),
            })

    return sorted(anomalies, key=lambda x: x["outlier_pct"], reverse=True)