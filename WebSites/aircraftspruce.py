from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserSelenium
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException
from subprocess import CREATE_NO_WINDOW


class Aircraftspruce(ParserSelenium):
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.page_load_strategy = "eager"
        options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})

        chrome_service = webdriver.ChromeService()
        chrome_service.creation_flags = CREATE_NO_WINDOW

        super().__init__(options=options, service=chrome_service)

    def login_function(self, login: str, password: str) -> Status:
        self.request_wrapper(self.driver.get, url="https://www.aircraftspruce.com/search/search.php")

        self.logged_in = True
        self.status = Status.OK
        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        try:
            search_input: WebElement = self.request_wrapper(self.driver.find_element, by=By.CSS_SELECTOR,
                                                            value="input[id=search_text]")
            self.request_wrapper(search_input.clear)
            self.request_wrapper(search_input.send_keys, number)
            ActionChains(self.driver).move_to_element(search_input).click(search_input).perform()
            self.request_wrapper(WebDriverWait(self.driver, self.delay).until,
                                 method=ec.visibility_of_element_located(
                                     (By.CSS_SELECTOR, "div[class='rfk_results']")))
            ref: WebElement | None = self.request_wrapper(self.driver.find_element,
                                                          exceptions_to_ignore=(NoSuchElementException,),
                                                          by=By.CSS_SELECTOR,
                                                          value="div[class='rfk_results'] div[class='rfk_product'] > a")
            if ref is None:
                self.request_wrapper(search_input.send_keys, Keys.ESCAPE)
                self.request_wrapper(WebDriverWait(self.driver, self.delay).until,
                                     method=ec.invisibility_of_element_located(
                                         (By.CSS_SELECTOR, "div[class='rfk_results']")))
                return self.status

            self.request_wrapper(self.driver.get, url=ref.get_attribute("href"))

            part_number_div: WebElement | None = self.request_wrapper(self.driver.find_element,
                                                                      exceptions_to_ignore=(NoSuchElementException,),
                                                                      by=By.CSS_SELECTOR, value="div[class='prModel']")
            if part_number_div is not None:
                part_number = part_number_div.text.split('\n')[1].strip().split()[-1]
                if part_number.lower() == number.lower():
                    self.product_info["part number"] = part_number
                    self.product_info["description"] = self.request_wrapper(
                        self.driver.find_element, by=By.CSS_SELECTOR, value="div[class='prDetailRight'] > h2").text
                    self.product_info["price"] = self.request_wrapper(
                        self.driver.find_element, by=By.CSS_SELECTOR,
                        value="div[class='prPrice'] div[id='np']").text.split('/')[0]
                    self.product_info["lead time"] = self.request_wrapper(
                        self.driver.find_element, by=By.CSS_SELECTOR, value="div[class='prStockStatus']").text
                    search_results.append(deepcopy(self.product_info))
        finally:
            return self.status
