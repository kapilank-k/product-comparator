# Product Comparator Script with GROQ LLM Fallback
# Compares product descriptions field-by-field using rule-based extraction, fuzzy matching, semantic similarity, and Groq-hosted LLM fallback (Mixtral)

import re
import requests
from rapidfuzz import fuzz
from prettytable import PrettyTable
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
import os

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")



# === Step 1: Preprocessing ===
def preprocess(text):
    text = text.lower().strip()
    text = text.replace("_", " ")
    text = text.replace(":-", ":")
    text = text.replace(";", "; ")
    return text

# === Step 2: Field Extractors ===
def extract_grade(text):
    match = re.search(r"(fe[\s_]?500[d]?|\b43\b|\b53\b)", text)
    return match.group(1).upper().replace(" ", "") if match else None

def extract_diameter(text):
    match = re.search(r"(\d{1,3}\.?\d*)\s?mm", text)
    return f"{float(match.group(1)):.2f} mm" if match else None

def extract_material(text):
    if "opc" in text:
        return "OPC"
    if "tmt" in text:
        return "TMT"
    if "strand" in text or "lrpc" in text:
        return "PC Strand"
    return None

def extract_form(text):
    if "bulk" in text or "loose" in text:
        return "Loose"
    if "straight" in text:
        return "Straight bars"
    if "bag" in text:
        return "Bag"
    return None

def extract_length(text):
    match = re.search(r"(\d{4,5}\.?\d*)\s?mm", text)
    return f"{float(match.group(1)):.2f} mm" if match else None

def extract_standard(text):
    match = re.search(r"is\s?\d{4}", text)
    return match.group(0).upper() if match else None

# === Step 3: Semantic Model Setup ===
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def semantic_match(val1, val2):
    if not val1 or not val2:
        return False
    emb1 = model.encode(val1, convert_to_tensor=True)
    emb2 = model.encode(val2, convert_to_tensor=True)
    similarity = util.cos_sim(emb1, emb2)
    return similarity.item() > 0.85

# === Step 4: Field Comparator ===
def compare_field(val1, val2):
    if not val1 and not val2:
        return ("⚪ Not Mentioned", val1, val2)
    elif val1 == val2:
        return ("✅ Exact Match", val1, val2)
    elif val1 and val2 and fuzz.ratio(val1, val2) > 85:
        return ("✅ Fuzzy Match", val1, val2)
    elif semantic_match(val1, val2):
        return ("✅ Semantic Match", val1, val2)
    else:
        return ("❌ Mismatch", val1, val2)

# === Step 5: Report Formatter ===
def print_report(string1, string2, results):
    print("\nString 1:")
    print(string1)
    print("\nString 2:")
    print(string2)
    print("\n🔍 Comparison Report:\n")

    table = PrettyTable()
    table.field_names = ["Aspect", "String 1", "String 2", "Match Status"]

    for row in results:
        table.add_row(row)

    print(table)

# === Step 6: GROQ LLM Fallback ===
GROQ_API_KEY = "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" 
 # Replace this with your real API key

def call_llm_groq(string1, string2):
    prompt = f"""
Compare the following two product descriptions and extract these fields:
- Grade
- Diameter
- Material
- Form
- Length
- Standard

Return a JSON object for each string with field-value pairs.

String 1: {string1}
String 2: {string2}
"""
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
               "model": "llama3-70b-8192",  
                 "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
        )

        data = response.json()
        
        # If 'choices' is missing, print error
        if "choices" not in data:
            print("❌ LLM Response Error:", data)
            return "LLM call failed: Unexpected response structure"

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"LLM call failed: {str(e)}"


# === Step 7: Check if Fields Are Missing ===
def fields_missing(results):
    for aspect, val1, val2, _ in results:
        if val1 == "-" or val2 == "-":
            return True
    return False

# === Step 8: Core Comparison ===
def compare_strings(string1, string2):
    s1 = preprocess(string1)
    s2 = preprocess(string2)

    results = []

    aspects = [
        ("Grade", extract_grade),
        ("Diameter", extract_diameter),
        ("Material", extract_material),
        ("Form", extract_form),
        ("Length", extract_length),
        ("Standard", extract_standard),
    ]

    for aspect, func in aspects:
        val1 = func(s1)
        val2 = func(s2)
        status, v1, v2 = compare_field(val1, val2)
        results.append((aspect, v1 or "-", v2 or "-", status))

    print_report(string1, string2, results)

    if fields_missing(results):
        print("\n⚠️ Falling back to Groq LLM for smart extraction...\n")
        llm_output = call_llm_groq(string1, string2)
        print("\n🤖 LLM Fallback Output:")
        print(llm_output)

# === Step 9: CLI Input ===
if __name__ == "__main__":
    print("\n🔧 Product Comparator - Enter two descriptions\n")
    s1 = input("Enter String 1:\n")
    s2 = input("Enter String 2:\n")

    compare_strings(s1, s2)
