import os
import time
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

import pandas as pd

# =====================
# Keywords
# =====================
LOGIN_HINTS = ["login", "log in", "signin", "sign in", "account", "sign-in"]
SIGNUP_HINTS = ["register", "sign up", "signup", "create account", "create an account", "join us", "create profile", "get started"]

# =====================
# Browser
# =====================
CHROMIUM_PATH = "/usr/bin/chromium-browser"

def start_browser():
    options = Options()
    options.binary_location = CHROMIUM_PATH
    #options.headless = False
    options.add_argument("--headless=new")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(15)  # max 15s per page load
    return driver

# =====================
# Utilities
# =====================
def normalize_url(url):
    if not url.startswith("http"):
        url = "https://" + url
    return url.rstrip("/")

def extract_visible_links(driver, base_url):
    """Extract all <a> links within the same domain."""
    soup = BeautifulSoup(driver.page_source, "html.parser")
    base_netloc = urlparse(base_url).netloc

    links = []
    for a in soup.find_all("a", href=True):
        full = urljoin(base_url, a["href"])
        if full:
            links.append({
                "url": full,
                "text": a.get_text(strip=True)
            })
    return links

def find_keyword_link(links, keywords):
    """Return link whose URL or text contains any keyword."""
    for link in links:
        combined = f"{link['url']} {link['text']}".lower()
        for kw in keywords:
            #print("KW:",kw," CMBD:", combined,"\n")
            if kw.lower() in combined:
                return link['url']
    return None

def find_clickable_keyword(driver, keywords):
    """Search all clickable elements for keywords."""
    try:
        elements = driver.find_elements(By.XPATH, "//*[self::a or self::button or self::div or self::span]")
        for el in elements:
            try:
                text = el.text.strip().lower()
                if any(kw.lower() in text for kw in keywords):
                    before = driver.current_url
                    el.click()
                    time.sleep(3)  # wait for navigation
                    after = driver.current_url
                    if after != before:
                        return after
            except Exception:
                continue
    except Exception:
        pass
    return None

# =====================
# Main agent
# =====================
def find_signup(base_url):
    base_url = normalize_url(base_url)
    driver = start_browser()

    # Open base URL
    try:
        #print(f"Opening {base_url}")
        driver.get(base_url)
        time.sleep(3)  # wait for JS
    except (TimeoutException, WebDriverException):
        driver.quit()
        return {"signup_url": "NO_DIRECT_SIGNUP_URL", "login_url": "NO_DIRECT_LOGIN_URL", "found_via": "timeout"}

    # Step 1: extract homepage links
    home_links = extract_visible_links(driver, base_url)

    # Step 2: detect login link
    login_url = find_keyword_link(home_links, LOGIN_HINTS)
    reg_url = find_keyword_link(home_links, SIGNUP_HINTS)

    #print("Login URL:",login_url, "\tReg URL:", reg_url,"\n")

    actual_login_url = login_url or "NO_DIRECT_LOGIN_URL"

    if login_url:
        try:
            driver.get(login_url)
            time.sleep(3)
            actual_login_url = driver.current_url
        except Exception:
            actual_login_url = login_url

    # Step 3: extract links again after navigating to login page
    auth_links = extract_visible_links(driver, driver.current_url)
    all_links = home_links + auth_links

    # Step 4: detect signup link in links
    signup_url = find_keyword_link(all_links, SIGNUP_HINTS)

    # Step 5: fallback: search all clickable elements
    if not signup_url:
        signup_url = find_clickable_keyword(driver, SIGNUP_HINTS)

    if not signup_url:
        signup_url = "NO_DIRECT_SIGNUP_URL"
        signup_url = reg_url or "NO_DIRECT_SIGNUP_URL"

    driver.quit()
    return {
        "signup_url": signup_url,
        "login_url": actual_login_url,
        "found_via": "keyword+js" if signup_url != "NO_DIRECT_SIGNUP_URL" else "keyword+js_failed"
    }

# =====================
# Run script
# =====================
def main(start=0, end=100, bs=100):
    # =====================
    # CONFIG
    # =====================
    START = start          
    END = end             
    batch_size = bs    

    INPUT_CSV = "tran_1M.csv"
    OUTPUT_FOLDER = "output"

    # =====================
    # LOAD DATA
    # =====================
    df = pd.read_csv(INPUT_CSV)

    df["signup_url"] = None
    df["login_url"] = None
    df["found_via"] = None
    df["crawl_status"] = None

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    total_rows = min(END, len(df))

    signup_count = 0
    login_count = 0
    # =====================
    # MAIN LOOP
    # =====================
    for idx in range(START, total_rows):
        domain = df.at[idx, "url"]
        print(f"\nProcessing row {idx+1}/{total_rows}: {domain}")

        try:
            result = find_signup(domain)

            df.at[idx, "signup_url"] = result.get("signup_url", "NO_DIRECT_SIGNUP_URL")
            df.at[idx, "login_url"] = result.get("login_url", "NO_DIRECT_LOGIN_URL")
            df.at[idx, "found_via"] = result.get("found_via", "unknown")
            df.at[idx, "crawl_status"] = "success"

        except Exception as e:
            print(f"Failed for {domain}: {e}")
            df.at[idx, "signup_url"] = "NO_DIRECT_SIGNUP_URL"
            df.at[idx, "login_url"] = "NO_DIRECT_LOGIN_URL"
            df.at[idx, "found_via"] = "error"
            df.at[idx, "crawl_status"] = "failed"


        #NOT FOUND COUNT
        if df.at[idx, "signup_url"] == "NO_DIRECT_SIGNUP_URL":
            signup_count = signup_count + 1
        if df.at[idx, "login_url"] == "NO_DIRECT_LOGIN_URL":
            login_count = login_count + 1

        # =====================
        # BATCH SAVE
        # =====================
        processed = idx - START + 1
        is_batch_end = processed % batch_size == 0
        is_final = idx + 1 == total_rows

        if is_batch_end or is_final:
            batch_end = idx + 1
            batch_start = batch_end - batch_size + 1
            batch_start = max(batch_start, START + 1)

            filename = f"tran_{batch_start}_{batch_end}.csv"
            filepath = os.path.join(OUTPUT_FOLDER, filename)

            df.iloc[batch_start-1:batch_end].to_csv(filepath, index=False)
            print(f"Saved batch → {filename}","\n",f"Signup NOT found so far: {signup_count} / {processed}","\n",f"Login NOT found so far: {login_count} / {processed}")

    # =====================
    # FINAL SAVE
    # =====================
    final_path = os.path.join(OUTPUT_FOLDER, "R_tran_1M.csv")
    df.iloc[START:total_rows].to_csv(final_path, index=False)

    print("\nCrawl complete.")
    print(f"Final results saved to {final_path}")



#main(360000, 400001, 1000)
#main(870000, 885001, 1000)
#main(879000, 882001, 1000)
#main(774000, 775001, 1000)
