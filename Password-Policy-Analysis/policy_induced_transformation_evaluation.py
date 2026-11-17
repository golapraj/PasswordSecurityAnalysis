import csv
import re
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from rapidfuzz.distance import Levenshtein,JaroWinkler
from zxcvbn import zxcvbn
import pandas as pd
import multiprocessing

# ============================================================================
# CONFIG
# ============================================================================

INPUT = "db-xato-net-10-million-passwords.csv"
OUTPUT = "db-xato-net-10-million-passwords_converted.csv"

#INPUT = "db-rockyou.csv"
#OUTPUT = "db-rockyou_converted.csv"

#INPUT = "db-000webhost.csv"
#OUTPUT = "db-000webhost_converted.csv"

PASSWORD_COLUMNS = ["password", "UL", "ULN", "ULNSP"]

# ============================================================================
# LEET TABLES
# ============================================================================

LEET_TO_NUMBER = [
    ("o", "0"), ("O", "0"),
    ("i", "1"), ("I", "1"),
    ("l", "1"), ("L", "1"),
    ("l", "7"), ("L", "7"),
    ("z", "2"), ("Z", "2"),
    ("e", "3"), ("E", "3"),
    ("a", "4"), ("A", "4"),
    ("s", "5"), ("S", "5"),
    ("g", "6"), ("G", "6"),
    ("g", "9"), ("G", "9"),
    ("t", "7"), ("T", "7"),
    ("b", "8"), ("B", "8"),
]

LEET_TO_SPECIAL = [
    ("a", "@"), ("A", "@"),
    ("c", "("), ("C", "("),
    ("c", "{"), ("C", "{"),
    ("c", "["), ("C", "["),
    ("c", "<"), ("C", "<"),
    ("s", "$"), ("S", "$"),
    ("i", "!"), ("I", "!"),
    ("i", "|"), ("I", "|"),
    ("e", "€"), ("E", "€"),
    ("x", "%"), ("X", "%"),
    ("l", "|"), ("L", "|"),
    ("t", "+"), ("T", "+"),
]

# ============================================================================
# POLICY HELPERS
# ============================================================================

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


def satisfies_policy(password, policy):

    if len(password) < 8:
        return False

    if not has_upper(password):
        return False

    if not has_lower(password):
        return False

    if policy in ("ULN", "ULNSP"):
        if not has_number(password):
            return False

    if policy == "ULNSP":
        if not has_special(password):
            return False

    return True


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

# ============================================================================
# PASSWORD TRANSFORMATION
# ============================================================================

def transform(password, policy):

    password = str(password).strip()

    # IMPORTANT:
    # If already compliant, return unchanged.
    if satisfies_policy(password, policy):
        return password

    chars = list(password)

    ul_changed = set()
    digit_idx = None

    # Uppercase
    if not has_upper(chars):

        chars, idx = capitalise_first(chars, ul_changed)

        if idx is not None:
            ul_changed.add(idx)
        else:
            chars.append("A")
            ul_changed.add(len(chars) - 1)

    # Lowercase
    if not has_lower(chars):

        for i, ch in enumerate(chars):

            if i not in ul_changed and ch.isupper():
                chars[i] = ch.lower()
                ul_changed.add(i)
                break

        else:
            chars.append("a")
            ul_changed.add(len(chars) - 1)

    # Number
    if policy in ("ULN", "ULNSP") and not has_number(chars):

        new, idx = apply_one_leet(
            chars,
            LEET_TO_NUMBER,
            ul_changed
        )

        if new:
            chars = new
            digit_idx = idx
        else:
            chars.append("1")
            digit_idx = len(chars) - 1

    # Special
    if policy == "ULNSP" and not has_special(chars):

        sp_skip = ul_changed

        if digit_idx is not None:
            sp_skip = sp_skip | {digit_idx}

        new, idx = apply_one_leet(
            chars,
            LEET_TO_SPECIAL,
            sp_skip
        )

        if new:
            chars = new
        else:
            chars.append("!")

    # Minimum length
    if len(chars) < 8:

        needed = "123"

        while len(chars) < 8:
            chars.append(
                needed[len(chars) % len(needed)]
            )

    return "".join(chars)

# ============================================================================
# ZXCVBN
# ============================================================================

def get_guesses(password):

    try:
        return zxcvbn(str(password))["guesses"]
    except Exception:
        return None


def process_column(values):

    workers = multiprocessing.cpu_count()

    with ProcessPoolExecutor(max_workers=workers) as executor:

        return list(
            executor.map(
                get_guesses,
                values,
                chunksize=500
            )
        )

# ============================================================================
# LEVENSHTEIN
# ============================================================================

def edit_distance(original, transformed):

    return Levenshtein.distance(
        str(original),
        str(transformed)
    )

def jw_similarity(original, transformed):
    return JaroWinkler.similarity(
        str(original),
        str(transformed)
    )
# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":

    print("Loading CSV...")
    df = pd.read_csv(INPUT)

    if "password" not in df.columns:
        raise ValueError("CSV must contain a 'password' column")

    print("Generating policy-compliant passwords...")

    df["UL"] = df["password"].apply(
        lambda x: transform(x, "UL")
    )

    df["ULN"] = df["password"].apply(
        lambda x: transform(x, "ULN")
    )

    df["ULNSP"] = df["password"].apply(
        lambda x: transform(x, "ULNSP")
    )

    print("Computing zxcvbn guesses...")

    for col in PASSWORD_COLUMNS:

        print(f"  {col}")

        df[f"g-{col}"] = process_column(
            df[col].astype(str)
        )

    print("Computing edit distances...")

    df["ed-UL"] = [
        edit_distance(a, b)
        for a, b in zip(df["password"], df["UL"])
    ]

    df["ed-ULN"] = [
        edit_distance(a, b)
        for a, b in zip(df["password"], df["ULN"])
    ]

    df["ed-ULNSP"] = [
        edit_distance(a, b)
        for a, b in zip(df["password"], df["ULNSP"])
    ]




    print("Computing Jaro-Winkler similarities...")

    df["jw-UL"] = [
        jw_similarity(a, b)
        for a, b in zip(df["password"], df["UL"])
    ]

    df["jw-ULN"] = [
        jw_similarity(a, b)
        for a, b in zip(df["password"], df["ULN"])
    ]

    df["jw-ULNSP"] = [
        jw_similarity(a, b)
        for a, b in zip(df["password"], df["ULNSP"])
    ]

    print("Writing output...")

    df.to_csv(
        OUTPUT,
        index=False
    )

    print(f"Done. Saved to {OUTPUT}")