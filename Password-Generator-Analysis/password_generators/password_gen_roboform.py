import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TARGET_COUNT = 100000
OUTPUT_FILE = "roboform_16_100K.txt"
URL = "https://www.roboform.com/password-generator"

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
        minus_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.counter-minus")))
        for _ in range(6):
            driver.execute_script("arguments[0].click();", minus_btn)
            time.sleep(0.05)
        time.sleep(0.5)
    except Exception as e:
        print(f"Warning adjusting minus button: {e}")

    # 3. Locate generate button
    generate_btn = wait.until(
        EC.presence_of_element_located((By.ID, "button-password"))
    )

    passwords_collected = 0
    time.sleep(10)
    with open(OUTPUT_FILE, "a", encoding="utf-8", buffering=1) as f:
        print(f"Started collection. Writing to {OUTPUT_FILE}...")
        
        while passwords_collected < TARGET_COUNT:

            try:
                generate_btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", generate_btn)


            try:
                wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "#password-field .slot15 li.password-letter").text.strip() != "")
            except Exception:

                continue


            password_text = driver.execute_script("""
                let pwd = '';
                for (let i = 0; i < 16; i++) {
                    let slot = document.querySelector('#password-field .slot' + i + ' li.password-letter');
                    if (slot && slot.textContent) {
                        pwd += slot.textContent.trim();
                    }
                }
                return pwd;
            """)


            if passwords_collected < 5:
                print(f"[DEBUG] Captured text (Len {len(password_text)}): '{password_text}'")


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