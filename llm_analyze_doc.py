from typing import Dict
import fitz
from openai import OpenAI

INCOME_STMT_HEADER = "CONDENSED CONSOLIDATED STATEMENT OF OPERATIONS"

##### Extracts text from a PDF page containing an income statement #####
def extract_inc_stmt_text(pdf: fitz.Document) -> str:     
        page_text = ""

        for page_index, page in enumerate(pdf):
            text = page.get_text()

            if INCOME_STMT_HEADER in text.upper():
                page_text = text
                if page_index + 1 < len(pdf):
                    page_text += "\n" + pdf[page_index + 1].get_text()
                break

        return page_text

##### LLM prompt instructions to analyze the EBITDA financial metric using data from an income statement #####
def llm_prompt_for_EBITDA(ticker: str, doc_excerpt: str) -> str:
     return f"""
        The following data is extracted text from {ticker}'s financial filing, which contains the company's income statement for a given quarter in the column "Three Months Ended". 
        In 1 concise bullet point, identify the quarter being analyzed and explain why EBITDA may be negative, unusually high, or low in the most recent quarter (typically the left-most column under "Three Months Ended"). 
        Look for mentions of impairment charges, operating losses, debt changes, or other one-time items.
        Note that EBITDA is defined as the sum of net income, interest expense, depreciation and amortization, and provision for income taxes.
        Document Text: {doc_excerpt}"""

##### Invokes the LLM to analyze the EBITDA financial metric in the income statement and returns the analysis #####
def analyze_quarter_doc(pdf_bytes: bytes, ticker: str, client: OpenAI) -> Dict[str, str]:
     
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        target_text = extract_inc_stmt_text(doc)
        
        if not target_text:
            raise ValueError("Could not find the Income Statement section in the PDF.")
        
        normalized_text = " ".join(target_text.split())
        prompt = llm_prompt_for_EBITDA(ticker, normalized_text[:4000])

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500
        )

        return {"analysis": response.choices[0].message.content}