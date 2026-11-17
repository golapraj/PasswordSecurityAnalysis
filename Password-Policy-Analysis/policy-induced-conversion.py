"""
Reads a CSV file with a 'password' column and appends three new columns:
  UL    - password transformed to meet Uppercase + Lowercase policy
  ULN   - password transformed to meet UL + Number policy
  ULNSP - password transformed to meet ULN + Special character policy
"""

import csv
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Leet substitution tables
# ---------------------------------------------------------------------------

LEET_TO_NUMBER = [
    ("o", "0"), ("O", "0"),
    ("i", "1"), ("I", "1"),
    ("l", "1"), ("L", "1"),
    ("z", "2"), ("Z", "2"),
    ("e", "3"), ("E", "3"),
    ("a", "4"), ("A", "4"),
    ("s", "5"), ("S", "5"),
    ("g", "6"), ("G", "6"),
    ("t", "7"), ("T", "7"),
    ("b", "8"), ("B", "8"),
]

LEET_TO_SPECIAL = [
    ("a", "@"), ("A", "@"),
    ("s", "$"), ("S", "$"),
    ("i", "!"), ("I", "!"),
    ("e", "€"), ("E", "€"),
    ("o", "°"), ("O", "°"),
    ("l", "|"), ("L", "|"),
    ("c", "("), ("C", "("),
    ("t", "+"), ("T", "+"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def has_upper(s):
    if isinstance(s, list):
        s = "".join(s)
    return bool(re.search(r"[A-Z]", s))

def has_lower(s):
    if isinstance(s, list):
        s = "".join(s)
    return bool(re.search(r"[a-z]", s))

def has_number(s):
    if isinstance(s, list):
        s = "".join(s)
    return bool(re.search(r"[0-9]", s))

def has_special(s):
    if isinstance(s, list):
        s = "".join(s)
    return bool(re.search(r"[^a-zA-Z0-9]", s))


def apply_one_leet(chars, table, skip):
    for i, ch in enumerate(chars):
        if i in skip:
            continue
        for src, dst in table:
            if ch == src:
                new = chars[:]
                new[i] = dst
                return new, i
    return None, None


def capitalise_first(chars, skip):
    for i, ch in enumerate(chars):
        if i not in skip and ch.islower():
            new = chars[:]
            new[i] = ch.upper()
            return new, i
    for i, ch in enumerate(chars):
        if i not in skip and ch.isalpha():
            new = chars[:]
            new[i] = ch.upper()
            return new, i
    return chars, None


# ---------------------------------------------------------------------------
# Core transform
# ---------------------------------------------------------------------------

def transform(password: str, policy: str) -> str:
    """
    Return the minimally-modified password that satisfies `policy`.
    Uses substitutions first, then inserts missing character classes if necessary.
    Pads to minimum length 8.
    """
    chars = list(password.strip())
    ul_changed = set()  # indices changed by upper/lower fixes
    digit_idx = None

    # 1. Uppercase
    if not has_upper(chars):
        chars, idx = capitalise_first(chars, ul_changed)
        if idx is not None:
            ul_changed.add(idx)
        else:
            chars.append("A")
            ul_changed.add(len(chars)-1)

    # 2. Lowercase
    if not has_lower(chars):
        for i, ch in enumerate(chars):
            if i not in ul_changed and ch.isupper():
                chars[i] = ch.lower()
                ul_changed.add(i)
                break
        else:
            chars.append("a")
            ul_changed.add(len(chars)-1)

    # 3. Digit (ULN / ULNSP)
    if policy in ("ULN", "ULNSP") and not has_number(chars):
        new, idx = apply_one_leet(chars, LEET_TO_NUMBER, ul_changed)
        if new:
            chars = new
            digit_idx = idx
        else:
            chars.append("1")
            digit_idx = len(chars)-1

    # 4. Special char (ULNSP)
    if policy == "ULNSP" and not has_special(chars):
        sp_skip = ul_changed | ({digit_idx} if digit_idx is not None else set())
        new, idx = apply_one_leet(chars, LEET_TO_SPECIAL, sp_skip)
        if new:
            chars = new
        else:
            chars.append("!")

    # 5. Minimum length 8
    if len(chars) < 8:
        needed = "123"  
        while len(chars) < 8:
            chars.append(needed[len(chars) % len(needed)])

    return "".join(chars)


# ---------------------------------------------------------------------------
# CSV processing
# ---------------------------------------------------------------------------

def process_csv(input_path: str, output_path: str) -> None:
    in_path  = Path(input_path)
    out_path = Path(output_path)

    with in_path.open(newline="", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        if "password" not in (reader.fieldnames or []):
            raise ValueError("CSV must contain a 'password' column.")

        fieldnames = list(reader.fieldnames) + ["UL", "ULN", "ULNSP"]
        rows = []
        for row in reader:
            pw = row["password"].strip()
            row["UL"]    = transform(pw, "UL")
            row["ULN"]   = transform(pw, "ULN")
            row["ULNSP"] = transform(pw, "ULNSP")
            rows.append(row)

    with out_path.open("w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Done — {len(rows)} rows written to '{out_path}'")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    input_csv  = "breached/db-000webhost.csv"
    #input_csv  = "breached/db-rockyou.csv"  
    #input_csv = "breached/db-xato-net-10-million-passwords.csv"
    output_csv = str(Path(input_csv).stem) + "_converted.csv"

    process_csv(input_csv, output_csv)