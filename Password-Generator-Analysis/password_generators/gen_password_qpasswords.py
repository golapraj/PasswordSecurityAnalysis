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

    driver.get("https://www.qpasswords.com/")

    time.sleep(1)

    generate_btn = driver.find_element(By.ID, "generateBtn")
    driver.execute_script("arguments[0].click();", generate_btn)

    time.sleep(1)

    password_element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "passwordDisplay"))
    )

    password = driver.execute_script("return arguments[0].textContent;", password_element)

    password = password.strip() if password else ""

    print(f"Extracted Password: {password}")

    time.sleep(10)

    #Note remove the first two passwords from the resulting txt file, they are duplicates of the first password. If the result does not equal 100,000 regenerated more passwords

    for x in range(100002):
        password_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "passwordDisplay"))
        )
        
        password = driver.execute_script("return arguments[0].textContent;", password_element)
        
        password = password.strip() if password else ""

        with open("qpassword_16_100K.txt", "a") as file:
            file.write(password + "\n")
        generate_btn = driver.find_element(By.ID, "generateBtn")
        driver.execute_script("arguments[0].click();", generate_btn)

        time.sleep(5)
