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