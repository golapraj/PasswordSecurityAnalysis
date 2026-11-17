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

    driver.get("https://www.bitdefender.com/en-us/consumer/password-generator")

    time.sleep(3)

    #length_input = driver.find_element(By.CSS_SELECTOR, "input.slider_counter__l513ozd")

   


    '''
    driver.execute_script("""
        arguments[0].value = '12';
    """, length_input)


    #length_input.send_keys(Keys.ENTER) 

    time.sleep(3)


    length_input.clear()
    length_input.send_keys(Keys.CONTROL + "a") 
    length_input.send_keys(Keys.BACKSPACE)
    driver.execute_script("""
        arguments[0].value = '12';
    """, length_input)
    time.sleep(2)    
    length_input.send_keys("")
    time.sleep(2)
    #length_input.send_keys(Keys.BACKSPACE)
    time.sleep(2)              
    length_input.send_keys(Keys.ENTER)    
    '''
    password_input = driver.find_element(By.CLASS_NAME, "password-generator--input")

    # Extract the generated password value
    generated_password = password_input.get_attribute("value")
    print(generated_password)




    time.sleep(10)

    retry_button = driver.find_element(By.CLASS_NAME, "password-generator--input-retry")
    retry_button.click()



    for x in range(100000):
        password_input = driver.find_element(By.CLASS_NAME, "password-generator--input")
        
            # Extract the generated password value
        generated_password = password_input.get_attribute("value")
        with open("bitdefender_16_100K.txt", "a") as file:
            file.write(generated_password + "\n")
        retry_button = driver.find_element(By.CLASS_NAME, "password-generator--input-retry")
        retry_button.click()
        time.sleep(0.01)




    time.sleep(5)