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

    driver.get("https://us.norton.com/feature/password-generator")

    time.sleep(3)

    
    minus_btn = driver.find_element(By.XPATH, "//img[@alt='Minus Icon']")
    minus_btn.click()
    minus_btn.click()
    minus_btn.click()
    minus_btn.click()
    

    time.sleep(1)

    password_field = driver.find_element(By.CLASS_NAME, "c-password-generator_password-text")

    password_text = password_field.text

    print(f"The password is: {password_text}")

    generate_button = driver.find_element(By.CLASS_NAME, "c-password-generator_refresh-password")
    print("Button Found")
    driver.execute_script("arguments[0].click();", generate_button)
    print("Button clicked")
    time.sleep(15)
    for x in range(100000):
        password_text = password_field.text
        with open("norton_16_100K.txt", "a") as file:
            file.write(password_text + "\n")
        driver.execute_script("arguments[0].click();", generate_button)
        time.sleep(0.1)
