from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserSelenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from subprocess import CREATE_NO_WINDOW


class Globalaviation(ParserSelenium):
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})

        chrome_service = webdriver.ChromeService()
        chrome_service.creation_flags = CREATE_NO_WINDOW

        super().__init__(options=options, service=chrome_service)

    def login_function(self, login: str, password: str) -> Status:
        self.driver.delete_all_cookies()
        if not self.request_wrapper(url="https://globalaviation.aero/gappcom-2/"):
            return self.status

        input_user_name = self.driver.find_element(By.XPATH, "//input[@name='login:username']")
        input_password = self.driver.find_element(By.XPATH, "//input[@name='login:password']")
        login_button = self.driver.find_element(By.XPATH, "//input[@name='login:login']")

        input_user_name.send_keys(login)
        input_password.send_keys(password)

        login_button.click()
        self.logged_in = True
        self.status = Status.OK

        try:
            self.driver.find_element(By.XPATH, "//span[@class='rf-msgs-sum']")
            self.status = Status.Login_error
            self.logged_in = False
        except NoSuchElementException:
            pass

        self.driver.find_element(By.XPATH, "//td[@id='form1:StockGA:header']").click()

        try:
            WebDriverWait(self.driver, self.delay).until(
                ec.invisibility_of_element_located((By.XPATH, "//div[@id='loading_content']")))
        except TimeoutException:
            self.status = Status.Time_error

        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.logged_in:
            self.status = Status.Login_error
            return self.status

        self.status = Status.OK

        search_section_button = self.driver.find_element(By.XPATH, "//td[@id='form1:StockGA:header']")
        search_section_button.click()

        try:
            WebDriverWait(self.driver, self.delay).until(
                ec.invisibility_of_element_located((By.XPATH, "//div[@id='loading_content']")))
        except TimeoutException:
            self.status = Status.Time_error
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
            self.status = Status.Time_error
            return self.status

        try:
            part_info = self.driver.find_element(By.XPATH, "//tr[@id='gaform:rstable:0:subrstable:0']")
        except NoSuchElementException:
            return self.status

        _, _, self.product_info["part number"], self.product_info["description"], self.product_info["QTY"], _, \
            self.product_info["condition"], _, _, self.product_info["price"], _, self.product_info[
            "lead time"], _, _ = [elem.text for elem in part_info.find_elements(By.XPATH, ".//td")]

        search_results.append(deepcopy(self.product_info))

        return self.status
