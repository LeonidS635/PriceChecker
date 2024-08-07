from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserSelenium
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from subprocess import CREATE_NO_WINDOW


class Aircraftspruce(ParserSelenium):
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.page_load_strategy = "eager"

        chrome_service = webdriver.ChromeService()
        chrome_service.creation_flags = CREATE_NO_WINDOW

        super().__init__(options=options, service=chrome_service)

    def login_function(self, login: str, password: str) -> Status:
        if not self.request_wrapper(url="https://www.aircraftspruce.com/search/search.php"):
            return self.status

        self.logged_in = True
        self.status = Status.OK
        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        search_input = self.driver.find_element(By.CSS_SELECTOR, "input[id=search_text]")
        search_input.clear()
        search_input.send_keys(number)
        search_input.send_keys(Keys.RETURN)

        if self.driver.current_url == "https://www.aircraftspruce.com/search/search.php":
            try:
                ref = self.driver.find_element(By.CSS_SELECTOR, "div[class='prTitle'] > a")
                ref.click()
            except NoSuchElementException:
                return self.status

        try:
            WebDriverWait(self.driver, self.delay).until(
                ec.visibility_of_element_located((By.CSS_SELECTOR, "div[class='prModel']")))
        except TimeoutException:
            self.status = Status.Time_error
            return self.status

        part_number_div = self.driver.find_element(By.CSS_SELECTOR, "div[class='prModel']")
        if part_number_div is None:
            return self.status

        part_number = part_number_div.text.split('\n')[1].strip().split()[-1]
        if part_number.lower() != number.lower():
            return self.status

        self.product_info["part number"] = part_number
        self.product_info["description"] = self.driver.find_element(
            By.CSS_SELECTOR, "div[class='prDetailRight'] > h2").text
        self.product_info["price"] = self.driver.find_element(
            By.CSS_SELECTOR, "div[class='prPrice'] div[id='np']").text.split('/')[0]
        self.product_info["lead time"] = self.driver.find_element(By.CSS_SELECTOR, "div[class='prStockStatus']").text
        search_results.append(deepcopy(self.product_info))

        return self.status
