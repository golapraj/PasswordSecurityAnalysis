import time
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TARGET_COUNT = 100000
OUTPUT_FILE = "kaspersky_16_100K.txt"
URL = "https://password.kaspersky.com/password-generator/"

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
        cookie_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(@id, 'accept') or contains(text(), 'Allow')]"))
        )
        cookie_btn.click()
        time.sleep(0.5)
    except Exception:
        pass

    try:
        slider = wait.until(EC.element_to_be_clickable((By.ID, "slider")))
        slider.click()

        for _ in range(2):
            slider.send_keys(Keys.ARROW_RIGHT)
            time.sleep(0.02)

        time.sleep(0.5)
    except Exception:
        pass


    generate_btn = wait.until(
        EC.presence_of_element_located((By.ID, "generate-btn"))
    )

    copy_btn = wait.until(
        EC.presence_of_element_located((By.ID, "copy-btn"))
    )

    passwords_collected = 0
    time.sleep(10)

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        while passwords_collected < TARGET_COUNT:

            try:
                generate_btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", generate_btn)

            time.sleep(1)


            try:
                copy_btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", copy_btn)

            time.sleep(0.02)


            password_text = pyperclip.paste().strip()

            if not password_text:
                continue


            f.write(password_text + "\n")
            f.flush()

            passwords_collected += 1
            if passwords_collected % 100 == 0 or passwords_collected == TARGET_COUNT:
                print(f"Collected: {passwords_collected} / {TARGET_COUNT}")

    print(f"Successfully saved {passwords_collected} passwords to {OUTPUT_FILE}.")

finally:
    driver.quit()