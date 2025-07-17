from typing import Dict
import fitz
from openai import OpenAI

def extract_inc_stmt_text(pdf: fitz.Document) -> str:     
        target_text = ""

        for i, page in enumerate(pdf):
            text = page.get_text()

            if "CONDENSED CONSOLIDATED STATEMENT OF OPERATIONS" in text.upper():
                target_text = text
                if i + 1 < len(pdf):
                    target_text += "\n" + pdf[i + 1].get_text()
                break

        return target_text

def build_llm_prompt_for_EBITDA(ticker: str, doc_excerpt: str) -> str:
     return f"""
        The following data is extracted text from {ticker}'s financial filing, which contains the company's income statement for a given quarter in the column "Three Months Ended". 
        In 1 concise bullet point, identify the quarter being analyzed and explain why EBITDA may be negative, unusually high, or low in the most recent quarter (typically the left-most column under "Three Months Ended"). 
        Look for mentions of impairment charges, operating losses, debt changes, or other one-time items.
        Note that EBITDA is defined as the sum of net income, interest expense, depreciation and amortization, and provision for income taxes.
        Document Text: {doc_excerpt}"""

def analyze_quarter_doc(pdf_bytes: bytes, ticker: str, client: OpenAI) -> Dict[str, str]:
     
        doc = fitz.open(stream=pdf_bytes.read(), filetype="pdf")

        target_text = extract_inc_stmt_text(doc)
        
        if not target_text:
            raise ValueError("Could not find the Income Statement section in the PDF.")
        
        normalized_text = " ".join(target_text.split())
        prompt = build_llm_prompt_for_EBITDA(ticker, normalized_text[:4000])

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500
        )

        return {"analysis": response.choices[0].message.content}