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


class Wencor(ParserSelenium):
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})

        chrome_service = webdriver.ChromeService()
        chrome_service.creation_flags = CREATE_NO_WINDOW

        super().__init__(options=options, service=chrome_service)

    def login_function(self, login: str, password: str) -> Status:
        try:
            self.request_wrapper(self.driver.delete_all_cookies)
            self.request_wrapper(self.driver.get, url="https://fly.wencor.com/log-in")

            input_user_name: WebElement = self.request_wrapper(self.driver.find_element,
                                                               by=By.XPATH,
                                                               value="//input[@id='_rhythmloginmultiinstancesportlet"
                                                                     "_WAR_rhythmloginmultiinstancesportlet_INSTANCE"
                                                                     "_Al8rQt3TrPh8_username']")
            input_password: WebElement = self.request_wrapper(self.driver.find_element,
                                                              by=By.XPATH,
                                                              value="//input[@id='_rhythmloginmultiinstancesportlet_"
                                                                    "WAR_rhythmloginmultiinstancesportlet_INSTANCE_A"
                                                                    "l8rQt3TrPh8_password']")
            login_button: WebElement = self.request_wrapper(self.driver.find_elements,
                                                            by=By.XPATH,
                                                            value="//button[@class='btn btn-primary login-btn']")[1]

            self.request_wrapper(input_user_name.send_keys, login)
            self.request_wrapper(input_password.send_keys, password)
            self.request_wrapper(login_button.click)

            login_error_message: WebElement | None = self.request_wrapper(self.driver.find_element,
                                                                          exceptions_to_ignore=(
                                                                              NoSuchElementException,),
                                                                          by=By.XPATH,
                                                                          value="//li[@class='error']")
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
        self.reset_product_info()
        try:
            input_field: WebElement = self.request_wrapper(self.driver.find_element,
                                                           by=By.XPATH,
                                                           value="//input[@id='header-search']")
            search_button: WebElement = self.request_wrapper(self.driver.find_element,
                                                             by=By.XPATH,
                                                             value="//a[@class='icon-label btn-icon expanded-btn']")
            self.request_wrapper(input_field.clear)
            self.request_wrapper(input_field.send_keys, number)
            self.request_wrapper(search_button.click)

            self.request_wrapper(WebDriverWait(self.driver, self.delay).until,
                                 method=ec.presence_of_element_located(
                                     (By.XPATH, "//div[@class='capture-search-done']") or
                                     (By.XPATH, "//a[@class='product-name']")))

            part_ref: WebElement | None = self.request_wrapper(self.driver.find_element,
                                                               exceptions_to_ignore=(NoSuchElementException,),
                                                               by=By.XPATH,
                                                               value="//a[@class='product-name']")
            if part_ref is not None:
                self.request_wrapper(part_ref.click)
                self.request_wrapper(WebDriverWait(self.driver, self.delay).until,
                                     method=ec.visibility_of_element_located(
                                         (By.XPATH, "//div[@class='product-title']/h1")))

                part_number = self.request_wrapper(self.driver.find_element,
                                                   by=By.XPATH,
                                                   value="//div[@class='product-title']/h1").get_attribute("innerHTML")
                if part_number == number:
                    self.request_wrapper(WebDriverWait(self.driver, self.delay).until,
                                         method=ec.presence_of_element_located(
                                             (By.XPATH, "//*[@class='attributes-table second-column']")))

                    self.product_info["part number"] = part_number
                    self.product_info["description"] = self.request_wrapper(
                        self.driver.find_element, by=By.XPATH, value="//div[@class='product-description']").text
                    if ((qty := self.request_wrapper(self.driver.find_element,
                                                     exceptions_to_ignore=(NoSuchElementException,),
                                                     by=By.XPATH, value="//div[@class='stock-quantity']"))) is not None:
                        self.product_info["QTY"] = qty.get_attribute("innerHTML").split()[2]
                    self.product_info["price"] = self.request_wrapper(
                        self.driver.find_element, by=By.XPATH,
                        value="//h2[@class='price new price-large']").get_attribute("innerHTML")
                    self.product_info["lead time"] = self.request_wrapper(
                        self.driver.find_element, by=By.XPATH, value="//*[text()='Standard Lead Time']"
                                                                     "/following::td").text
                    if ((interchanges := self.request_wrapper(self.driver.find_element,
                                                              exceptions_to_ignore=(NoSuchElementException,),
                                                              by=By.XPATH,
                                                              value="//*[text()='Interchanges']/following::td")) is
                            not None):
                        self.product_info["other information"] = f"interchanges: {interchanges.text}"
                    else:
                        self.product_info["other information"] = ""

                    search_results.append(deepcopy(self.product_info))
        finally:
            return self.status
