from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
import time

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
for i in range(1):
    driver.get("https://www.lastpass.com/features/password-generator")

    time.sleep(3)

    length_input = driver.find_element(By.ID, "lp-pg-password-length")

    length_input.clear()
    length_input.send_keys(Keys.CONTROL + "a") 
    length_input.send_keys(Keys.BACKSPACE)    
    length_input.send_keys("16")             
    length_input.send_keys(Keys.ENTER)    

    password_field = driver.find_element(By.ID, "GENERATED-PASSWORD")

    password_text = password_field.get_attribute("value")

    print(f"The password is: {password_text}")

    generate_button = driver.find_element(By.XPATH, "//button[.//span[text()='Generate']]")
    print("Button Found")
    driver.execute_script("arguments[0].click();", generate_button)
    #generate_button.click()
    print("Button clicked")
    time.sleep(10)
    for x in range(100000):
        password_text = password_field.get_attribute("value")
        with open("lastpass_16_100K.txt", "a") as file:
            file.write(password_text + "\n")
        driver.execute_script("arguments[0].click();", generate_button)
        time.sleep(0.1)




    time.sleep(5)