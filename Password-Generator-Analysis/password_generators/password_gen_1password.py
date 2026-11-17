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

    driver.get("https://1password.com/password-generator")

    time.sleep(3)

    #length_input = driver.find_element(By.CSS_SELECTOR, "input.slider_counter__l513ozd")

    slider_thumb = driver.find_element(By.ID, "random-character-count")

    slider_thumb.click()

    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)
    slider_thumb.send_keys(Keys.ARROW_LEFT)

   


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
    symbols_toggle = driver.find_element(By.ID, "random-symbols")
    symbols_toggle.click()




    time.sleep(3)

    #password_field = driver.find_element(By.CSS_SELECTOR, "p.text-iron-ore-700")
    #password_field = driver.find_element(By.CSS_SELECTOR, "section h2")
    #password_field = driver.find_element(By.CSS_SELECTOR, "p.text-xl.font-light.flex-wrap")
    password_selector = "p.text-xl.font-light.flex-wrap"


    time.sleep(3)
    wait = WebDriverWait(driver, 5)
    password_el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, password_selector)))

    password_text = password_el.get_attribute("textContent").strip()
    #password_text = password_field.text

    print(f"The password is: {password_text}")

    refresh_btn = driver.find_element(By.ID, "refresh-password")
    print("Button Found")
    refresh_btn.click()
    #generate_button.click()
    print("Button clicked")
    time.sleep(10)

    for x in range(100000):
        password_selector = "p.text-xl.font-light.flex-wrap"
        wait = WebDriverWait(driver, 5)
        password_el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, password_selector)))
        # password_field = driver.find_element(By.CSS_SELECTOR, "p.text-xl.font-light.flex-wrap")
        #password_field = driver.find_element(By.CSS_SELECTOR, "section h2")
        #password_field = driver.find_element(By.CSS_SELECTOR, "p.text-iron-ore-700")
        #password_text = password_field.text
        password_text = password_el.get_attribute("textContent").strip()
        with open("1password_16_100K.txt", "a") as file:
            file.write(password_text + "\n")
        refresh_btn = driver.find_element(By.ID, "refresh-password")
        refresh_btn.click()
        time.sleep(0.01)




    time.sleep(5)