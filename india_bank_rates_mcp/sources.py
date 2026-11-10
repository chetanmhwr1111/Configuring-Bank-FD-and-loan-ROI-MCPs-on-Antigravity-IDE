"""Editable list of official-source URLs.

These are source-page starting points. Website layouts can change; parsers may need
bank-specific adapters. Verify every result against the official page.
"""

RBI_SOURCES = [
    "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx",
    "https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=119",
]

BANKS = [
    {"name": "State Bank of India", "category": "public", "url": "https://sbi.co.in/web/interest-rates/interest-rates/deposit-rates"},
    {"name": "Bank of Baroda", "category": "public", "url": "https://www.bankofbaroda.in/interest-rate"},
    {"name": "Punjab National Bank", "category": "public", "url": "https://www.pnbindia.in/interest-rates-deposit.html"},
    {"name": "Canara Bank", "category": "public", "url": "https://canarabank.com/pages/interest-rates"},
    {"name": "Union Bank of India", "category": "public", "url": "https://www.unionbankofindia.co.in/english/interest-rates.aspx"},
    {"name": "Bank of India", "category": "public", "url": "https://bankofindia.co.in/interest-rates"},
    {"name": "Indian Bank", "category": "public", "url": "https://indianbank.in/departments/interest-rates/"},
    {"name": "HDFC Bank", "category": "private", "url": "https://www.hdfcbank.com/personal/resources/rates"},
    {"name": "ICICI Bank", "category": "private", "url": "https://www.icicibank.com/personal-banking/deposits/fixed-deposit/fd-interest-rates"},
    {"name": "Axis Bank", "category": "private", "url": "https://www.axisbank.com/interest-rate"},
    {"name": "Kotak Mahindra Bank", "category": "private", "url": "https://www.kotak.com/en/rates/interest-rates.html"},
    {"name": "IndusInd Bank", "category": "private", "url": "https://www.indusind.com/in/en/personal/rates.html"},
    {"name": "IDFC FIRST Bank", "category": "private", "url": "https://www.idfcfirstbank.com/personal-banking/deposits/fixed-deposit/fd-interest-rates"},
    {"name": "Federal Bank", "category": "private", "url": "https://www.federalbank.co.in/interest-rates"},
]
