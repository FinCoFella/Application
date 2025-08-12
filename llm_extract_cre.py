import base64, tempfile, json, os, re
from collections import defaultdict
from decimal import Decimal, ROUND_DOWN, getcontext
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI

from ticker_prompts_cre import PROMPT_MAP as TICKER_PROMPT_MAP
from generic_prompt_cre import generic_prompt_pie_percent, generic_prompt_value_table, normalize_label, Standardized_Labels

getcontext().prec = 28

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=60.0)

############ Extract Data into Markdown Table ############
def extract_cre_table(image_file, ticker: str, quarter: str, units: str, currency: str, category: str, chart_type: str = "percentage_pie") -> tuple[str, str]:
    tmp_path = None
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp_path = tmp.name

        image_file.save(tmp_path)

        try:
            with Image.open(tmp_path) as img:
                w, h = img.size

                if w > 0 and h > 0:
                    max_side = 1600
                    long_side = max(w, h)
                    scale = min(2.0, max_side / float(long_side))

                    if abs(scale - 1.0) > 1e-9:
                        resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
                        new_size = (int(w * scale), int(h * scale))
                        img = img.resize(new_size, resample=resample)

                img.save(tmp_path, format="PNG", optimize=True)

        except Exception:
            pass

        with open(tmp_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        ticker_up = ticker.upper()
        ticker_builder = TICKER_PROMPT_MAP.get(ticker_up)

        if ticker_builder:
            instruction = ticker_builder(ticker_up, quarter, units, currency, category)
        else:
            if chart_type == "value_table":
                instruction = generic_prompt_value_table(ticker_up, quarter, units, currency, category)
            else:
                instruction = generic_prompt_pie_percent(ticker_up, quarter, units, currency, category)

        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": instruction},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{image_b64}", "detail": "high"},
                            },
                        ],
                    }
                ],
                timeout=60.0,
            )
            raw = (resp.choices[0].message.content or "").strip()
        except Exception:
            return "", "### Explanation\nLLM request failed or timed out."

        parts = re.split(r'^#+\s*Explanation\b', raw, flags=re.I|re.M) 

        if len(parts) == 1:
            parts.append("LLM does not have an explanation.")

        md_table = parts[0].strip()
        explanation = parts[1].strip()

        return md_table, explanation

    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

############ Convert Markdown Table into Python Dictionary List ############
def md_table_to_rows(md_table: str):

    rows = []
    lines = [l for l in md_table.splitlines() if l.startswith("|")]

    if len(lines) < 3:
        return rows
    
    for line in lines[2:]:
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) != 7:
            continue
        try:
            value = float(parts[3].replace(",", ""))
        except ValueError:
            value = None

        rows.append(
            {
                "Ticker": parts[0],
                "Quarter": parts[1],
                "Line_Item_Name": parts[2],
                "Value": value,
                "Unit": parts[4],
                "Currency": parts[5],
                "Category": parts[6],
            }
        )

    return rows

def aggregate_standardized(rows):
    if not rows:
        return rows

    agg = defaultdict(float)
    meta = {k: v for k, v in rows[0].items() if k not in ("Line_Item_Name", "Value")}

    for r in rows:
        name = str(r.get("Line_Item_Name", "")).strip()
        if not name or name.lower() == "total cre":
            continue
        normalized = normalize_label(name)

        if normalized not in Standardized_Labels:
            continue
        val = r.get("Value") or 0
        try:
            val = float(val)
        except Exception:
            val = 0
        agg[normalized] += val

    out = []
    for label, val in agg.items():
        out.append({**meta, "Line_Item_Name": label, "Value": int(val)})

    total = int(sum(r["Value"] for r in out))
    out.append({**meta, "Line_Item_Name": "Total CRE", "Value": total})

    return out

def rows_from_slices_json_precise(explanation_text, ticker, quarter, units, currency, category):
    m = re.search(r"```json\s*(\{.*?\})\s*```", explanation_text, flags=re.S|re.I)

    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except Exception:
        return None

    total = Decimal(str(data.get("total_mn", 0)))
    slices = data.get("slices", []) or []

    agg = defaultdict(Decimal)

    for s in slices:
        raw_label = str(s.get("label", "")).strip()
        pct = s.get("percent")

        if pct is None:
            continue

        amt_exact = (total * Decimal(str(pct))) / Decimal(100)
        amt_trunc = amt_exact.quantize(Decimal("1"), rounding=ROUND_DOWN)

        norm = normalize_label(raw_label)
        if norm in Standardized_Labels:
            agg[norm] += amt_trunc

    meta = {"Ticker": ticker, "Quarter": quarter, "Unit": units, "Currency": currency, "Category": category}
    rows = [{**meta, "Line_Item_Name": k, "Value": int(v)} for k, v in agg.items()]
    total_row = int(sum(r["Value"] for r in rows))
    rows.append({**meta, "Line_Item_Name": "Total CRE", "Value": total_row})

    return rows