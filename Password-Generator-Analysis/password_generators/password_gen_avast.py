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
    driver.get("https://www.avast.com/random-password-generator#pc")

    time.sleep(3)

    #length_input = driver.find_element(By.CSS_SELECTOR, "input.slider_counter__l513ozd")

    slider_handle = driver.find_element(By.CLASS_NAME, "c-pwd-gen__slider")

    slider_handle.click()

    slider_handle.send_keys(Keys.ARROW_LEFT)
    slider_handle.send_keys(Keys.ARROW_LEFT)
    slider_handle.send_keys(Keys.ARROW_LEFT)
    slider_handle.send_keys(Keys.ARROW_LEFT)
    slider_handle.send_keys(Keys.ARROW_LEFT)
    slider_handle.send_keys(Keys.ARROW_LEFT)
    slider_handle.send_keys(Keys.ARROW_LEFT)
    slider_handle.send_keys(Keys.ARROW_LEFT)
    slider_handle.send_keys(Keys.ARROW_LEFT)
    slider_handle.send_keys(Keys.ARROW_LEFT)




    checkbox = driver.find_element(By.CSS_SELECTOR, "input[id^='randompasswordgenerator'][id$='specials']")
    checkbox.click()






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
    #symbols_toggle = driver.find_element(By.ID, "random-symbols")
    #symbols_toggle.click()




    time.sleep(3)

    #password_field = driver.find_element(By.CSS_SELECTOR, "p.text-iron-ore-700")
    #password_field = driver.find_element(By.CSS_SELECTOR, "section h2")
    #password_field = driver.find_element(By.CSS_SELECTOR, "p.text-xl.font-light.flex-wrap")
    password_selector = "p.text-xl.font-light.flex-wrap"


    time.sleep(3)
    wait = WebDriverWait(driver, 5)
    """
    password_el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, password_selector)))

    password_text = password_el.get_attribute("textContent").strip()
    #password_text = password_field.text

    print(f"The password is: {password_text}")
    """
    password_input = driver.find_element(By.CSS_SELECTOR, "input.c-pwd-gen__password-generated")

    # Extract the actual password string
    password_text = password_input.get_attribute("value")
    print(f"Password: {password_text}")


    regen_button = driver.find_element(By.CSS_SELECTOR, "button.c-pwd-gen__icon-refresh")
    regen_button.click()
    #generate_button.click()
    print("Button clicked")

    time.sleep(10)
    for x in range(100000):
        password_selector = "p.text-xl.font-light.flex-wrap"
        #wait = WebDriverWait(driver, 5)
        password_input = driver.find_element(By.CSS_SELECTOR, "input.c-pwd-gen__password-generated")

    # Extract the actual password string
        password_text = password_input.get_attribute("value")
        with open("avast_16_100K.txt", "a") as file:
            file.write(password_text + "\n")
        regen_button = driver.find_element(By.CSS_SELECTOR, "button.c-pwd-gen__icon-refresh")
        regen_button.click()
        time.sleep(0.1)




    time.sleep(5)