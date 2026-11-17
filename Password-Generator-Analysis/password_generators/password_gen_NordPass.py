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

    driver.get("https://nordpass.com/password-generator/")

    time.sleep(3)

    slider_handle = driver.find_element(By.CSS_SELECTOR, "[aria-label='Password length']")

    slider_handle.click()

    slider_handle.send_keys(Keys.ARROW_LEFT)
    slider_handle.send_keys(Keys.ARROW_LEFT)
    slider_handle.send_keys(Keys.ARROW_LEFT)
    slider_handle.send_keys(Keys.ARROW_LEFT)





    checkbox = driver.find_element(By.CSS_SELECTOR, "[data-testid='password-generator-checkbox-ambiguous']")
    checkbox.click()


    time.sleep(3)

    password_selector = "p.text-xl.font-light.flex-wrap"


    time.sleep(3)
    wait = WebDriverWait(driver, 5)
    password_element = driver.find_element(By.CSS_SELECTOR, "p.body-lg-medium.break-all")

    # Extract the text inside it
    generated_password = password_element.text

    print(f"Captured Password: {generated_password}")


    regen_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='password-generator-regenerate-button']")
    regen_button.click()
    print("Button clicked")

    time.sleep(10)
    for x in range(100000):
        password_selector = "p.text-xl.font-light.flex-wrap"
        password_element = driver.find_element(By.CSS_SELECTOR, "p.body-lg-medium.break-all")

    # Extract the text inside it
        generated_password = password_element.text
        with open("NordPass_16_100K.txt", "a") as file:
            file.write(generated_password + "\n")
        regen_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='password-generator-regenerate-button']")
        regen_button.click()
        time.sleep(0.01)




    time.sleep(5)