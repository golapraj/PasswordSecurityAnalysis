"""
Converts a raw password policy CSV into a structured CSV.
"""

import csv
import re
import ast
import argparse


FIELDS = [
    "sl", "url",
    "Uppercase Required", "Lowercase Required", "Number Required",
    "Special Char Required", "Special Chars Forbidden",
    "Min Length", "Max Length",
    "Check Common/Breached", "No Repeating Chars",
    "No Sequential Chars", "Strength Meter", "Full Policy"
]

# Word-to-digit map for written-out numbers
WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20,
}
_WORD_NUM_PAT = "|".join(WORD_TO_NUM.keys())
 
 
def to_int(value: str) -> int:
    """Convert a digit string or word number to int."""
    v = value.strip().lower()
    if v.isdigit():
        return int(v)
    return WORD_TO_NUM.get(v, None)


def parse_policy(policy_text: str) -> dict:
    try:
        policies = ast.literal_eval(policy_text)
    except Exception:
        policies = [policy_text]

    combined = " ".join(policies).lower()

    result = {
        "Uppercase Required":      "No",
        "Lowercase Required":      "No",
        "Number Required":         "No",
        "Special Char Required":   "No",
        "Special Chars Forbidden": "No",
        "Min Length":              "",
        "Max Length":              "",
        "Check Common/Breached":   "No",
        "No Repeating Chars":      "No",
        "No Sequential Chars":     "No",
        "Strength Meter":          "No",
        "Full Policy":            policy_text
    }

    if re.search(r"upper\s*case|uppercase|capital letter|big letter", combined):
        result["Uppercase Required"] = "Yes"

    if re.search(r"lower\s*case|lowercase|small letter", combined):
        result["Lowercase Required"] = "Yes"

    if re.search(r"\bnumber\b|\bdigit\b|\bnumeric\b|contain.*number|at least.*number|0-9", combined):
        result["Number Required"] = "Yes"

    # Check forbidden BEFORE required (some policies explicitly ban special chars)
    if re.search(r"special characters? are not allowed", combined):
        result["Special Chars Forbidden"] = "Yes"
    elif re.search(r"special char|symbol|punctuation|\blike ! and &\b|!@#|\$%|one special", combined):
        result["Special Char Required"] = "Yes"

    # ------------------------------------------------------------------ #
    # Length extraction
    # ------------------------------------------------------------------ #
    NUM = rf"(\d+|{_WORD_NUM_PAT})(?:\s*\(\d+\))?"   # matches digit string OR word number
    min_len = None
    max_len = None
 
    def search(pat, text=combined):
        return re.search(pat, text, re.IGNORECASE)
 
    # --- Range patterns (both min and max) ---
 

    m = search(rf"(\d+)\s*[-–]\s*(\d+)\s*(?:alphanumeric\s+)?(?:characters?|chars?|digits?|letters?)?")
    if m:
        min_len, max_len = int(m.group(1)), int(m.group(2))
 

    if min_len is None:
        m = search(rf"between\s+{NUM}\s+(?:and|to)\s+{NUM}")
        if m:
            min_len = to_int(m.group(1))
            max_len = to_int(m.group(2))
 
    # "length should be between 6-20"
 
    # "grater/greater then/than X and less then/than Y"
    if min_len is None:
        m = search(rf"gr[ae]a?ter\s+th[ae]n\s+{NUM}\s+and\s+less\s+th[ae]n\s+{NUM}")
        if m:
            min_len = to_int(m.group(1))
            max_len = to_int(m.group(2))
 
    # "min. 4, max. 20" / "min 4 max 20"
    if min_len is None:
        m = search(rf"min\.?\s*{NUM}[,\s]+max\.?\s*{NUM}")
        if m:
            min_len = to_int(m.group(1))
            max_len = to_int(m.group(2))
 
    # --- Min-only patterns ---
    if min_len is None:
        min_patterns = [
            # "a length of at least 8" / "at least three characters in length"
            rf"(?:a\s+)?length\s+of\s+at\s+least\s+{NUM}",
            rf"at\s+least\s+{NUM}\s+(?:characters?|chars?|digits?|letters?)\s+(?:long\s+)?(?:in\s+length)?",
            rf"at\s+least\s+{NUM}\s+(?:characters?|chars?|digits?|letters?)?",
            # "least be six (6) characters"
            rf"least\s+be\s+{NUM}(?:\s*\(\d+\))?\s*(?:characters?|chars?)",
            # "X or more characters" (digit or word)
            rf"{NUM}\s+or\s+more\s+(?:characters?|chars?|digits?|letters?)",
            # "contain 8 or more"
            rf"contain\s+{NUM}\s+or\s+more",
            # "must have at least X"
            rf"must\s+have\s+at\s+least\s+{NUM}",
            # "must be at least X" / "must be min. X"
            rf"must\s+(?:be|contain|to\s+be)\s+(?:at\s+least\s+)?{NUM}",
            # "(minimum eight characters)"
            rf"\(?minimum\s+{NUM}\s*(?:characters?|chars?|digits?|letters?)?\)?",
            # "minimum password length is 6" / "minimum 8"
            rf"minimum(?:\s+\w+){{0,3}}?\s+(?:is\s+)?{NUM}",
            # "8 character minimum"
            rf"{NUM}\s+(?:character|char|digit|letter)s?\s+minimum",
            # "no less than 6" / "no fewer than 6"
            rf"no\s+(?:less|fewer)\s+than\s+{NUM}",
            # "greater/grater than X"
            rf"gr[ae]a?ter\s+th[ae]n\s+{NUM}",
            # "please enter 6 or more" / "be 6 or more"
            rf"(?:enter|be)\s+{NUM}\s+or\s+more",
            # "characters: 8"
            rf"characters?:\s*{NUM}",
            # "longer than X" / "more than X characters"
            rf"(?:longer|more)\s+than\s+{NUM}\s*(?:characters?|chars?|digits?)?",
            # "password is seven or more characters"
            rf"is\s+{NUM}\s+or\s+more\s+(?:characters?|chars?)",
            # "minimum 8 letters & numbers"
            rf"minimum\s+{NUM}\s+(?:letters?|characters?|chars?|digits?)",
            # "shorter than minimum string length (4 < 6)"
            rf"shorter than minimum.*?\(\d+\s*<\s*{NUM}\)",
            # fallback: plain "X characters" / "X+ characters"
            rf"{NUM}\+?\s*(?:characters?|chars?|digits?|letters?(?:\s*[&and]+\s*numbers?)?)(?:\s+or\s+more)?",
        ]
        for pat in min_patterns:
            m = search(pat)
            if m:
                val = to_int(m.group(1))
                if val is not None:
                    min_len = val
                    break
 

    if max_len is None:
        max_patterns = [
            rf"(?:up\s+to|maximum|no\s+more\s+than|at\s+most)\s+{NUM}\s*(?:characters?|chars?)",
            rf"(?<!no )less\s+th[ae]n\s+{NUM}\s*(?:characters?|chars?)?",
        ]
        for pat in max_patterns:
            m = search(pat)
            if m:
                val = to_int(m.group(1))
                if val is not None:
                    max_len = val
                    break
 
    if min_len is not None:
        result["Min Length"] = min_len
    if max_len is not None:
        result["Max Length"] = max_len

    if re.search(r"common(?:ly used)?|breach(?:ed)?|compromised|list of passwords|commonly used on other|(?:found|exposed|leaked) in data breaches?", combined):
        result["Check Common/Breached"] = "Yes"

    if re.search(r"repeat(?:ing)?\s*char|no.*repeat|aaa|111", combined):
        result["No Repeating Chars"] = "Yes"

    if re.search(r"sequential\s*char|ex:.*abc|ex:.*123", combined):
        result["No Sequential Chars"] = "Yes"

    if re.search(r"too weak|very weak|better password|excellent|strength|strong enough", combined):
        result["Strength Meter"] = "Yes"


    return result


def main():
    parser = argparse.ArgumentParser(description="Parse password policy CSV to structured CSV.")
    parser.add_argument("--input",  default="output2.csv", help="Path to input CSV")
    parser.add_argument("--output", default="password_policies_structured.csv", help="Path to output CSV")
    args = parser.parse_args()

    rows = []
    with open(args.input, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("policy") and row["policy"].strip():
                parsed = parse_policy(row["policy"])
                rows.append({"sl": row["sl"], "url": row["url"], **parsed})

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved: {args.output}  ({len(rows):,} rows)")


if __name__ == "__main__":
    main()
