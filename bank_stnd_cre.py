from typing import List, Dict

STANDARDIZED_LABELS = ["Multi-family", "Industrial", "Lodging", "Office", "Retail", "Mixed-use", "Residential", "Other"]

##### Convert a Markdown table into a list of dictionaries for represent the table row #####
def build_rows_from_llm(md_table_to_rows, extract_cre_table, image, ticker, quarter, units, currency, category):

    md_table, explanation  = extract_cre_table(image, ticker, quarter, units, currency, category)
    clean_table = "\n".join(line for line in md_table.splitlines() if line.lstrip().startswith("|"))
    rows = md_table_to_rows(clean_table)

    return rows, explanation

##### Apply user override values entered in the standardized label fields and append a row to calcualate the sum of all values in the prior rows#####
def override_values(orig_rows: List[Dict], form_dict) -> List[Dict]:

    by_label = {r["Line_Item_Name"]: r.copy()
            for r in orig_rows if r["Line_Item_Name"] != "Total CRE"}
    
    template = next((r for r in orig_rows
            if r["Line_Item_Name"] != "Total CRE"), {})

    new_rows: List[Dict] = []
    grand_total = 0.0

    for label in STANDARDIZED_LABELS:
        field = f"ov_{label.replace(' ', '_')}"
        user_val = (form_dict.get(field) or "").strip()

        if user_val:
            try:
                value = float(user_val)
            except ValueError:
                value = 0.0
        elif label in by_label:
            value = by_label[label]["Value"]
        else:
            continue

        row = by_label.get(label) or {
            "Ticker": form_dict["ticker"],
            "Quarter": form_dict["quarter"],
            "Line_Item_Name": label,
            "Unit": template.get("Unit", ""),
            "Currency": template.get("Currency", ""),
            "Category": template.get("Category", ""),
        }
    
        row["Value"] = value
        new_rows.append(row)
        grand_total += value

    new_rows.append({
        "Ticker": form_dict["ticker"],
        "Quarter": form_dict["quarter"],
        "Line_Item_Name": "Total CRE",
        "Value": round(grand_total, 1),
        "Unit": template.get("Unit", ""),
        "Currency": template.get("Currency", ""),
        "Category": template.get("Category", ""),
    })

    return new_rows