import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyperclip

TARGET_COUNT = 100000
OUTPUT_FILE = "keygen_16_100K.txt"

# create Chromeoptions instance 
options = webdriver.ChromeOptions() 

# adding argument to disable the AutomationControlled flag 
options.add_argument("--disable-blink-features=AutomationControlled") 

# exclude the collection of enable-automation switches 
options.add_experimental_option("excludeSwitches", ["enable-automation"]) 

# turn-off userAutomationExtension 
options.add_experimental_option("useAutomationExtension", False) 

# setting the driver path and requesting a page 
driver = webdriver.Chrome(options=options) 

# changing the property of the navigator value for webdriver to undefined 
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 

try:

    driver.get("https://randomkeygen.com/bulk-password-generator")
    wait = WebDriverWait(driver, 10)


    try:
        special_chars_btn = wait.until(
            EC.element_to_be_clickable((
                By.XPATH, 
                "//button[contains(., 'Special') or contains(., 'Symbols') or contains(., 'Characters')] | "
                "//label[contains(., 'Special') or contains(., 'Symbols') or contains(., 'Characters')]"
            ))
        )
        special_chars_btn.click()
        time.sleep(0.5)
    except Exception as e:
        print("Note: Could not locate special characters button directly. Proceeding with current configuration.")

    count_500_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '500')] | //label[contains(text(), '500')]"))
    )
    count_500_btn.click()
    time.sleep(10)
    passwords_collected = 0

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        while passwords_collected < TARGET_COUNT:

            generate_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and contains(@class, 'password-generator--input-retry')] | //button[contains(text(), 'Generate')]"))
            )
            generate_btn.click()


            time.sleep(1)


            copy_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Copy All']"))
            )
            copy_btn.click()


            copied_text = pyperclip.paste().strip()

            if not copied_text:
                print("Clipboard was empty. Retrying...")
                continue


            batch = copied_text.splitlines()


            for pwd in batch:
                f.write(pwd + "\n")

            passwords_collected += len(batch)
            print(f"Collected: {passwords_collected} / {TARGET_COUNT}")

    print(f"Successfully saved {passwords_collected} passwords to {OUTPUT_FILE}.")

finally:
    driver.quit()