import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TARGET_COUNT = 1000
OUTPUT_FILE = "dashlane_ULSP.txt"
URL = "https://www.dashlane.com/features/password-generator"

# Configure Chrome Options
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

try:
    # 1. Open website
    driver.get(URL)
    wait = WebDriverWait(driver, 10)

    # 2. Dismiss cookie banner if present
    try:
        cookie_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow all')]"))
        )
        cookie_btn.click()
        time.sleep(0.5)
    except Exception:
        pass

    # 3. Click ONLY the specific Symbols toggle label
    # Targets the label directly adjacent to/parent of the 'Symbols (@&$!#?)' text span
    symbols_label = wait.until(
        EC.element_to_be_clickable((
            By.XPATH, 
            "//span[contains(., 'Symbols') and contains(., '(@&$!#?)')]/ancestor::div[contains(@class, 'flex')]//label"
        ))
    )
    symbols_label.click()
    time.sleep(0.5)

    # 4. Locate refresh button and password input field
    refresh_btn = wait.until(
        EC.element_to_be_clickable((
            By.XPATH, 
            "//img[@alt='action-refresh']/ancestor::button | //img[@alt='action-refresh']"
        ))
    )
    time.sleep(10)
    password_input = wait.until(
        EC.presence_of_element_located((
            By.XPATH, 
            "//input[contains(@class, 'wk-h5')] | //input[contains(@class, 'bg-transparent') and @value]"
        ))
    )

    passwords_collected = 0

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        while passwords_collected < TARGET_COUNT:
            # Click refresh button
            refresh_btn.click()
            time.sleep(0.001)

            # Extract password from value attribute
            password_text = password_input.get_attribute("value")

            if not password_text:
                continue

            # Write password to file
            f.write(password_text + "\n")

            passwords_collected += 1
            if passwords_collected % 100 == 0 or passwords_collected == TARGET_COUNT:
                print(f"Collected: {passwords_collected} / {TARGET_COUNT}")

    print(f"Successfully saved {passwords_collected} passwords to {OUTPUT_FILE}.")

finally:
    driver.quit()