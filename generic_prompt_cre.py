import re

Standardized_Labels = ["Multi-family", "Industrial", "Lodging", "Office", "Retail", "Mixed-use", "Residential", "Other"]

Synonyms = { 
    "Multifamily": "Multi-family", 
    "Apartments": "Multi-family",
    "Apartment & Residential": "Multi-family",
    "Multi Family": "Multi-family",
    "Multi-family rental": 'Multi-family',

    "Industrial / Warehouse": "Industrial",
    "Industrial/warehouse": "Industrial",
    "Industrial/Warehouse": "Industrial",
    "Warehouse/Industrial": "Industrial",
    "Warehouse": "Industrial",

    "Hotel": "Lodging",
    "Hotels": "Lodging",
    "Hotel / Motel": "Lodging",
    "Hotel/Motel": "Lodging",
    "Hotel/motel": "Lodging",
    "Hospitality": "Lodging",

    "Mixed use": "Mixed-use",
    "Mixed use properties": "Mixed-use",
    "Multi use": "Mixed-use",

    "Shopping Centers": "Retail",
    "Shopping center": "Retail",
    "Retail (excl shopping center)": "Retail",

    "Medical Office": "Office",
    "General Office": "Office",
    "Office Building": "Office",
    "Healthcare Office": "Office",
    "Other general office": "Office",
    "Credit tenant lease and life sciences": "Office",

    "Single Family / Land Development": "Residential",
    "Residential Land": "Residential",
    "Residential Properties": "Residential",
    "Residential for Sale": "Residential",
    "Residential (Housing)": "Residential",
    "Res. Homebuilders": "Residential",

    "Land Carry": "Other",
    "Other Income Producing Properties": "Other",
    "Services and Non Income Producing": "Other",
    "Land & Residential": "Other",
    "Senior Housing": "Other",
    "Seniors Housing": "Other",
    "Diversified": "Other",
    "Healthcare": "Other",
    "Healthcare ": "Other",
    "Health care": "Other",
    "Health Care": "Other",
    "Health-care": "Other",
    "Commercial Land": "Other",
    "Construction and Land": "Other",
    "Data Center": "Other",
    "Institutional": "Other",
    "Self Storage": "Other",
    "Mobile home park": "Other",
    "Skilled Nursing": "Other",
    "Specialty & Other": "Other",
    "Student Housing": "Other",
    "Self-Storage": "Other",
    "Storage facility": "Other",
    "Development & Land": "Other",
    "Other Investment Properties": "Other",
    "Co-op": "Other"
}

###### INSTRUCTS LLM TO EXTRACT LABELS AND PERCENTAGES VALUES FROM THE INPUT IMAGE AND OUTPUTS A JSON CODE BLOCK, EXPLANATION, AND MARKDOWN TABLE ######
def generic_prompt_pie_percent(ticker, quarter, units, currency, category) -> str:
    syn_labels = "\n".join(f" - '{a}' → '{b}'" for a, b in Synonyms.items())
    stnd_labels = ", ".join(Standardized_Labels)

    return f""" 
    Extract CRE exposure from the pie chart image.

    MARKDOWN TABLE
    Return one markdown table in the exact order below with the subsequent constant values:
    | Ticker | Quarter | CRE Property Type | Loan Amount | Units | Currency | Category |

    - Ticker: {ticker}\n
    - Quarter: {quarter}\n
    - Units: {units}\n
    - Currency: {currency}\n
    - Category: {category}\n

    NOTES
    - The last row in the 'CRE Property Type' column should say 'Total CRE'. 
    - The last row in the 'Loan Amount' column should be the sum of all rows.

    ### EXPLANATION 
    Begin this section with a fenced JSON code block.

    JSON CODE BLOCK
    ```json
            {{ "total_mn": <number in millions or null>,
            "slices": [ {{ "label": <category text only>, "percent": <number without % symbol> }}, ... ],
            "percent_sum": <sum of slice percents, no rounding>
            }}
    ```
    NOTES
    - Each slice printed next to the chart should contain a 'label' and 'percent' number.
    - Do not rename or normalize the labels in the JSON code block.
    - Do not add extra keys in the JSON code block.
    
    INSTRUCTIONS
    1) Read the total dollar amount in the center of the pie chart, and convert it into millions by multiply by 1000 (e.g.'0.0' to 0,000).
    2) Capture every slice in the pie chart and make sure the sum of the 'percent' values equals 100. Do not massage the 'percent' values to equal 100.

    EXPLANATION
    3) In less than 200 words, describe how the labels were normalized using the {syn_labels} mapping into {stnd_labels}. Mention how the 'Other' property label was normalized.
    """

###### INSTRUCTS LLM TO EXTRACT LABELS AND VALUES FROM THE INPUT IMAGE AND OUTPUTS A JSON CODE BLOCK, EXPLANATION, AND MARKDOWN TABLE ######
def generic_prompt_value_table(ticker, quarter, units, currency, category) -> str:
    syn_labels = "\n".join(f" - '{a}' → '{b}'" for a, b in Synonyms.items())
    stnd_labels = ", ".join(Standardized_Labels)

    return f"""
    Extract CRE exposure from the tabular image.

    MARKDOWN TABLE
    Return one markdown table in the exact order below with the subsequent constant values:
    | Ticker | Quarter | CRE Property Type | Loan Amount | Units | Currency | Category |

    - Ticker: {ticker}\n
    - Quarter: {quarter}\n
    - Units: {units}\n
    - Currency: {currency}\n
    - Category: {category}\n

    NOTES
    - The last row in the 'CRE Property Type' column should say 'Total CRE'. 
    - The last row in the 'Loan Amount' column should be the sum of all rows.

    ### EXPLANATION 
    Strictly begin the Explanation section with a fenced JSON code block:

    JSON CODE BLOCK
    ```json
        {{ "mode": "table",
        "rows": [ {{ "label": <category text only>, "amount": <number> }}, ... ],
        }}
    ```
    NOTES
    - The JSON code block must list every property type that carries a corresponding number in each row from the table image.
    - The numbers in the JSON code block should be the exact values from the table image (integers or decimals).
    - Use valid JSON syntax: no trailing commas, no currency symbols, no commas, and no unit suffixes.
    - Do not rename or normalize the labels and do not include any 'Total' rows in the JSON code block.

    EXTRACT
    1) Read each property type row and its corresponding loan amount value.
    2) Copy the property type label and the exact loan amount value into the JSON code block.
    3) Apply these rules in some certain cases:
        - If the table contains a 'Credit exposure' and '% Drawn' column, multiply the values from the 'Credit exposure' and '% Drawn" to calculate the loan amount.
        - If the table contains a 'Loans outstanding balance' column, use those values as the loan amounts for each property type label.
        - If the table contains a 'Total' column of amounts by type, use those values as the loan amounts for each property type label.

    EXPLANATION
    4) In less than 200 words, describe how the labels were normalized using the {syn_labels} mapping into {stnd_labels}. Mention how the 'Other' property label was normalized.
    """