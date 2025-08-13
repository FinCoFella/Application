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

###### INSTRUCTS LLM TO EXTRACT LABELS AND PERCENTAGES VALUES FROM THE INPUT IMAGE AND OUTPUTS A JSON CODE BLOCK ######
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

    TABLE NOTES
    - The last row in the 'CRE Property Type' column should say 'Total CRE'. 
    - The last row in the 'Loan Amount' column should be the sum of all rows.

    ### EXPLANATION JSON CODE BLOCK
    Begin this section with a fenced JSON code block.

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
    3) Describe how the labels were normalized in less than 200 words.
    """

################### INSTRUCTS LLM TO EXTRACT LABELS & VALUES AND PLACES THEM INTO A JSON CODE BLOCK WITH EXPLANATION ###################
def generic_prompt_value_table(ticker, quarter, units, currency, category) -> str:
    syn_labels = "\n".join(f" - '{a}' → '{b}'" for a, b in Synonyms.items())
    stnd_labels = ", ".join(Standardized_Labels)

    return f"""
    Extract CRE exposure from the tabular image.

    OUTPUT TABLE:
    - Return one markdown table with columns in this exact order:
        | Ticker | Quarter | CRE Property Type | Loan Amount | Units | Currency | Category |
    - The last row in the 'CRE Property Type' column should say 'Total CRE'. 
    - The last row in the 'Loan Amount' column should be the sum of all rows.

    OUTPUT AUDIT
    - After the table, add '### Explanation' that begins with a JSON code block:
    ```json
        {{ "mode": "table",
        "rows": [ {{ "label":"Office", "amount": <number> }}, ... ],
        "unit_detected": "B"|"M"|null
        }}
    ```
    - The JSON code block must list every property type row extracted from the table.

    EXPLANATION 
    - After the JSON closing ```, write a paragraph in <200 words explaining:
        - Describe how the labels were normalized using the mapping: {syn_labels}.
        - Describe how the 'Other' property label was normalized.

    EXTRACT
    1) Read each property type row and its corresponding numeric loan amount value.
    2) If the values are in a table, follow these rules:
        - If the table contains a 'Credit exposure' and '% Drawn' column, multiply the values from the 'Credit exposure' and '% Drawn" to calculate the loan amount.
        - If the table contains a 'Loans outstanding balance' column, use those values as the loan amounts for each property type label.
        - If the table contains a 'Total' column of amounts by type, use those values as the loan amounts for each property type label.

    CONVERT UNITS
    3) If the values are in billions (e.g., '0.0'), multiply the value by 1000 to convert it into millions.

    NORMALIZE LABELS
    4) USe the following case-insensitive mapping to normalize the labels {syn_labels} and keep only these final labels: {stnd_labels}.
    5) Check to make sure 'Other' = sum of *all* slices that map to 'Other' in {syn_labels}.

    AGGREGATE
    6) After normalizing the property type lables, **sum the amounts that map to the same final label within {stnd_labels}**. 

    FORMAT 
    7) After aggregating the loan amount values, **truncate the trailing decimal values** in the 'Loan Amount' column to an integer to remove decimals.

    APPLY USER INPUT
    8) Produce only one markdown table that uses the following constant values:
        - Ticker: {ticker}\n"
        - Quarter: {quarter}\n"
        - Units: {units}\n"
        - Currency: {currency}\n"
        - Category: {category}\n"
    """