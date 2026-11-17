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
for i in range (1):
    
    driver.get("https://www.expressvpn.com/password-generator?srsltid=AfmBOorVvJc4PvUnwxghIh01YIsvucJ_2ioqSwbGj2IrFGtru9Hl7_e1")

    time.sleep(3)

    slider_thumb = driver.find_element(By.ID, "slider")

    slider_thumb.click()

    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)


    time.sleep(3)

    password_selector = "p.text-xl.font-light.flex-wrap"


    time.sleep(3)
    wait = WebDriverWait(driver, 5)

    password_input = driver.find_element(By.ID, "single-pw-display")

    # Extract the text currently sitting inside the input field
    password_text = password_input.get_attribute("value")

    print(f"Generated Password: {password_text}")

    regen_button = driver.find_element(By.CSS_SELECTOR, "button.gen-pw-btn")
    regen_button.click()
    print("Button clicked")

    time.sleep(10)
    for x in range(100000):
        password_selector = "p.text-xl.font-light.flex-wrap"
        password_input = driver.find_element(By.ID, "single-pw-display")

    # Extract the text currently sitting inside the input field
        password_text = password_input.get_attribute("value")
        with open("expressVPN_ULD.txt", "a") as file:
            file.write(password_text + "\n")
        regen_button = driver.find_element(By.CSS_SELECTOR, "button.gen-pw-btn")
        regen_button.click()
        time.sleep(0.01)




time.sleep(5)