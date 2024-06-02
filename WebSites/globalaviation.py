from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from subprocess import CREATE_NO_WINDOW


class Globalaviation:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        chrome_service = webdriver.ChromeService()
        chrome_service.creation_flags = CREATE_NO_WINDOW

        self.driver = webdriver.Chrome(options=options, service=chrome_service)

        self.delay = 20

        self.logged_in = False
        self.status = "OK"

    def __del__(self):
        self.driver.quit()

    def login_function(self, login, password):
        self.driver.delete_all_cookies()
        try:
            self.driver.get("https://globalaviation.aero/gappcom-2/")
        except TimeoutException:
            self.status = "Time error"
            return self.status
        except WebDriverException:
            self.status = "Connection error"
            return self.status

        input_user_name = self.driver.find_element(By.XPATH, "//input[@name='login:username']")
        input_password = self.driver.find_element(By.XPATH, "//input[@name='login:password']")
        login_button = self.driver.find_element(By.XPATH, "//input[@name='login:login']")

        input_user_name.send_keys(login)
        input_password.send_keys(password)

        login_button.click()
        self.logged_in = True
        self.status = "OK"

        try:
            self.driver.find_element(By.XPATH, "//span[@class='rf-msgs-sum']")
            self.status = "Login error"
            self.logged_in = False
        except NoSuchElementException:
            pass

        self.driver.find_element(By.XPATH, "//td[@id='form1:StockGA:header']").click()

        try:
            WebDriverWait(self.driver, self.delay).until(
                ec.invisibility_of_element_located((By.XPATH, "//div[@id='loading_content']")))
        except TimeoutException:
            self.status = "Time error"

        return self.status

    def search_part(self, number, search_results):
        if not self.logged_in:
            self.status = "Login error"
            return self.status

        self.status = "OK"

        search_section_button = self.driver.find_element(By.XPATH, "//td[@id='form1:StockGA:header']")
        search_section_button.click()

        try:
            WebDriverWait(self.driver, self.delay).until(
                ec.invisibility_of_element_located((By.XPATH, "//div[@id='loading_content']")))
        except TimeoutException:
            self.status = "Time error"
            return self.status

        part_number_input = self.driver.find_element(By.XPATH, "//textarea[@name='gaform:s10area']")
        part_number_input.clear()
        part_number_input.send_keys(number)

        search_button = self.driver.find_element(By.XPATH, "//input[@name='gaform:j_idt99']")
        search_button.click()

        try:
            WebDriverWait(self.driver, self.delay).until(
                ec.invisibility_of_element_located((By.XPATH, "//div[@id='loading_content']")))
        except TimeoutException:
            self.status = "Time error"
            return self.status

        try:
            part_info = self.driver.find_element(By.XPATH, "//tr[@id='gaform:rstable:0:subrstable:0']")
        except NoSuchElementException:
            return self.status

        _, _, part_number, description, qty, _, condition, _, _, price, _, lead_time, _, _ = part_info.find_elements(
            By.XPATH, ".//td")

        search_results.append({
            "vendor": "globalaviation",
            "part number": part_number.text,
            "description": description.text,
            "price": price.text,
            "QTY": qty.text,
            "condition": condition.text,
            "lead time": lead_time.text
        })

        return self.status

    def change_delay(self, new_delay):
        self.delay = new_delay
