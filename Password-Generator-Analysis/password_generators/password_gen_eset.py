from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
import time
#Preventing captchas from interrupting the generation
#create Chromeoptions instance 
options = webdriver.ChromeOptions() 
 
#adding argument to disable the AutomationControlled flag 
options.add_argument("--disable-blink-features=AutomationControlled") 
 
#exclude the collection of enable-automation switches 
options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
 
#turn-off userAutomationExtension 
options.add_experimental_option("useAutomationExtension", False) 
 
#setting the driver path and requesting a page 
driver = webdriver.Chrome(options=options) 
 
#changing the property of the navigator value for webdriver to undefined 
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 

#Password Generation Code
for i in range(1):
    
    driver.get("https://www.eset.com/us/password-generator/?cjdata=MXxOfDB8WXww&ref=AFC-CJ&attr=100357191&pub=14462142&shop=cba-a193e43e-b184-4ff8-8841-cca52adbe632&utm_source=100357191&utm_medium=affiliate&utm_content=14462142&cjevent=5b49c84b38ff11f182b801ad0a82b820")

    time.sleep(3)

    shadow_host = driver.find_element(By.CSS_SELECTOR, "eset-pwd-generator")

    shadow_root = driver.execute_script('return arguments[0].shadowRoot', shadow_host)

    slider = shadow_root.find_element(By.ID, "slider")

    slider.click()

    for _ in range(26):
        slider.send_keys(Keys.ARROW_LEFT)

    password_field = shadow_root.find_element(By.ID, "pwd-input")

    password_text = password_field.get_attribute("textContent")


    print(f"The password is: {password_text}")
    print("\n" + str(password_text))

    time.sleep(1)

    generate_button = shadow_root.find_element(By.CSS_SELECTOR, ".icon-regenerate")
    print("Button Found")
    generate_button.click()
    print("Button clicked")
    time.sleep(1)

    password_field = shadow_root.find_element(By.ID, "pwd-input")
    password_text = password_field.get_attribute("textContent")

    print(f"The password is: {password_text}")
    print("\n" + str(password_text))


    time.sleep(10)
    for x in range(100000):
        password_field = shadow_root.find_element(By.ID, "pwd-input")
        password_text = password_field.get_attribute("textContent")
        with open("eset_16_100K.txt", "a") as file:
            file.write(str(password_text) + "\n")
        generate_button.click()
        time.sleep(0.01)




time.sleep(1)