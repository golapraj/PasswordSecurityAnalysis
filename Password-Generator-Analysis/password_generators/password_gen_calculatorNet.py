import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TARGET_COUNT = 100000
OUTPUT_FILE = "calculatornet_16_100K.txt"
URL = "https://www.calculator.net/password-generator.html"

# Configure Chrome Options
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

try:

    driver.get(URL)
    wait = WebDriverWait(driver, 10)


    try:

        brackets_input = wait.until(EC.presence_of_element_located((By.ID, "iexcludeb")))
        if brackets_input.is_selected():
            brackets_cbmark = driver.find_element(By.XPATH, "//label[@for='iexcludeb']//span[@class='cbmark']")
            try:
                brackets_cbmark.click()
            except Exception:
                driver.execute_script("arguments[0].click();", brackets_cbmark)


        ambiguous_input = wait.until(EC.presence_of_element_located((By.ID, "iexclude")))
        if ambiguous_input.is_selected():
            ambiguous_cbmark = driver.find_element(By.XPATH, "//label[@for='iexclude']//span[@class='cbmark']")
            try:
                ambiguous_cbmark.click()
            except Exception:
                driver.execute_script("arguments[0].click();", ambiguous_cbmark)

        time.sleep(0.3)
    except Exception as e:
        print(f"Warning handling checkbox states: {e}")


    try:
        slider = wait.until(EC.presence_of_element_located((By.NAME, "lenrange")))
        slider.click()

        for _ in range(6):
            slider.send_keys(Keys.ARROW_RIGHT)
            time.sleep(0.02)

        driver.execute_script("arguments[0].value = 16; doSliding(16);", slider)
        time.sleep(0.5)
    except Exception as e:
        print(f"Warning adjusting range slider: {e}")

    # 4. Locate regenerate link
    regenerate_btn = wait.until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@onclick, 'generatePass')]"))
    )

    passwords_collected = 0
    time.sleep(10)

    with open(OUTPUT_FILE, "a", encoding="utf-8", buffering=1) as f:
        print(f"Started collection. Writing to {OUTPUT_FILE}...")

        while passwords_collected < TARGET_COUNT:

            try:
                regenerate_btn.click()
            except Exception:
                driver.execute_script("generatePass();")


            try:
                password_element = wait.until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div.verybigtext"))
                )
                wait.until(lambda d: password_element.text.strip() != "")
                time.sleep(0.5)
                password_text = password_element.text.strip()
            except Exception:

                password_text = driver.execute_script(
                    "return document.querySelector('div.verybigtext')?.textContent.trim();"
                )

            if not password_text or len(password_text) != 16:
                continue


            f.write(password_text + "\n")
            f.flush()

            passwords_collected += 1
            if passwords_collected % 100 == 0 or passwords_collected == TARGET_COUNT:
                print(f"Collected: {passwords_collected} / {TARGET_COUNT}")

    print(f"Successfully saved {passwords_collected} passwords to {OUTPUT_FILE}.")

finally:
    driver.quit()