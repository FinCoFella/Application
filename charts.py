import io, base64, matplotlib.pyplot as plt
import pandas as pd
import matplotlib
matplotlib.use("Agg") 

def line_chart_png(ratio_df: pd.DataFrame) -> str:

    if ratio_df.empty:
        return ""
    
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(
        ratio_df["Quarter"], 
        ratio_df["Unsecured_Debt_to_EBITDA"],
        marker="o", 
        linewidth=2, 
        color="#00aeef"
    )
    
    ax.set_xlabel("Quarter")
    ax.set_ylabel("Total Unsecured Debt / EBITDA (Annualized)")
    ax.set_title("Unsecured Leverage Trend")
    ax.grid(alpha=0.3, linestyle="--", linewidth=0.5)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    
    return base64.b64encode(buf.getvalue()).decode("ascii")

def pie_chart_png(df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(6, 6))

    df = df[df["Value"] > 0].copy()
    total_cre_row = df[df["Line_Item_Name"] == "Total CRE"]

    if total_cre_row.empty:
        plt.close(fig)
        return ""

    total_cre_value = total_cre_row["Value"].values[0]
    df = df[df["Line_Item_Name"] != "Total CRE"].copy()
    df = df.sort_values(by="Value", ascending=False)

    colors = [
        "#003f5c", "#29487d", "#87bdd8", "#AEDEF4", "#012F42",
        "#51A0AC", "#3B6565", "#409ac7", "#0f9a93", "#59C9BA"
    ]

    color_cycle = (colors * ((len(df) // len(colors)) + 1))[:len(df)]

    values = df["Value"]
    raw_labels = df["Line_Item_Name"]
    percentages = values / total_cre_value * 100
    labels = [f"{label}, {pct:.1f}%" for label, pct in zip(raw_labels, percentages)]

    ax.pie(values, labels=labels, startangle=140, colors=color_cycle)
    ax.set_title("CRE Loan Portfolio Distribution")
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)

    return base64.b64encode(buf.getvalue()).decode("ascii")