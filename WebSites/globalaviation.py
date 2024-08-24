from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserSelenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException
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
        try:
            self.request_wrapper(self.driver.delete_all_cookies)
            self.request_wrapper(self.driver.get, url="https://globalaviation.aero/gappcom-2/")

            input_user_name: WebElement = self.request_wrapper(self.driver.find_element, by=By.XPATH,
                                                               value="//input[@name='login:username']")
            input_password: WebElement = self.request_wrapper(self.driver.find_element, by=By.XPATH,
                                                              value="//input[@name='login:password']")
            login_button: WebElement = self.request_wrapper(self.driver.find_element, by=By.XPATH,
                                                            value="//input[@name='login:login']")

            self.request_wrapper(input_user_name.send_keys, login)
            self.request_wrapper(input_password.send_keys, password)
            self.request_wrapper(login_button.click)

            login_error_message: WebElement | None = self.request_wrapper(self.driver.find_element,
                                                                          exceptions_to_ignore=(
                                                                              NoSuchElementException,),
                                                                          by=By.XPATH,
                                                                          value="//span[@class='rf-msgs-sum']")
            if login_error_message is not None:
                self.status = Status.Login_error
                self.logged_in = False
            else:
                self.status = Status.OK
                self.logged_in = True
        finally:
            return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.logged_in:
            self.status = Status.Login_error
            return self.status

        self.status = Status.OK
        try:
            search_section_button: WebElement = self.request_wrapper(self.driver.find_element, by=By.XPATH,
                                                                     value="//td[@id='form1:StockGA:header']")
            self.request_wrapper(search_section_button.click)
            self.request_wrapper(WebDriverWait(self.driver, self.delay).until,
                                 method=ec.invisibility_of_element_located((By.XPATH, "//div[@id='loading_content']")))

            part_number_input: WebElement = self.request_wrapper(self.driver.find_element, by=By.XPATH,
                                                                 value="//textarea[@name='gaform:s10area']")
            self.request_wrapper(part_number_input.clear)
            self.request_wrapper(part_number_input.send_keys, number)

            search_button: WebElement = self.request_wrapper(self.driver.find_element, by=By.XPATH,
                                                             value="//input[@name='gaform:j_idt99']")
            self.request_wrapper(search_button.click)
            self.request_wrapper(WebDriverWait(self.driver, self.delay).until,
                                 method=ec.invisibility_of_element_located((By.XPATH, "//div[@id='loading_content']")))

            part_info: WebElement | None = self.request_wrapper(self.driver.find_element,
                                                                exceptions_to_ignore=(NoSuchElementException,),
                                                                by=By.XPATH,
                                                                value="//tr[@id='gaform:rstable:0:subrstable:0']")
            if part_info is not None:
                part_info_cols: list[WebElement] = self.request_wrapper(part_info.find_elements, by=By.XPATH,
                                                                        value=".//td")
                (_, _, self.product_info["part number"], self.product_info["description"], self.product_info["QTY"], _,
                 self.product_info["condition"], _, _, self.product_info["price"], _,
                 self.product_info["lead time"], _, _) = [elem.text for elem in part_info_cols]
                search_results.append(deepcopy(self.product_info))
        finally:
            return self.status
