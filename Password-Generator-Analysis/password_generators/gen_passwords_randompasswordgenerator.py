import time
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TARGET_COUNT = 100000
OUTPUT_FILE = "randompasswordgenerator_16_100K.txt"
URL = "https://randompasswordgenerator.com/?length=16&numbers=1&lcase=1&ucase=1&lbegin=0&nodup=0&noseq=0&qty=100&symbols=IUAqJD8mJV8uLTosIicpKDs9Lz57fVtdK3w8I15gfg&nosim=0"

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

    driver.get(URL)
    wait = WebDriverWait(driver, 10)

    passwords_collected = 0
    time.sleep(10)

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        while passwords_collected < TARGET_COUNT:

            generate_btn = wait.until(
                EC.element_to_be_clickable((By.ID, "generate-button-footer"))
            )
            generate_btn.click()


            time.sleep(0.2)


            copy_btn = wait.until(
                EC.element_to_be_clickable((By.ID, "copy-button-footer"))
            )
            copy_btn.click()


            time.sleep(0.2)


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