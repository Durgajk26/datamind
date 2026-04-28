"""
DataMind FastAPI Backend
-------------------------
Handles file upload, AI analysis, chart generation,
Q&A, and PDF report export.
"""

import os
import io
import json
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv

from backend.analyser import (
    generate_ai_insights, answer_data_question,
    detect_anomalies, get_dataframe_profile
)
from backend.charts import auto_generate_charts, generate_custom_chart
from backend.reporter import generate_report

load_dotenv()

app = FastAPI(title="DataMind API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for uploaded dataframes
_dataframes: dict[str, pd.DataFrame] = {}
_filenames:  dict[str, str]          = {}


def read_file(content: bytes, filename: str) -> pd.DataFrame:
    """Read CSV or Excel file into a pandas DataFrame."""
    if filename.endswith(".csv"):
        return pd.read_csv(io.BytesIO(content))
    elif filename.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(content))
    else:
        raise ValueError(f"Unsupported file type: {filename}")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "DataMind API running", "version": "1.0.0"}


@app.post("/upload/{session_id}")
async def upload_file(session_id: str, file: UploadFile = File(...)):
    content  = await file.read()
    filename = file.filename

    try:
        df = read_file(content, filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    _dataframes[session_id] = df
    _filenames[session_id]  = filename

    return {
        "filename": filename,
        "rows":     int(df.shape[0]),
        "columns":  int(df.shape[1]),
        "column_names": df.columns.tolist(),
        "message":  "File uploaded successfully"
    }


@app.get("/analyse/{session_id}")
def analyse(session_id: str):
    if session_id not in _dataframes:
        raise HTTPException(status_code=404, detail="No file uploaded")

    df       = _dataframes[session_id]
    filename = _filenames[session_id]

    insights  = generate_ai_insights(df, filename)
    anomalies = detect_anomalies(df)
    charts    = auto_generate_charts(df)
    profile   = get_dataframe_profile(df)

    return {
        "insights":  insights,
        "anomalies": anomalies,
        "charts":    charts,
        "profile":   profile,
        "filename":  filename,
    }


class QuestionRequest(BaseModel):
    question: str


@app.post("/ask/{session_id}")
def ask(session_id: str, request: QuestionRequest):
    if session_id not in _dataframes:
        raise HTTPException(status_code=404, detail="No file uploaded")

    df       = _dataframes[session_id]
    filename = _filenames[session_id]

    result = answer_data_question(df, request.question, filename)

    # Generate chart if AI suggests one
    chart_json = None
    suggestion = result.get("chart_suggestion", {})
    if (suggestion.get("type") and
        suggestion.get("x_column") and
        suggestion.get("x_column") in df.columns):

        y_col = suggestion.get("y_column")
        if y_col and y_col not in df.columns:
            y_col = None

        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not y_col and numeric_cols:
            y_col = numeric_cols[0]

        if y_col:
            chart_json = generate_custom_chart(
                df,
                suggestion["type"],
                suggestion["x_column"],
                y_col,
                suggestion.get("title", "Chart")
            )

    return {
        "answer":            result.get("answer", ""),
        "methodology":       result.get("methodology", ""),
        "chart":             chart_json,
        "follow_up":         result.get("follow_up_questions", []),
        "chart_suggestion":  suggestion,
    }


@app.get("/profile/{session_id}")
def profile(session_id: str):
    if session_id not in _dataframes:
        raise HTTPException(status_code=404, detail="No file uploaded")
    df = _dataframes[session_id]
    return get_dataframe_profile(df)


@app.get("/preview/{session_id}")
def preview(session_id: str, rows: int = 50):
    if session_id not in _dataframes:
        raise HTTPException(status_code=404, detail="No file uploaded")
    df = _dataframes[session_id]
    return {
        "data":    df.head(rows).fillna("").to_dict(orient="records"),
        "columns": df.columns.tolist(),
        "total_rows": int(df.shape[0])
    }


@app.post("/export/{session_id}")
def export(session_id: str):
    if session_id not in _dataframes:
        raise HTTPException(status_code=404, detail="No file uploaded")

    df       = _dataframes[session_id]
    filename = _filenames[session_id]
    insights = generate_ai_insights(df, filename)
    anomalies = detect_anomalies(df)
    profile_data = get_dataframe_profile(df)

    pdf_bytes = generate_report(filename, insights, anomalies, profile_data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=datamind_report.pdf"}
    )


@app.delete("/session/{session_id}")
def clear(session_id: str):
    _dataframes.pop(session_id, None)
    _filenames.pop(session_id, None)
    return {"message": "Session cleared"}