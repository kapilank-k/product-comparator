import re
from prettytable import PrettyTable

# -----------------------------
# Regex-Based Field Extraction Rules
# -----------------------------
FIELD_RULES = {
    "Full Form": [
        (r"ORDINARY PORTLAND CEMENT", lambda m: 'ORDINARY PORTLAND CEMENT (full form)'),
        (r"\bOPC\b", lambda m: 'OPC (abbreviated)'),
        (r"TMT", lambda m: 'Abbreviated: "TMT"'),
        (r"HT STEEL STRAND", lambda m: 'Full form: "HT STEEL STRAND"'),
        (r"LRPCF", lambda m: 'Abbreviated: "LRPCF"'),
        (r"RIB BAR", lambda m: 'Abbreviated: RIB BAR + CRS')
    ],
    "Grade": [
        (r"GRADE\s*[:-]?\s*(\w+)", lambda m: f'GRADE :- {m.group(1)}'),
        (r"GRADE:-(\w+)", lambda m: f'GRADE:- {m.group(1)}'),
        (r"(FE_?500D|FE550D|1860|53)", lambda m: f'Inline: "{m.group(1)}"'),
        (r"\b53\b", lambda m: '53 (inline)' if 'LOOSE' in m.string else '53 (implied)')
    ],
    "Form": [
        (r"FORM\s*[:-]?\s*([^;]+)", lambda m: f'FORM :- {m.group(1).strip()}'),
        (r"FORM:-([^;]+)", lambda m: f'FORM:- {m.group(1).strip()}'),
        (r"LOOSELOOSE", lambda m: '"LOOSELOOSE" (redundant)'),
        (r"LOOSE", lambda m: 'LOOSE'),
        (r"BULK", lambda m: 'FORM :- Bulk'),
    ],
    "Type": [
        (r"TYPE\s*[:-]?\s*([^;]+)", lambda m: f'TYPE :- {m.group(1).strip()}'),
        (r"TYPE:-([^;]+)", lambda m: f'TYPE:- {m.group(1).strip()}'),
        (r"TYPE OF STRAND\s*[:-]?\s*([^;]+)", lambda m: f'TYPE OF STRAND :- {m.group(1).strip()}'),
        (r"Corrosion resistant steel", lambda m: 'TYPE:- Corrosion resistant steel (CRS)'),
        (r"Thermo mechanically treated", lambda m: 'TYPE :- Thermo mechanically treated (TMT)'),
        (r"TMT.*CRS", lambda m: 'TMT + CRS'),
        (r"RIB BAR.*CRS", lambda m: 'RIB BAR + CRS'),
    ],
    "Diameter": [
        (r"NOMINAL DIAMETER OF STRAND\s*[:-]?\s*(\d+(?:\.\d+)?)\s*MM",
         lambda m: f'NOMINAL DIAMETER :- {m.group(1)} mm'),
        (r"DIAMETER\s*[:-]?\s*(\d+(?:\.\d+)?)\s*MM",
         lambda m: f'DIAMETER :- {m.group(1)} mm'),
        (r"(\d+(?:\.\d+)?)\s*MM", lambda m: f'Inline: "{m.group(1)} mm"'),
    ],
    "Length": [
        (r"Length:\s*(\d+\.\d+)\s*M", lambda m: f'clearly "{m.group(1)} m"'),
        (r"(\d+)-\1-\1.*Length:\s*(\d+\.\d+)\s*M", lambda m: f'Repeated as "{m.group(1)}", clearly "{m.group(2)} m"'),
        (r"(\d+)-\1-\1", lambda m: f'Repeated as "{m.group(1)}", clearly "{m.group(1)}.000 m"'),
        (r"FORM.*Standard length", lambda m: 'FORM:- Straight bars (standard length)'),
        (r"FORM.*Specific length", lambda m: 'FORM :- Straight bars (specific length)')
    ],
    "Standard": [
        (r"STANDARD\s*[:-]?\s*([^;]+)", lambda m: f'STANDARD :- {m.group(1).strip()}' if 'STANDARD :-' in m.string else f'STANDARD:- {m.group(1).strip()}'),
        (r"IS 1786", lambda m: 'STANDARD :- IS 1786'),
        (r"BIS \d+_\d+", lambda m: f'Mentioned: BIS {m.group(0)}'),
    ],
    "Structure": [
        (r";.*:-", lambda m: 'Fully structured'),
        (r"^OPC\d+$", lambda m: 'Very short'),
        (r"^OPC\d+\s+LOOSE$", lambda m: 'Short & inline'),
        (r"-", lambda m: 'Coded inline'),
        (r"/", lambda m: 'Mixed inline + natural language'),
        (r".*", lambda m: 'Unstructured free text'),
    ],
    "Extra Info": [
        (r"6C11M0007000000", lambda m: 'Ends with code: 6C11M0007000000'),
        (r"Oiled\.", lambda m: '"Oiled." suffix'),
        (r"JVBTLCD201 P1", lambda m: 'Codes: JVBTLCD201, P1'),
        (r";", lambda m: 'Not present'),
    ]
}

# IMPORTANT: You'll need to decide which ASPECT_ORDER to use when
# fetching input from the user, as there's no inherent "pair_num"
# for user-provided input. For simplicity, I'll use the order for Pair 6
# as an example, but you could add a prompt to select the order, or
# create a "generic" order.
GENERIC_ASPECT_ORDER = [
    "Type", "Full Form", "Grade", "Diameter", "Length",
    "Form", "Standard", "Structure", "Extra Info"
]


# -----------------------------
# Helper Functions (Unchanged)
# -----------------------------

def extract_details(text):
    result = {}
    for field, rules in FIELD_RULES.items():
        for pattern, formatter in rules:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                result[field] = formatter(match)
                break
    return result

def compare_strings(s1, s2, pair_num=None, aspect_order=None):
    d1 = extract_details(s1)
    d2 = extract_details(s2)

    # Use provided aspect_order or default to GENERIC_ASPECT_ORDER
    aspects_to_display = aspect_order if aspect_order is not None else GENERIC_ASPECT_ORDER

    if pair_num:
        print(f"✅ Pair {pair_num}")
    else:
        print(f"✅ User Input Comparison")

    print(f"String 1: {s1}")
    print(f"String 2: {s2}\n")

    table = PrettyTable()
    table.field_names = ["Aspect", "String 1", "String 2"]
    table.align["Aspect"] = "l"
    table.align["String 1"] = "l"
    table.align["String 2"] = "l"

    for aspect in aspects_to_display:
        v1 = d1.get(aspect, "Not mentioned")
        v2 = d2.get(aspect, "Not mentioned")
        if v1 == "Not mentioned" and v2 == "Not mentioned":
            continue
        table.add_row([aspect, v1, v2])

    print(table)
    print("\n---\n")

# -----------------------------
# Main Execution for User Input
# -----------------------------

def main():
    print("Welcome to the String Comparison Tool!")
    print("Enter 'exit' at any prompt to quit.")

    comparison_count = 1
    while True:
        print(f"\n--- Comparison {comparison_count} ---")
        s1 = input("Enter String 1: ").strip()
        if s1.lower() == 'exit':
            break

        s2 = input("Enter String 2: ").strip()
        if s2.lower() == 'exit':
            break

        # You can choose which ASPECT_ORDER to use here.
        # For a generic comparison, GENERIC_ASPECT_ORDER is good.
        # If you wanted to simulate a specific pair from the original,
        # you could manually set it, e.g., ASPECT_ORDER.get(6) for Pair 6's order.
        compare_strings(s1, s2, pair_num=comparison_count, aspect_order=GENERIC_ASPECT_ORDER)

        comparison_count += 1

    print("Thank you for using the tool. Goodbye!")

if __name__ == "__main__":
    main()