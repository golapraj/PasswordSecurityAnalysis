import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TARGET_COUNT = 100000
OUTPUT_FILE = "liquidweb_16_100K.txt"
URL = "https://www.liquidweb.com/tools/secure-password-generator/"

# Configure Chrome Options to bypass detection
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")


def safe_click(driver, element):
    """
    Attempts a regular Selenium click. If intercepted by an overlay/popup, 
    dismisses potential popups and falls back to a JavaScript click.
    """
    try:
        element.click()
    except Exception:

        try:
            close_buttons = driver.find_elements(
                By.XPATH, 
                "//button[contains(@class, 'close') or contains(@aria-label, 'Close') or text()='×']"
            )
            for btn in close_buttons:
                if btn.is_displayed():
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(0.2)
        except Exception:
            pass


        driver.execute_script("arguments[0].click();", element)


try:

    driver.get(URL)
    wait = WebDriverWait(driver, 10)


    try:
        cookie_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(@id, 'accept')]"))
        )
        cookie_btn.click()
        time.sleep(0.5)
    except Exception:
        pass


    try:
        first_char_symbol = wait.until(EC.presence_of_element_located((By.ID, "firstCharSymbol")))
        if not first_char_symbol.is_selected():
            driver.execute_script("arguments[0].click();", first_char_symbol)

        other_char_symbol = wait.until(EC.presence_of_element_located((By.ID, "otherCharSymbol")))
        if not other_char_symbol.is_selected():
            driver.execute_script("arguments[0].click();", other_char_symbol)
            
        time.sleep(0.5)
    except Exception as e:
        print(f"Warning handling checkboxes: {e}")


    generate_btn = wait.until(
        EC.presence_of_element_located((By.XPATH, "//button[@type='submit' and normalize-space()='Generate']"))
    )

    password_box = wait.until(
        EC.presence_of_element_located((By.ID, "password"))
    )
    time.sleep(10)
    passwords_collected = 0

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        while passwords_collected < TARGET_COUNT:
            try:

                safe_click(driver, generate_btn)
                time.sleep(0.05)


                password_text = password_box.get_attribute("value")
                if not password_text:
                    password_text = password_box.text.strip()

                if not password_text:
                    continue


                f.write(password_text + "\n")

                passwords_collected += 1
                if passwords_collected % 100 == 0 or passwords_collected == TARGET_COUNT:
                    print(f"Collected: {passwords_collected} / {TARGET_COUNT}")

            except Exception as e:

                try:
                    generate_btn = driver.find_element(By.XPATH, "//button[@type='submit' and normalize-space()='Generate']")
                except Exception:
                    pass
                continue

    print(f"Successfully saved {passwords_collected} passwords to {OUTPUT_FILE}.")

finally:
    driver.quit()