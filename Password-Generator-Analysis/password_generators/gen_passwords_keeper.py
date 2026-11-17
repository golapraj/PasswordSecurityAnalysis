import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TARGET_COUNT = 100000
OUTPUT_FILE = "keeper_16_100K.txt"
URL = "https://www.keepersecurity.com/features/password-generator/"

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
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(@id, 'accept')]"))
        )
        cookie_btn.click()
        time.sleep(0.5)
    except Exception:
        pass


    slider = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.password-strength__slider")))
    slider.click()

    for _ in range(38):
        slider.send_keys(Keys.ARROW_LEFT)
        time.sleep(0.02)

    time.sleep(0.5)


    generate_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.tumbling_dice"))
    )
    password_box = wait.until(
        EC.presence_of_element_located((By.ID, "strongPassword"))
    )

    passwords_collected = 0
    time.sleep(10)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        while passwords_collected < TARGET_COUNT:

            generate_btn.click()
            time.sleep(0.1)


            password_text = password_box.get_attribute("value")

            if not password_text:
                continue


            f.write(password_text + "\n")

            passwords_collected += 1
            if passwords_collected % 100 == 0 or passwords_collected == TARGET_COUNT:
                print(f"Collected: {passwords_collected} / {TARGET_COUNT}")

    print(f"Successfully saved {passwords_collected} passwords to {OUTPUT_FILE}.")

finally:
    driver.quit()