"""
categorizer.py
==============
Keyword-based transaction categorizer for Indian bank statements.

Usage:
    from categorizer import categorize

    category, subcategory = categorize("SWIGGY ORDER 12345")
    # → ("Food & Dining", "Delivery")

Rules:
  - Case-insensitive matching against description
  - First matching rule wins
  - More specific keywords listed before general ones
  - UPI transactions: < 500 → "General Expenses", >= 500 → "Payments & Transfers"
  - Large transfers (>= 2000) without merchant match → "Payments & Transfers"
  - Default: ("Uncategorized", "")
"""

import re

# Short keywords (≤4 chars) that must match as whole words to avoid false positives
# e.g., "emi" in "premium", "ola" in "cola", "lab" in "laboratory"
_WORD_BOUNDARY_KEYWORDS = {
    "emi",
    "ola",
    "lab",
    "kfc",
    "jio",
    "pvr",
    "aws",
    "dth",
    "lic",
    "1mg",
}


# ============================================================
# Rule Structure
# ============================================================
# Each rule: (keyword, category, subcategory)
# Rules are checked in ORDER — first match wins.
# IMPORTANT: More specific keywords MUST come before general ones.
# e.g., "swiggy instamart" before "swiggy"
# NOTE: UPI/Payment keywords are NOT in rules - handled separately at the end

_RULES: list[tuple[str, str, str]] = [
    # ── Groceries (check BEFORE Food & Dining for swiggy instamart) ──────────
    ("avenue supermarts", "Groceries", "Offline"),  # D-Mart parent company
    ("swiggy instamart", "Groceries", "Online"),
    ("bigbasket", "Groceries", "Online"),
    ("blinkit", "Groceries", "Online"),
    ("zepto", "Groceries", "Online"),
    ("instamart", "Groceries", "Online"),
    ("jiomart", "Groceries", "Online"),
    ("grofers", "Groceries", "Online"),
    ("dunzo", "Groceries", "Online"),
    ("dmart", "Groceries", "Offline"),
    ("more supermarket", "Groceries", "Offline"),
    ("reliance fresh", "Groceries", "Offline"),
    ("nature basket", "Groceries", "Offline"),
    # ── Food & Dining ─────────────────────────────────────────────────────────
    ("swiggy", "Food & Dining", "Delivery"),
    ("zomato", "Food & Dining", "Delivery"),
    ("starbucks", "Food & Dining", "Coffee"),
    ("cafe coffee day", "Food & Dining", "Coffee"),
    ("third wave", "Food & Dining", "Coffee"),
    ("cafe", "Food & Dining", "Coffee"),
    ("mcdonalds", "Food & Dining", "Fast Food"),
    ("mcdonald", "Food & Dining", "Fast Food"),
    ("burger king", "Food & Dining", "Fast Food"),
    ("kfc", "Food & Dining", "Fast Food"),
    ("dominos", "Food & Dining", "Fast Food"),
    ("domino", "Food & Dining", "Fast Food"),
    ("subway", "Food & Dining", "Fast Food"),
    ("pizza hut", "Food & Dining", "Fast Food"),
    ("haldiram", "Food & Dining", "Fast Food"),
    ("barbeque nation", "Food & Dining", "Restaurant"),
    ("biryani", "Food & Dining", "Restaurant"),
    ("bakery", "Food & Dining", "Bakery"),
    ("juice", "Food & Dining", "Beverages"),
    ("restaurant", "Food & Dining", "Restaurant"),
    ("dining", "Food & Dining", "Restaurant"),
    # ── Shopping ──────────────────────────────────────────────────────────────
    ("amazon", "Shopping", "Online"),
    ("flipkart", "Shopping", "Online"),
    ("myntra", "Shopping", "Online"),
    ("ajio", "Shopping", "Online"),
    ("nykaa", "Shopping", "Online"),
    ("meesho", "Shopping", "Online"),
    ("tatacliq", "Shopping", "Online"),
    ("croma", "Shopping", "Electronics"),
    ("reliance digital", "Shopping", "Electronics"),
    ("cell point", "Shopping", "Electronics"),  # Cell Point India (SBI)
    ("shoppers stop", "Shopping", "Offline"),
    ("lifestyle", "Shopping", "Offline"),
    ("westside", "Shopping", "Offline"),
    ("decathlon", "Shopping", "Sports"),
    # ── Travel ────────────────────────────────────────────────────────────────
    ("irctc", "Travel", "Trains"),
    ("makemytrip", "Travel", "Booking"),
    ("goibibo", "Travel", "Booking"),
    ("cleartrip", "Travel", "Booking"),
    ("yatra", "Travel", "Booking"),
    ("indigo", "Travel", "Flights"),
    ("air india", "Travel", "Flights"),
    ("vistara", "Travel", "Flights"),
    ("spicejet", "Travel", "Flights"),
    ("airport", "Travel", "Flights"),
    ("uber", "Travel", "Cabs"),
    ("ola", "Travel", "Cabs"),
    ("rapido", "Travel", "Cabs"),
    # ── Bills & Utilities ─────────────────────────────────────────────────────
    ("airtel", "Bills & Utilities", "Mobile"),
    ("jio", "Bills & Utilities", "Mobile"),
    ("vodafone", "Bills & Utilities", "Mobile"),
    ("bsnl", "Bills & Utilities", "Mobile"),
    ("postpaid", "Bills & Utilities", "Mobile"),
    ("prepaid", "Bills & Utilities", "Mobile"),
    ("bescom", "Bills & Utilities", "Electricity"),
    ("tata power", "Bills & Utilities", "Electricity"),
    ("electricity", "Bills & Utilities", "Electricity"),
    ("gas bill", "Bills & Utilities", "Gas"),
    ("water bill", "Bills & Utilities", "Water"),
    ("broadband", "Bills & Utilities", "Internet"),
    ("tatasky", "Bills & Utilities", "DTH"),
    ("dish tv", "Bills & Utilities", "DTH"),
    ("dth", "Bills & Utilities", "DTH"),
    # ── Entertainment ─────────────────────────────────────────────────────────
    ("netflix", "Entertainment", "Streaming"),
    ("hotstar", "Entertainment", "Streaming"),
    ("prime video", "Entertainment", "Streaming"),
    ("spotify", "Entertainment", "Music"),
    ("youtube premium", "Entertainment", "Streaming"),
    ("sony liv", "Entertainment", "Streaming"),
    ("zee5", "Entertainment", "Streaming"),
    ("jiocinema", "Entertainment", "Streaming"),
    ("apple tv", "Entertainment", "Streaming"),
    ("disney", "Entertainment", "Streaming"),
    ("bookmyshow", "Entertainment", "Events"),
    ("pvr", "Entertainment", "Cinema"),
    ("inox", "Entertainment", "Cinema"),
    # ── Health ────────────────────────────────────────────────────────────────
    ("pharmeasy", "Health", "Pharmacy"),
    ("1mg", "Health", "Pharmacy"),
    ("netmeds", "Health", "Pharmacy"),
    ("apollo pharmacy", "Health", "Pharmacy"),
    ("practo", "Health", "Consultation"),
    ("hospital", "Health", "Hospital"),
    ("clinic", "Health", "Consultation"),
    ("diagnostic", "Health", "Diagnostics"),
    ("lab", "Health", "Diagnostics"),
    ("medical", "Health", "Medical"),
    ("dentist", "Health", "Dental"),
    ("doctor", "Health", "Consultation"),
    # ── Fuel ──────────────────────────────────────────────────────────────────
    ("hp petroleum", "Fuel", ""),
    ("bharat petroleum", "Fuel", ""),
    ("indian oil", "Fuel", ""),
    ("bpcl", "Fuel", ""),
    ("hpcl", "Fuel", ""),
    ("iocl", "Fuel", ""),
    ("petrol", "Fuel", ""),
    ("fuel", "Fuel", ""),
    ("shell", "Fuel", ""),
    # ── Education ─────────────────────────────────────────────────────────────
    ("education payment", "Education", ""),  # IDFC "Education Payment Fee"
    ("education fee", "Education", ""),
    ("udemy", "Education", "Online"),
    ("coursera", "Education", "Online"),
    ("skillshare", "Education", "Online"),
    ("unacademy", "Education", "Online"),
    ("byjus", "Education", "Online"),
    ("vedantu", "Education", "Online"),
    ("college", "Education", "Offline"),
    ("university", "Education", "Offline"),
    ("school", "Education", "Offline"),
    ("tuition", "Education", "Offline"),
    # ── EMI & Loans ───────────────────────────────────────────────────────────
    ("principal amount", "EMI & Loans", ""),  # ICICI loan amortization
    ("interest amount", "EMI & Loans", ""),  # ICICI loan interest
    ("amortization", "EMI & Loans", ""),  # ICICI amortization rows
    ("bajaj finserv", "EMI & Loans", ""),
    ("home credit", "EMI & Loans", ""),
    ("zestmoney", "EMI & Loans", ""),
    ("simpl", "EMI & Loans", "BNPL"),
    ("lazypay", "EMI & Loans", "BNPL"),
    ("emi", "EMI & Loans", ""),
    ("loan", "EMI & Loans", ""),
    # ── Insurance ─────────────────────────────────────────────────────────────
    ("lic", "Insurance", "Life"),
    ("icici lombard", "Insurance", "General"),
    ("hdfc ergo", "Insurance", "General"),
    ("star health", "Insurance", "Health"),
    ("acko", "Insurance", "General"),
    ("digit insurance", "Insurance", "General"),
    ("policy", "Insurance", ""),
    ("insurance", "Insurance", ""),
    # ── Subscriptions ─────────────────────────────────────────────────────────
    ("google storage", "Subscriptions", "Cloud"),
    ("icloud", "Subscriptions", "Cloud"),
    ("microsoft 365", "Subscriptions", "Software"),
    ("adobe", "Subscriptions", "Software"),
    ("notion", "Subscriptions", "Software"),
    ("chatgpt", "Subscriptions", "AI"),
    ("openai", "Subscriptions", "AI"),
    ("github", "Subscriptions", "Developer"),
    ("aws", "Subscriptions", "Cloud"),
    # ── Bills & Utilities — Tax charges ───────────────────────────────────────
    ("igst", "Bills & Utilities", "Tax"),  # IDFC/IndusInd IGST charges
    ("cgst", "Bills & Utilities", "Tax"),  # GST components
    ("sgst", "Bills & Utilities", "Tax"),
    ("gst @", "Bills & Utilities", "Tax"),  # IndusInd "GST @ 18%"
    ("annual fee", "Bills & Utilities", "Bank Charges"),  # SBI annual fee
    ("bank charges", "Bills & Utilities", "Bank Charges"),
    # ── Payment-specific keywords (NOT UPI - handled separately) ─────────────
    ("payment received", "Payments & Transfers", "Received"),
    ("cashback", "Payments & Transfers", "Cashback"),
    ("refund", "Payments & Transfers", "Refund"),
    ("reversal", "Payments & Transfers", "Reversal"),
    ("autopay", "Payments & Transfers", "AutoPay"),
    ("nach", "Payments & Transfers", "AutoPay"),
    ("mandate", "Payments & Transfers", "AutoPay"),
    ("bill payment", "Payments & Transfers", "Bill Pay"),
    ("cred", "Payments & Transfers", "Bill Pay"),
    ("bbps", "Payments & Transfers", "Bill Pay"),
    ("spaid", "Payments & Transfers", "Payment"),  # SPAID payment gateway
    ("payment/dp", "Payments & Transfers", "Payment"),  # IDFC "Payment/DP..."
]


# ============================================================
# Categorize Function
# ============================================================


def categorize(description: str, amount: float | None = None) -> tuple[str, str]:
    """
    Categorize a transaction description using keyword matching.

    Args:
        description: Transaction description string (any case).
        amount:      Optional transaction amount (float). Used for UPI/transfer fallback.

    Returns:
        Tuple of (category, subcategory).
        Categories include: Food & Dining, Groceries, Shopping, Travel,
        Bills & Utilities, Entertainment, Health, Fuel, Education,
        EMI & Loans, Insurance, Subscriptions, Payments & Transfers,
        General Expenses, Uncategorized.

    Rules are checked in order — first match wins.
    Short keywords (in _WORD_BOUNDARY_KEYWORDS) use word-boundary regex
    to avoid false positives (e.g., "emi" in "premium", "ola" in "cola").
    All other keywords use fast substring search.

    UPI Logic:
        - UPI + amount < 500 → "General Expenses" / "UPI"
        - UPI + amount >= 500 → "Payments & Transfers" / "UPI"

    Transfer Logic:
        - No merchant match + amount >= 2000 → "Payments & Transfers"
    """
    if not description:
        return ("Uncategorized", "")

    desc_lower = description.lower()

    # First, check all merchant/service rules
    for keyword, category, subcategory in _RULES:
        if keyword in _WORD_BOUNDARY_KEYWORDS:
            # Word-boundary match: "emi" must not be inside "premium"
            if re.search(r"\b" + re.escape(keyword) + r"\b", desc_lower):
                return (category, subcategory)
        else:
            if keyword in desc_lower:
                return (category, subcategory)

    # ── UPI Logic (after all merchant rules checked) ──────────────────────────
    # Check if this is a UPI transaction
    if "upi" in desc_lower:
        # UPI small transaction → General Expenses
        if amount is not None and amount < 500:
            return ("General Expenses", "UPI")
        # UPI larger transaction → Payments & Transfers
        return ("Payments & Transfers", "UPI")

    # ── Large Transfer Logic ──────────────────────────────────────────────────
    # Large amounts without merchant match → Payments & Transfers
    if amount is not None and amount >= 2000:
        return ("Payments & Transfers", "Transfer")

    return ("Uncategorized", "")


def categorize_batch(descriptions: list[str]) -> list[tuple[str, str]]:
    """
    Categorize a list of descriptions. Returns list of (category, subcategory) tuples.
    """
    return [categorize(d) for d in descriptions]


# ============================================================
# CLI / Quick Test
# ============================================================

if __name__ == "__main__":
    test_cases = [
        ("SWIGGY ORDER 12345", 200, "Food & Dining", "Delivery"),
        ("SWIGGY INSTAMART GROCERY", 500, "Groceries", "Online"),
        ("AMAZON PAY INDIA", 1000, "Shopping", "Online"),
        ("IRCTC TICKET BOOKING", 500, "Travel", "Trains"),
        ("UBER TRIP BANGALORE", 150, "Travel", "Cabs"),
        ("NETFLIX SUBSCRIPTION", 649, "Entertainment", "Streaming"),
        ("HDFC BANK EMI", 5000, "EMI & Loans", ""),
        ("AIRTEL POSTPAID BILL", 499, "Bills & Utilities", "Mobile"),
        ("PHARMEASY ORDER", 350, "Health", "Pharmacy"),
        ("UNKNOWN MERCHANT XYZ", 100, "Uncategorized", ""),
        ("BBPS PAYMENT RECEIVED", 1000, "Payments & Transfers", "Bill Pay"),
        ("CASHBACK CREDIT", 100, "Payments & Transfers", "Cashback"),
        ("UPI-UNKNOWN-MERCHANT", 200, "General Expenses", "UPI"),  # UPI < 500
        ("UPI-UNKNOWN-MERCHANT", 1000, "Payments & Transfers", "UPI"),  # UPI >= 500
        (
            "paytm.s/Paid v UPICC/DR/557405715279/Swigg y/",
            200,
            "Food & Dining",
            "Delivery",
        ),  # Swiggy in UPI
        (
            "LARGE TRANSFER NO MERCHANT",
            5000,
            "Payments & Transfers",
            "Transfer",
        ),  # >= 2000
        ("SMALL UNKNOWN", 100, "Uncategorized", ""),  # < 2000, no match
    ]

    print(f"{'Description':<45} {'Amt':>8} {'Expected':<25} {'Got':<25} {'Match'}")
    print("-" * 115)
    passed = 0
    for desc, amt, exp_cat, _exp_sub in test_cases:
        cat, sub = categorize(desc, amt)
        match = "✅" if cat == exp_cat else "❌"
        if cat == exp_cat:
            passed += 1
        print(f"{desc:<45} {amt:>8} {exp_cat:<25} {cat:<25} {match}")

    print(f"\n{passed}/{len(test_cases)} tests passed")
