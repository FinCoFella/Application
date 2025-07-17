from typing import List, Dict
import json

def build_rows_from_llm(md_table_to_rows, extract_cre_table, image, ticker, quarter, units, currency, category):

    md_table  = extract_cre_table(image, ticker, quarter, units, currency, category)
    clean_table = "\n".join(line for line in md_table.splitlines() if line.lstrip().startswith("|"))

    return md_table_to_rows(clean_table)

def override_values(orig_rows: List[Dict], form_dict) -> List[Dict]:

    override_rows = []
    total_override = 0.0

    for r in orig_rows:
        r2 = r.copy()

        if r["Line_Item_Name"] != "Total CRE":

            field_name = f"ov_{r['Line_Item_Name'].replace(' ', '_')}"

            try:
                new_val = float(form_dict.get(field_name, "") or r["Value"])
            except ValueError:
                new_val = r["Value"]

            r2["Value"] = new_val
            total_override += new_val

        override_rows.append(r2)

    for r2 in override_rows:
        if r2["Line_Item_Name"] == "Total CRE":
            r2["Value"] = round(total_override, 1)
            break

    return override_rows