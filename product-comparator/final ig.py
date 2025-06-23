
import re
from prettytable import PrettyTable


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

ASPECT_ORDER = {
    1: ["Full Form", "Grade", "Form", "Structure", "Extra Info"],
    2: ["Full Form", "Grade", "Diameter", "Extra Info", "Standard", "Type", "Structure"],
    3: ["Type", "Grade", "Diameter", "Length", "Extra Info", "Standard", "Structure"],
    4: ["Brand", "Type", "Grade", "Diameter", "Standard", "Structure"],
    5: ["Type", "Grade", "Diameter", "Length", "Standard", "Structure"],
    6: ["Type", "Grade", "Diameter", "Length", "Standard", "Structure"],
    7: ["Full Form", "Grade", "Form", "Structure"],
    8: ["Full Form", "Grade", "Form", "Structure"]
}

# Helper Functions

def extract_details(text):
    result = {}
    for field, rules in FIELD_RULES.items():
        for pattern, formatter in rules:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                result[field] = formatter(match)
                break
    return result

def compare_strings(s1, s2, pair_num):
    d1 = extract_details(s1)
    d2 = extract_details(s2)

    # Determine which aspects to display based on pair_num
    aspects = ASPECT_ORDER.get(pair_num, [])

    print(f"✅ Pair {pair_num}")
    print(f"String 1: {s1}")
    print(f"String 2: {s2}\n")

    table = PrettyTable()
    table.field_names = ["Aspect", "String 1", "String 2"]
    table.align["Aspect"] = "l"
    table.align["String 1"] = "l"
    table.align["String 2"] = "l"

    for aspect in aspects:
        v1 = d1.get(aspect, "Not mentioned")
        v2 = d2.get(aspect, "Not mentioned")
        # Skip rows where both values are "Not mentioned"
        if v1 == "Not mentioned" and v2 == "Not mentioned":
            continue
        table.add_row([aspect, v1, v2])

    print(table)
    print("\n---\n")

# Sample Input Strings
string_pairs = [
    ("OPC 53LOOSELOOSE CEMENT", "GRADE :- 53;ORDINARY PORTLAND CEMENT;  FORM :- Bulk; - 6C11M0007000000"),
    ("S_LRPCF BIS 14268_2022 GRADE_1860-P 15.20mm Oiled.", "HT STEEL STRAND; TYPE OF STRAND :- 7 ply; 1860; TYPE :- P; NOMINAL DIAMETER OF STRAND :- 15.2 mm;"),
    ("TMT FE_500D JVBTLCD201 P1 12.00mm 12000.00mm.", "REINFORCEMENT STEEL BAR; TYPE :- Thermo mechanically treated (TMT); GRADE :- Fe 500D; DIAMETER :- 12 mm; FORM :- Straight bars (standard length); STANDARD :- IS 1786;"),
    ("TISCON-TMT IS 1786 FE550D CRS# 32.00 mm", "REINFORCEMENT STEEL BAR; TYPE :- Corrosion resistant steel (CRS); GRADE :- Fe 550D; DIAMETER :- 32 mm; FORM :- Straight bars (standard length); STANDARD :- IS 1786;"),
    ("TMT-FE_500D-32mm-11.000mtr.", "REINFORCEMENT STEEL BAR; TYPE :- Thermo mechanically treated (TMT); GRADE :- Fe 500D; DIAMETER :- 32 mm; FORM :- Straight bars (specific length); STANDARD :- IS 1786;"),
    ("RIB BAR 16.00 MM DIA LEN 12-12-12   FE550D-CRS / Length: 12.000 m", "REINFORCEMENT STEEL BAR; TYPE:-Corrosion resistant steel (CRS); GRADE:-Fe 500D; DIAMETER:-16 mm; FORM:-Straight bars (standard length); STANDARD:-IS 1786"),
    ("OPC53", "ORDINARY PORTLAND CEMENT; GRADE :- 53; FORM :- Bulk;"),
    ("OPC53 LOOSE", "ORDINARY PORTLAND CEMENT; GRADE :- 53; FORM :- Bulk;")
]

# Run Comparisons
for idx, (s1, s2) in enumerate(string_pairs, start=1):
    compare_strings(s1, s2, idx)
