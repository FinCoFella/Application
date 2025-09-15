import matplotlib
matplotlib.use("Agg") 
import io, base64
import matplotlib.pyplot as plt
import pandas as pd

#### Return a base64-encoded PNG image of a line chart showing the trend of Unsecured-Debt-to-EBITDA ratio over a time series #####
def line_chart_png(df: pd.DataFrame) -> str:

    if df.empty:
        return ""
    
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(df["Quarter"], df["Unsecured_Debt_to_EBITDA"], marker="o",  linewidth=2, color="#00aeef")
    ax.set_xlabel("Quarter")
    ax.set_ylabel("Total Unsecured Debt / EBITDA (Annualized)")
    ax.set_title("Unsecured Leverage Trend")
    ax.grid(alpha=0.3, linestyle="--", linewidth=0.5)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    
    return base64.b64encode(buf.getvalue()).decode("ascii")

#### Return a base64-encoded PNG image of a pie chart showing the composition of a CRE loan portfolio #####
def pie_chart_png(df: pd.DataFrame) -> str:
    
    df = df[df["Value"] > 0].copy()
    total_row = df[df["Line_Item_Name"] == "Total CRE"]

    if total_row.empty:
        return ""
    
    total_val = float(total_row["Value"].iloc[0])
    if total_val <= 0:
        return  ""

    total_value = total_row["Value"].iloc[0]
    df = df[df["Line_Item_Name"] != "Total CRE"].copy()
    if df.empty:
        return ""

    df = df.sort_values(by="Value", ascending=False)

    colors = [
        "#003f5c", "#29487d", "#87bdd8", "#AEDEF4", "#012F42",
        "#51A0AC", "#3B6565", "#409ac7", "#0f9a93", "#59C9BA"
    ]

    color_cycle = (colors * ((len(df) // len(colors)) + 1))[:len(df)]

    values = df["Value"]
    raw_labels = df["Line_Item_Name"]
    percentages = values / total_value * 100
    labels = [f"{label}, {pct:.1f}%" for label, pct in zip(raw_labels, percentages)]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(values, labels=labels, startangle=140, colors=color_cycle)
    ax.set_title("CRE Loan Portfolio Distribution")
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)

    return base64.b64encode(buf.getvalue()).decode("ascii")