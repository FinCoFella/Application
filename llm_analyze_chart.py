from typing import Dict, Any
from openai import OpenAI
import pandas as pd
from load_db_ticker_rows import load_rows_by_ticker

def build_prompt(ticker: str, ratio_df: pd.DataFrame) -> str:

    trend_str = "\n".join([
        f"{row['Quarter']}: {row['Unsecured_Debt_to_EBITDA']:.2f}"
        for _, row in ratio_df.iterrows()
    ])

    return f"""The following data is a quarterly trend of an unsecured debt-to-EBITDA ratio for the REIT ticker {ticker}: {trend_str} 
    Analyze how this ratio has changed over time and provide exactly 3 concise bullet point that explain possible reasons for why the financial ratio has increased or decreased materially in certain quarters.
    Use financial reasoning and trends in the REIT industry to explain changes in this company's EBITDA financial metric and unsecured debt levels.
    Avoid giving generic statements in the explanation and keep each bullet under 3 sentences."""

def analyze_ratio(ticker: str, engine, unsecured_debt_to_ebitda, client: OpenAI) -> Dict[str, Any]:

    df = load_rows_by_ticker(ticker, engine)
    if df.empty:
        raise ValueError("No financial data found for this ticker.")

    ratio_df = unsecured_debt_to_ebitda(df)
    if ratio_df.empty:
        raise ValueError("Not enough data to analyze.")
    
    prompt = build_prompt(ticker, ratio_df)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=400
    )

    return {
        "analysis": response.choices[0].message.content,
        "ratio_df": ratio_df.to_dict(orient="records"),
    }





