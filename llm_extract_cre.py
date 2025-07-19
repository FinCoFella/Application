import base64, tempfile, os
from typing import Dict, Callable
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def cfg_prompt(ticker, quarter, units, currency, category) -> str: 
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels and loan amounts from this image, then output a markdown table with columns:\n" 
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Merge 'Other general office' and 'Credit tenant lease and life sciences' into 'Office'.\n"
        f"Merge 'Other', 'Co‑op', and 'Data Center' into 'Other'.\n"
        f"Rename 'Hospitality' to 'Lodging'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def bac_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels and loan amounts from this image, then output a markdown table with columns:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Rename 'Industrial / Warehouse' to 'Industrial', 'Multi-family rental' to 'Multi-family', 'Shopping centers / Retail' to 'Retail', 'Hotel / Motels' to 'Lodging', and 'Multi-use' to 'Mixed-use'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def jpm_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels, their corresponding values in the 'Credit Exposure' column, and the '% Drawn' column from this image.\n"
        f"Then multiply the values in '% Drawn' column with the values in th 'Credit Exposure' column and place the product in a 'Loan Amount' column.\n"
        f"Generate a markdown table with the following columns in this exact order:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Combine 'Other Income Producing Properties' and 'Services and Non Income Producing' into a single 'Other' property type row.\n"
        f"Rename 'Multifamily' to 'Multi-family'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def wfc_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels below the 'By property:' column and their corresponding 'Loans oustanding balance' values under the 'Total commercial real estate' section from this image.\n"
        f"Generate a markdown table with the following columns in this exact order:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Combine 'Shopping center' with 'Retail (excl shopping)' into a 'Retail' property type row.\n"
        f"Combine 'Other' with 'Storage facility', 'Mobile home park', and 'Instiutional' into a single 'Other' property type row.\n"
        f"Rename 'Apartments' to 'Multi-family', 'Industrial/warehouse' to 'Industrial', 'Hotel/motel' to 'Lodging', and 'Mixed use properties' to 'Mixed-use'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def key_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels below the 'Nonowner-occupied' column and their corresponding values in the 'Total' column from this image.\n"
        f"Generate a markdown table with the following columns in this exact order:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Combine the 'Medical Office' value with the 'Office' value into a single 'Office' property type.\n"
        f"Combine 'Diversified' into 'Other', add 'Data Center' into 'Other', add 'Land & Residential' into 'Other', add 'Self Storage' into 'Other', add 'Senior Housing' into 'Other', add 'Skilled Nursing' into 'Other', and add 'Student Housing' into 'Other'.\n"
        f"Rename 'Multifamily' to 'Multi-family'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"        
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def hban_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels and loan amounts from this image, then output a markdown table with columns:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Rename 'Multifamily' to 'Multi-family'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Divide the values by 1000.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def snv_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels and loan amounts from this image, then output a markdown table with columns:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Rename 'Other Investment Properties' into 'Other' and add 'Development & Land' into the single 'Other' property type row.\n"
        f"Rename 'Office Building' to 'Office', 'Shopping Centers' to 'Retail', 'Hotels' to 'Lodging', 'Warehouse' to 'Industrial', and 'Residential Properties' to 'Residential'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def fcnca_prompt(ticker, quarter, units, currency, category) -> str:
       return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels and loan amounts from this image, then output a markdown table with columns:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Combine 'Medical Office' and 'General Office' values into a single 'Office' property type row.\n"
        f"Rename 'Hotel/Motel' to 'Lodging' and 'Industrial / Warehouse' to 'Industrial'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Divide the values by 1000.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def pnc_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels and loan amounts from this image, then output a markdown table with columns:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Combine 'Seniors Housing' into the 'Other' property type row.'\n"
        f"Rename 'Industrial / Warehouse' to 'Industrial', 'Multifamily' to 'Multi-family', 'Mixed Use' to 'Mixed-use', and 'Hotel / Motel' to 'Lodging'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Divide the values by 1000.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def rf_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels and loan amounts from this image, then output a markdown table with columns:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Add the percentages from 'Residential homebuilders' and 'Residential land' into 'Residential'.\n" 
        f"Add the percentages of 'Data center', 'Diversified', 'Healthcare', 'Commercial land', 'Other', and 'Self storage' into the single 'Other' property type.\n"
        f"Then multiply each percentage by property type by the dollar amount value in the center of the pie chart to determine the loan amount by property type.\n"
        f"Rename 'Apartments' to 'Multi-family' and 'Hotel' to 'Lodging'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Divide the values by 1000.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

PROMPT_MAP: Dict[str, Callable[[str, str, str, str, str],str]] = {
    "CFG": cfg_prompt,
    "BAC": bac_prompt,
    "JPM": jpm_prompt,
    "WFC": wfc_prompt,
    "KEY": key_prompt,
    "HBAN": hban_prompt,
    "SNV": snv_prompt,
    "FCNCA": fcnca_prompt,
    "PNC": pnc_prompt,
    "RF": rf_prompt,
}

############ Extract Data into Markdown Table ############
def extract_cre_table(image_file, ticker: str, quarter: str, units: str, currency: str, category: str) -> str:
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        image_file.save(tmp.name)
        with open(tmp.name, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

    ticker_up = ticker.upper()
    prompt_builder = PROMPT_MAP.get(ticker_up, cfg_prompt)
    instruction = prompt_builder(ticker_up, quarter, units, currency, category)

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instruction},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ],
            }
        ],
    )

    return resp.choices[0].message.content

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