import time
import json
import re
from enum import Enum

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

import random
import string
import time


# =====================================================
# CONFIG
# =====================================================
CHROMIUM_PATH = "/usr/bin/chromium-browser"
HEADLESS = True

def generate_username(
    prefix="user",
    min_length=8,
    max_length=16,
    allow_underscore=True
):
    """
    Dynamically generate a valid username.
    """

    # base entropy using timestamp
    timestamp_part = str(int(time.time()))[-5:]

    # allowed characters
    chars = string.ascii_lowercase + string.digits
    if allow_underscore:
        chars += "_"

    # random filler
    random_length = random.randint(
        max(0, min_length - len(prefix) - len(timestamp_part)),
        max_length - len(prefix) - len(timestamp_part)
    )

    random_part = "".join(random.choices(chars, k=random_length))

    username = f"{prefix}{random_part}{timestamp_part}"

    # ensure first char is letter
    if username[0].isdigit():
        username = "u" + username

    return username[:max_length]



DEFAULT_VALUES = {
    "email": f"user{int(time.time())}@gmail.com",
    "username": generate_username(),
    "name": "Test User",
    "first_name": "Test",
    "last_name": "User",
    "gender": "male",
    "organization": "MyTestCompany",
    "phone": "1234567890"
}


# =====================================================
# BROWSER
# =====================================================

def start_browser():
    options = Options()
    options.binary_location = CHROMIUM_PATH
    #options.headless = HEADLESS
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    return webdriver.Chrome(options=options)


# =====================================================
# JS VALIDATION HOOK
# =====================================================

def inject_js_hooks(driver):
    driver.execute_script("""
        window.__validationErrors = [];
        const orig = HTMLInputElement.prototype.setCustomValidity;
        HTMLInputElement.prototype.setCustomValidity = function(msg) {
            if (msg) window.__validationErrors.push(msg);
            return orig.call(this, msg);
        };
    """)

def get_js_errors(driver):
    return driver.execute_script("return window.__validationErrors || []")


# =====================================================
# FIELD EXTRACTION
# =====================================================


XPATH_INTERACTIVE = """
//input[not(@type='hidden')] |
 //textarea |
 //select |
 //*[@role='textbox'] |
 //*[@role='combobox'] |
 //*[@contenteditable='true'] |
 //*[@aria-autocomplete] |
 //*[@role='button']
"""

def extract_fields(driver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input"))
    )

    elements = driver.find_elements(By.XPATH, XPATH_INTERACTIVE)
    fields = []

    for idx, el in enumerate(elements):
        if not el.is_displayed():
            continue

        fields.append({
            "index": idx,
            "tag": el.tag_name,
            "type": el.get_attribute("type"),
            "name": el.get_attribute("name"),
            "id": el.get_attribute("id"),
            "placeholder": el.get_attribute("placeholder"),
            "aria_label": el.get_attribute("aria-label"),
            "text": el.text.strip()
        })

    return fields, elements


# =====================================================
# FIELD CLASSIFICATION
# =====================================================


def classify_fields(fields, elements, driver):

    classified = {"fields": []}

    # ------------------------------------------------
    # KEYWORD DICTIONARY
    # ------------------------------------------------

    KEYWORDS = {

        "email": [
            "email", "e-mail"
        ],

        "username": [
            "username", "user_name", "handle",
            "login", "user-id"
        ],

        "password": [
            "password", "passwd", "passcode"
        ],

        "first_name": [
            "first", "firstname", "given"
        ],

        "last_name": [
            "last", "lastname", "surname",
            "family"
        ],

        "name": [
            "name", "fullname", "displayname"
        ],

        "phone": [
            "phone", "mobile", "tel", "telephone"
        ],

        "gender": [
            "gender", "sex"
        ],

        "date_of_birth": [
            "dob", "birth", "birthday",
            "birthdate"
        ]
    }

    # ------------------------------------------------
    # DOB keywords (critical for React forms)
    # ------------------------------------------------

    DOB_KEYWORDS = [
        "month",
        "day",
        "year",
        "birth",
        "birthday",
        "dob"
    ]

    # ------------------------------------------------
    # Regex patterns
    # ------------------------------------------------

    EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    PHONE_REGEX = re.compile(r"\+?[0-9]{7,15}")

    # ------------------------------------------------
    # Month list for select detection
    # ------------------------------------------------

    DOB_MONTHS = [
        "jan","january","feb","february","mar","march",
        "apr","april","may","jun","june","jul","july",
        "aug","august","sep","september","oct","october",
        "nov","november","dec","december"
    ]

    # ------------------------------------------------
    # Helper: build text blob
    # ------------------------------------------------

    def build_blob(field):

        parts = [
            field.get("name"),
            field.get("id"),
            field.get("placeholder"),
            field.get("aria_label"),
            field.get("text"),
            field.get("type"),
            field.get("pattern")
        ]

        return " ".join(
            [str(p).lower() for p in parts if p]
        )

    # ------------------------------------------------
    # Helper: get label text
    # ------------------------------------------------

    def get_label_text(field):

        field_id = field.get("id")

        if not field_id:
            return ""

        try:
            label = driver.find_element(
                By.XPATH,
                f"//label[@for='{field_id}']"
            )
            return label.text.lower()

        except:
            return ""

    # ------------------------------------------------
    # Helper: detect DOB select
    # ------------------------------------------------

    def detect_dob_select(element):

        try:

            options = element.find_elements(By.TAG_NAME, "option")

            texts = [
                o.text.strip().lower()
                for o in options
            ]

            # Month dropdown
            if any(m in texts for m in DOB_MONTHS):
                return True

            # Day dropdown (1–31)
            nums = [
                int(t) for t in texts
                if t.isdigit()
            ]

            if nums and min(nums) == 1 and max(nums) >= 28:
                return True

            # Year dropdown
            years = [
                int(t) for t in texts
                if t.isdigit() and 1900 <= int(t) <= 2100
            ]

            if len(years) > 10:
                return True

        except:
            pass

        return False


    # ------------------------------------------------
    # MAIN CLASSIFICATION LOOP
    # ------------------------------------------------

    for f in fields:

        idx = f["index"]

        tag = (f.get("tag") or "").lower()
        ftype = (f.get("type") or "").lower()

        placeholder = (f.get("placeholder") or "").lower()
        pattern = (f.get("pattern") or "").lower()

        blob = build_blob(f)
        label = get_label_text(f)

        blob = blob + " " + label

        category = "unknown"

        # --------------------------------------------
        # Strong HTML type detection
        # --------------------------------------------

        if ftype == "email":
            category = "email"

        elif ftype == "password":
            category = "password"

        elif ftype == "tel":
            category = "phone"

        elif ftype == "checkbox":
            category = "checkbox"

        elif ftype == "submit":
            category = "submit"

        elif ftype == "radio":

            if any(k in blob for k in ["male","female","gender"]):
                category = "gender"


        # --------------------------------------------
        # Regex-based detection
        # --------------------------------------------

        if category == "unknown":

            if EMAIL_REGEX.search(placeholder) or "@" in pattern:
                category = "email"

            elif PHONE_REGEX.search(placeholder):
                category = "phone"


        # --------------------------------------------
        # Keyword detection
        # --------------------------------------------

        if category == "unknown":

            for cat, words in KEYWORDS.items():

                if any(w in blob for w in words):
                    category = cat
                    break


        # --------------------------------------------
        # DOB keyword detection (React / Stripe fix)
        # --------------------------------------------

        if category == "unknown":

            if any(k in blob for k in DOB_KEYWORDS):
                category = "date_of_birth"


        # --------------------------------------------
        # DOB select detection
        # --------------------------------------------

        if category == "unknown" and tag == "select":

            element = elements[idx]

            if detect_dob_select(element):
                category = "date_of_birth"


        # --------------------------------------------
        # First/Last name fallback
        # --------------------------------------------

        if category == "unknown":

            if "first" in blob:
                category = "first_name"

            elif "last" in blob:
                category = "last_name"


        classified["fields"].append({
            "index": idx,
            "category": category
        })


    return classified


# =====================================================
# DOB HANDLING (YOUR WORKING LOGIC — FIXED & STABLE)
# =====================================================



def fill_dob(driver, elements, classified):
    """
    Universal DOB handler.
    Works on:
    - (Jan / Feb / Mar <select>)
    - (ARIA combobox)
    - <input type="date">
    - React-controlled inputs
    """

    dob_meta = [
        f for f in classified["fields"]
        if f["category"] == "date_of_birth"
        and f["index"] < len(elements)
    ]

    if not dob_meta:
        return False

    dob_elements = [elements[f["index"]] for f in dob_meta]

    YEAR = "2000"
    DAY = "1"

    # ---------------------------------
    # CASE 1: Native <input type="date">
    # ---------------------------------
    if len(dob_elements) == 1:
        el = dob_elements[0]
        tag = el.tag_name.lower()
        el_type = (el.get_attribute("type") or "").lower()

        try:
            if tag == "input" and el_type == "date":
                driver.execute_script(
                    """
                    arguments[0].value = '2000-01-01';
                    arguments[0].dispatchEvent(new Event('input', {bubbles:true}));
                    arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
                    """,
                    el
                )
                return True
        except:
            pass

        # Text DOB fallback
        try:
            el.clear()
            for fmt in ["01/01/2000", "2000-01-01", "01-01-2000"]:
                el.send_keys(fmt)
                time.sleep(0.4)
                if el.get_attribute("value"):
                    return True
        except:
            pass

        return False

    # ---------------------------------
    # CASE 2: <select>s
    # ---------------------------------
    selects = [el for el in dob_elements if el.tag_name.lower() == "select"]

    if len(selects) >= 3:
        try:
            for el in selects:
                name = (el.get_attribute("name") or "").lower()
                sel = Select(el)

                options_text = [o.text.strip().lower() for o in sel.options]

                # --- Month ---
                if "month" in name:
                    for opt in sel.options:
                        t = opt.text.strip().lower()
                        if t in ["jan", "january", "1", "01"]:
                            sel.select_by_visible_text(opt.text)
                            break
                    else:
                        sel.select_by_index(1)  # fallback

                # --- Year ---
                elif "year" in name:
                    if YEAR in options_text:
                        sel.select_by_visible_text(YEAR)
                    else:
                        sel.select_by_index(1)

                # --- Day ---
                elif "day" in name:
                    if DAY in options_text:
                        sel.select_by_visible_text(DAY)
                    else:
                        sel.select_by_index(1)


                # --- Unknown select (fallback by content) ---
                else:
                    if YEAR in options_text:
                        sel.select_by_visible_text(YEAR)
                    elif DAY in options_text:
                        sel.select_by_visible_text(DAY)
                    else:
                        sel.select_by_index(18)

            return True
        except Exception as e:
            print("[DOB DEBUG] select failed:", e)

    # ---------------------------------
    # CASE 3: ARIA combobox
    # ---------------------------------
    dob_elements = dob_elements[:3]  # Month / Day / Year order
    values = ["Jan", DAY, YEAR]

    for el, value in zip(dob_elements, values):
        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", el
            )
            time.sleep(0.3)

            role = (el.get_attribute("role") or "").lower()
            tag = el.tag_name.lower()

            # ARIA dropdown
            if role in ["combobox", "button"]:
                el.click()
                time.sleep(0.6)

                # Try exact match
                options = driver.find_elements(
                    By.XPATH,
                    f"//*[@role='option' and normalize-space(text())='{value}']"
                )

                if options:
                    options[0].click()
                else:
                    all_opts = driver.find_elements(By.XPATH, "//*[@role='option']")
                    if all_opts:
                        all_opts[0].click()

                time.sleep(0.4)
                continue

            # Plain input fallback
            if tag == "input":
                el.clear()
                el.send_keys(value)
                el.send_keys(Keys.TAB)

        except Exception as e:
            print("[DOB DEBUG] ARIA error:", e)
            continue

    # Blur to trigger validation
    driver.execute_script("document.activeElement.blur();")
    time.sleep(0.4)

    return True




# =====================================================
# NON-PASSWORD FIELDS
# =====================================================

def fill_non_password_fields(driver, elements, classified):
    """
    Filler for all non-password fields, including:
    - Text inputs (first/last name, email, phone, username)
    - Checkboxes
    - Select/dropdowns
    - ARIA comboboxes / button dropdowns
    - Radio buttons for gender
    """

    for f in classified["fields"]:
        idx = f["index"]
        cat = f["category"]

        if cat in ["password", "gender"]:
            continue  
        if idx >= len(elements):
            continue

        el = elements[idx]
        tag = el.tag_name.lower()
        role = (el.get_attribute("role") or "").lower()
        el_type = (el.get_attribute("type") or "").lower()

        try:
            # Text inputs
            if tag == "input" and el_type in ["text", "email", "tel", "number", "search", "url"]:
                if cat in DEFAULT_VALUES:

                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    driver.execute_script("arguments[0].focus();", el)

                    time.sleep(0.2)

                    el.clear()
                    el.send_keys(DEFAULT_VALUES[cat])
                continue

            # Checkboxes
            if tag == "input" and el_type == "checkbox":
                if DEFAULT_VALUES.get(cat, True) and not el.is_selected():
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    el.click()
                    time.sleep(0.1)
                continue

            # Native select
            if tag == "select" and cat in DEFAULT_VALUES:
                sel = Select(el)
                target = DEFAULT_VALUES[cat].lower()
                for option in sel.options:
                    text = option.text.strip().lower()
                    if target in text:
                        sel.select_by_visible_text(option.text)
                        break
                continue

            # ARIA combobox / button dropdown
            if role in ["combobox", "button"] and cat in DEFAULT_VALUES:
                el.click()
                time.sleep(0.3)
                options = driver.find_elements(By.XPATH, "//*[@role='option']")
                matched = False
                target = DEFAULT_VALUES[cat].lower()
                for opt in options:
                    if target in opt.text.strip().lower():
                        opt.click()
                        matched = True
                        break
                if not matched and options:
                    options[0].click()
                continue

            # Fallback input
            if tag == "input" and cat in DEFAULT_VALUES:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                driver.execute_script("arguments[0].focus();", el)
                time.sleep(0.2)
                el.clear()
                el.send_keys(DEFAULT_VALUES[cat])
                continue

            # Textarea fallback
            if tag == "textarea" and cat in DEFAULT_VALUES:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                driver.execute_script("arguments[0].focus();", el)
                time.sleep(0.2)

                el.clear()
                el.send_keys(DEFAULT_VALUES[cat])
                continue

        except Exception as e:
            print(f"[DEBUG] Error filling '{cat}' at index {idx}: {e}")
            continue

    # -----------------------------
    # gender
    # -----------------------------
    male_indicators = ["male", "m", "man"]

    gender_radios = [
        elements[f["index"]] for f in classified["fields"] if f["category"] == "gender"
    ]

    for idx, el in enumerate(gender_radios):
        try:
            el_value = (el.get_attribute("value") or "").lower()
            el_aria = (el.get_attribute("aria-label") or "").lower()
            el_id = (el.get_attribute("id") or "").lower()
            el_name = (el.get_attribute("name") or "").lower()
            label_text = ""
            label = None
            try:
                label = el.find_element("xpath", "ancestor::label")
                label_text = label.text.strip().lower()
            except:
                pass

            # Check for Male indicators
            if any(ind in s for ind in male_indicators for s in [el_value, el_aria, el_id, el_name, label_text]):
                if el.is_displayed() and el.is_enabled():
                    el.click()
                    #print(f"[DEBUG] Clicked Male radio [{idx}] via input")
                elif label:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", label)
                    label.click()
                    #print(f"[DEBUG] Clicked Male radio [{idx}] via label")
                else:
                    pass
                    #print(f"[DEBUG] Cannot click Male radio [{idx}]")
                time.sleep(0.2)
                break  # STOP after selecting Male

        except Exception as e:
            print(f"[DEBUG] Error clicking gender radio [{idx}]: {e}")
            continue





def find_signup_context(driver):

    best_score = 0
    best_frame = None

    frames = driver.find_elements(By.XPATH, "//iframe")

    contexts = [None] + frames

    for frame in contexts:

        try:
            if frame:
                driver.switch_to.frame(frame)

            score = 0

            password_fields = driver.find_elements(By.XPATH, "//input[@type='password']")
            email_fields = driver.find_elements(By.XPATH, "//input[@type='email']")
            text_fields = driver.find_elements(By.XPATH, "//input[@type='text']")
            submit_buttons = driver.find_elements(By.XPATH, "//button | //input[@type='submit']")

            score += len(password_fields) * 5
            score += len(email_fields) * 4
            score += min(len(text_fields), 3) * 2
            score += min(len(submit_buttons), 2) * 2

            labels = driver.find_elements(By.XPATH, "//label")
            for l in labels:
                if "password" in (l.text or "").lower():
                    score += 2

            if score > best_score:
                best_score = score
                best_frame = frame

            if frame:
                driver.switch_to.default_content()

        except:
            driver.switch_to.default_content()

    if best_frame:
        driver.switch_to.frame(best_frame)
        

    else:
        pass
        

    return best_score

# =====================================================
# PASSWORD PROBES (DIFFERENTIAL TESTING)
# =====================================================

def generate_password_probes():
    return [
        ("len_1", "1"),
        ("len_4", "1111"),
        ("len_6", "123456"),
        ("len_8", "12345678"),
        ("lower_digit", "aaaaaaa1"),
        ("upper_digit", "1234567A"),
        ("lower_upper", "aaaaAAAA"),
        ("symbol", "aaaaaaa!"),
        ("lower_upper_digit", "aaaaaaA1"),
        ("len_10", "1234567890")
    ]


# =====================================================
# SNAPSHOT + RESET
# =====================================================

def snapshot_visible_text(driver):
    body = driver.find_element(By.TAG_NAME, "body")
    lines = set()

    for line in body.text.splitlines():
        cleaned = " ".join(line.strip().split())  # normalize spaces
        if cleaned:
            lines.add(cleaned)

    return lines


def reset_page(driver):
    driver.refresh()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input"))
    )
    inject_js_hooks(driver)
    time.sleep(1)
    _, elements = extract_fields(driver)
    return elements


# =====================================================
# PASSWORD ATTEMPT (ISOLATED)
# =====================================================

def fill_password(elements, classified, password):
    for f in classified["fields"]:
        if f["category"] == "password":

            idx = f["index"]

            if idx >= len(elements):
                continue

            el = elements[idx]

            #el = elements[f["index"]]
            try:
                el.clear()
                el.send_keys(password)
                el.send_keys(Keys.TAB)
            except Exception as e:
                print("[DEBUG] Password fill failed:", e)


def click_submit(driver):
    """
    Click the primary submit button on any registration form,
    avoiding social OAuth buttons.
    """
    oauth_keywords = ["google", "apple", "facebook", "github", "twitter"]
    submit_keywords = ["create account", "sign up", "register", "submit", "continue", "create", "join", "next", "get started", "start", "let's go", "sign me up",   "create my account",    "create new account", "register now", "sign up now", "complete registration", "create profile", "create user", "create new profile", "create new user", "finish", "Submit"]

    elements = driver.find_elements(
        By.XPATH,
        "//button | //input[@type='submit']"
    )

    # ---- keyword-based detection ----
    for el in elements:
        try:
            if not el.is_displayed() or not el.is_enabled():
                continue

            text = (el.text or "").lower()
            value = (el.get_attribute("value") or "").lower()
            aria = (el.get_attribute("aria-label") or "").lower()

            combined = f"{text} {value} {aria}"

            if any(k in combined for k in oauth_keywords):
                continue

            if any(k in combined for k in submit_keywords):
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", el
                )
                el.click()
                return True

        except:
            continue


    # ---- ONLY real form submits ----
    for el in elements:
        try:
            if not el.is_displayed() or not el.is_enabled():
                continue

            tag = el.tag_name.lower()
            el_type = (el.get_attribute("type") or "").lower()

            if tag == "button" or el_type == "submit":
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", el
                )
                el.click()
                return True

        except:
            continue

    return False


def attempt_password(driver, elements, classified, label, password):
    before_url = driver.current_url
    before_html = driver.page_source
    before_text = snapshot_visible_text(driver)
    fill_password( elements, classified, password)
    time.sleep(0.5)

    clicked = click_submit(driver)
    if not clicked:
        print("No submit button found.")
    time.sleep(2)  # wait for potential validation to trigger

    after_url = driver.current_url
    after_html = driver.page_source
    after_text = snapshot_visible_text(driver)

    #print("\nAfter Text:", after_text)  

    js_errors = get_js_errors(driver)

    # Detect page reload or validation response
    url_changed = (before_url != after_url)
    #page_changed = (before_html != after_html)
    new_lines = set(after_text) - set(before_text)
    page_changed = len(new_lines) > 0
    
    # Extract common server-side validation keywords
    error_lines = []
    for line in new_lines:
        lower = line.lower()

        if any(eword in lower for eword in [
            "username",
            "is available",
        ]):
            continue

        if any(word in lower for word in [
            "password",
            "invalid",
            "must",
            "required",
            "error",
            "use",
            "common",
            "incorrect",
            "at least",
            "minimum",
            "maximum",
            "uppercase",
            "lowercase",
            "upper case",
            "lower case",
            "number",
            "digit",
            "special",
            "symbol",
            "character",
            "length",
            "alpha",
            "alphanumeric",
            "whitespace",
            "no",
            "need",
            "weak",
            "strong"
        ]):
            error_lines.append(line.strip())

    return {
        "label": label,
        "password": password,
        "after_submit_page_changed": page_changed,
        "after_submit_url_changed": url_changed,
        "after_submit_new_url": after_url if url_changed else None,
        "after_submit_validation_errors": list(set(error_lines)),
        "js_errors": js_errors
    }


# =====================================================
# CONSTRAINT EXTRACTION
# =====================================================

def extract_constraints(elements, classified):
    constraints = []
    for f in classified["fields"]:
        if f["category"] == "password":
            el = elements[f["index"]]
            for attr in ["minlength", "maxlength", "pattern"]:
                val = el.get_attribute(attr)
                if val:
                    constraints.append({
                        "attribute": attr,
                        "value": val
                    })
    return constraints


def extract_visible_password_rules(driver, elements, classified):
    """
    Extract only meaningful password policy lines.
    Avoid collecting full container text or unrelated UI content.
    """

    rule_keywords = [
        "at least",
        "minimum",
        "maximum",
        "must",
        "uppercase",
        "lowercase",
        "upper case",
        "lower case",
        "number",
        "digit",
        "special",
        "symbol",
        "character",
        "characters",
        "length",
        "alpha",
        "alphanumeric",
        "whitespace",
            "require",
            "need",
            "should",
            "password must",
            "password should",
            "password require",
            "no"
    ]

    rules = set()

    for f in classified["fields"]:
        if f["category"] != "password":
            continue

        idx = f["index"]
        if idx >= len(elements):
            continue

        password_el = elements[idx]

        # Look for nearby rule elements (siblings within same form)
        try:
            form = password_el.find_element(By.XPATH, "ancestor::form")
        except:
            form = driver


        candidates = form.find_elements(
            By.XPATH,
            ".//*[self::li or self::p or self::span or self::div]"
        )

        #print("Candidates found:", len(candidates))  # Debugging candidates

        for el in candidates:
            try:
                if not el.is_displayed():
                    continue

                text = el.text.strip()

                # Skip very long blocks (language dropdown etc.)
                if len(text) > 200:
                    continue

                # Must contain rule keyword
                if not any(k in text.lower() for k in rule_keywords):
                    continue

                result = {line for line in text.split("\n") if line.strip()}
                rules.update(result)

            except Exception as e:
                print(f"Error in processing element: {e}")
                continue

    filtered_rules = [item for item in list(rules) if len(item.split()) > 1]

    return filtered_rules


def extract_visible_password_rules2(driver, elements, classified):
    """
    Extract password rules globally (Cloudflare-compatible).
    """

    rule_keywords = [
        "at least",
        "minimum",
        "maximum",
        "must",
        "uppercase",
        "lowercase",
        "upper case",
        "lower case",
        "number",
        "digit",
        "special",
        "symbol",
        "character",
        "characters",
        "length",
        "alpha",
        "alphanumeric",
        "whitespace",
            "require",
            "need",
            "should",
            "password must",
            "password should",
            "password require",
            "no"
    ]

    rule_excludes = ["username", "is available", "is available.", "product updates","Terms of Service","Privacy Policy", "country", "America", "United States", "United States of America", "Language", "receive notifications", "Contact"]

    rules = set()

    # Look across entire page
    candidates = driver.find_elements(
        By.XPATH,
        "//*[self::li or self::p or self::span or self::div]"
    )

    for el in candidates:
        try:
            if not el.is_displayed():
                continue

            text = el.text.strip()
            
            if len(text) > 200:
                continue

            if not any(k in text.lower() for k in rule_keywords):
                continue

            for line in text.split("\n"):
                clean = line.strip()
                #print("Candidate rule line:", clean)  # Debugging output
                if any(kl in clean.lower() for kl in rule_excludes) or len(clean.split()) < 2:
                    continue
                else:
                    rules.add(clean)
                    #print("Added rule:", clean)  # Debugging output

                #if len(clean.split()) > 1:
                #    rules.add(clean)
                

        except:
            continue

    return list(rules)



# =====================================================
# MAIN
# =====================================================

def run_agent(url):
    driver = start_browser()
    driver.get(url)
    time.sleep(5)

    find_signup_context(driver)
    

    WebDriverWait(driver, 20).until(
    EC.presence_of_element_located(
        (By.XPATH, "//input | //*[@role='textbox']")
     )
    )

    inject_js_hooks(driver)

    fields, elements = extract_fields(driver)

    inputs = driver.find_elements(By.XPATH, "//input")

    #print("Total inputs detected:", len(inputs))

    #for i, el in enumerate(inputs[:10]):
    #    print(
    #    i,
    #    el.get_attribute("type"),
    #    el.get_attribute("name"),
    #    el.get_attribute("id"),
    #    el.get_attribute("placeholder")
    #)


    classified = classify_fields(fields, elements, driver)
    #print("classified fields:", classified)
    if not any(f["category"] == "password" for f in classified["fields"]):
        print("No password field detected. Exiting.")
        driver.quit()

        return {
        "url": url,
        "password_field_detected": False,
        "constraints": None,
        "static_rules": None,
        "attempts": None
        }
    
    static_rules = extract_visible_password_rules2(driver,elements, classified)

    fill_non_password_fields(driver, elements, classified)
    fill_dob(driver, elements, classified)
    time.sleep(0.5)


    constraints = extract_constraints(elements, classified)

    attempts = []

    for label, password in generate_password_probes():
        elements = reset_page(driver)

        fill_non_password_fields(driver, elements, classified)
        fill_dob(driver, elements, classified)
        time.sleep(0.5)

        result = attempt_password(driver, elements, classified, label, password)
        attempts.append(result)

        if (not result["after_submit_validation_errors"] and not result["js_errors"] and not result["after_submit_url_changed"]):
            driver.quit()
            break

    driver.quit()

    return {
        "url": url,
        "password_field_detected": True,
        "constraints": constraints,
        "static_rules": static_rules,
        "attempts": attempts
    }


if __name__ == "__main__":
    result = run_agent(URL)
    print(json.dumps(result, indent=2))
