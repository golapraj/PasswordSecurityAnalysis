import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TARGET_COUNT = 100000
OUTPUT_FILE = "fsecure_16_100K.txt"
URL = "https://www.f-secure.com/us-en/password-generator"

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
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow all')]"))
        )
        cookie_btn.click()
        time.sleep(0.5)
    except Exception:
        pass


    shadow_root = None
    try:
        shadow_host = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "password-generator, [id*='password-generator']")))
        shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)
    except Exception:
        pass

    minus_button_xpath = "//*[local-name()='svg' and .//*[contains(@d, 'M18 14H8')]]/ancestor::button"

    decrease_btn = None
    if shadow_root:
        try:
            decrease_btn = shadow_root.find_element(By.CSS_SELECTOR, "button:has(svg path[d*='M18 14H8'])")
        except Exception:
            pass

    if not decrease_btn:
        decrease_btn = wait.until(EC.element_to_be_clickable((By.XPATH, minus_button_xpath)))

    #sets length
    for _ in range(16):
        decrease_btn.click()
        time.sleep(0.05)

    time.sleep(0.5)

    passwords_collected = 0
    time.sleep(10)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        while passwords_collected < TARGET_COUNT:

            try:
                if shadow_root:
                    generate_btn = shadow_root.find_element(By.CSS_SELECTOR, "button[class*='generate'], #generate-btn")
                else:
                    generate_btn = driver.find_element(By.XPATH, "//button[contains(., 'Generate')]")
            except Exception:
                generate_btn = driver.find_element(By.XPATH, "//button[contains(., 'Generate')]")

            generate_btn.click()
            time.sleep(0.01)


            try:
                if shadow_root:
                    pwd_input = shadow_root.find_element(By.CSS_SELECTOR, "input[readonly]")
                else:
                    pwd_input = driver.find_element(By.CSS_SELECTOR, "input[readonly]")
                
                password_text = pwd_input.get_attribute("value")
            except Exception:

                pwd_input = driver.find_element(By.XPATH, "//input[@readonly and contains(@class, 'byVlTM')]")
                password_text = pwd_input.get_attribute("value")

            if not password_text:
                print("Password input was empty. Retrying...")
                continue


            f.write(password_text + "\n")

            passwords_collected += 1
            if passwords_collected % 100 == 0 or passwords_collected == TARGET_COUNT:
                print(f"Collected: {passwords_collected} / {TARGET_COUNT}")

    print(f"Successfully saved {passwords_collected} passwords to {OUTPUT_FILE}.")

finally:
    driver.quit()