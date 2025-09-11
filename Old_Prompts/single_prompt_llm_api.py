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

def generic_single_prompt(ticker, quarter, units, currency, category) -> str:
    syn_labels = "\n".join(f" - '{a}' → '{b}'" for a, b in Synonyms.items())
    stnd_labels = ", ".join(Standardized_Labels)

    return f"""
    Carefully read and execute the following instructions:

    1. Extract the property type labels and loan amounts from this image.
    2. If the property type labels are in percentages, multiply each percentage by the dollar amount value 
    in the center of the pie chart to determine the loan amount by property type.
    3. If the property type values are in a 'Credit exposure' column within a table (like JPM ticker), 
    multiply it by the percentage in the '% Drawn' column to determine the loan amount by property type.
    4. If the property type values are in a 'Loans outstanding balance' column within a table (like WFC ticker), 
    extract these values for each property type.
    5. If the property type values are in a 'Total' column within a table (like KEY ticker),
    extract these values for each property type label.
    6. Normalize the labels using this case-insensitive mapping: {syn_labels}
    7. Then keep only these final labels: {stnd_labels}
    8. Produce a markdown table with these columns:
        Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.
    9. Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.
    10. If the values are in billions in the format of '0.0', then multiply the value 
    by 1000 in order to convert the value into millions.

    11. Truncate the trailing decimal values in the 'Loan Amount' column.
    12. Apply the following user input values for the respective columns:
    - Ticker: {ticker}
    - Quarter: {quarter}
    - Units: {units}
    - Currency: {currency}
    - Category: {category}
    13. After the table, provide a second markdown block that begins with '### Explanation' and in less than 
    120 words describes how the labels were normalized and the total loan amount calculated.
    """