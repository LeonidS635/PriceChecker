from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserSelenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from subprocess import CREATE_NO_WINDOW


class Wencor(ParserSelenium):
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        chrome_service = webdriver.ChromeService()
        chrome_service.creation_flags = CREATE_NO_WINDOW

        super().__init__(options=options, service=chrome_service)

    def login_function(self, login: str, password: str) -> Status:
        self.driver.delete_all_cookies()

        if not self.request_wrapper(url="https://fly.wencor.com/log-in"):
            return self.status

        input_user_name = self.driver.find_element(By.XPATH,
                                                   "//input[@id='_rhythmloginmultiinstancesportlet_WAR_rhythmloginm"
                                                   "ultiinstancesportlet_INSTANCE_Al8rQt3TrPh8_username']")
        input_password = self.driver.find_element(By.XPATH,
                                                  "//input[@id='_rhythmloginmultiinstancesportlet_WAR_rhythmloginmu"
                                                  "ltiinstancesportlet_INSTANCE_Al8rQt3TrPh8_password']")
        login_button = self.driver.find_elements(By.XPATH, "//button[@class='btn btn-primary login-btn']")[1]

        input_user_name.send_keys(login)
        input_password.send_keys(password)
        login_button.click()
        self.logged_in = True
        self.status = Status.OK

        try:
            self.driver.find_element(By.XPATH, "//li[@class='error']")
            self.status = Status.Login_error
            self.logged_in = False
        except NoSuchElementException:
            pass

        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.logged_in:
            self.status = Status.Login_error
            return self.status

        self.status = Status.OK
        self.reset_product_info()

        input_field = self.driver.find_element(By.XPATH, "//input[@id='header-search']")
        search_button = self.driver.find_element(By.XPATH, "//a[@class='icon-label btn-icon expanded-btn']")

        input_field.clear()
        input_field.send_keys(number)
        search_button.click()

        try:
            WebDriverWait(self.driver, self.delay).until(
                ec.presence_of_element_located((By.XPATH, "//div[@class='capture-search-done']") or
                                               (By.XPATH, "//a[@class='product-name']")))

            try:
                part_ref = self.driver.find_element(By.XPATH, "//a[@class='product-name']")
            except NoSuchElementException:
                pass
            else:
                part_ref.click()

                WebDriverWait(self.driver, self.delay).until(
                    ec.visibility_of_element_located((By.XPATH, "//div[@class='product-title']/h1")))

                part_number = self.driver.find_element(By.XPATH, "//div[@class='product-title']/h1").get_attribute(
                    "innerHTML")

                if part_number == number:
                    WebDriverWait(self.driver, self.delay).until(
                        ec.presence_of_element_located((By.XPATH, "//*[@class='attributes-table second-column']")))

                    self.product_info["part number"] = part_number
                    self.product_info["description"] = self.driver.find_element(
                        By.XPATH, "//div[@class='product-description']").text
                    try:
                        self.product_info["QTY"] = self.driver.find_element(
                            By.XPATH, "//div[@class='stock-quantity']").get_attribute("innerHTML").split()[2]
                    except NoSuchElementException:
                        self.product_info["QTY"] = ""
                    self.product_info["price"] = self.driver.find_element(
                        By.XPATH, "//h2[@class='price new price-large']").get_attribute("innerHTML")
                    self.product_info["lead time"] = self.driver.find_element(
                        By.XPATH, "//*[text()='Standard Lead Time']/following::td").text
                    try:
                        interchanges = self.driver.find_element(By.XPATH, "//*[text()='Interchanges']/following::td")
                        self.product_info["other information"] = f"interchanges: {interchanges.text}"
                    except NoSuchElementException:
                        self.product_info["other information"] = ""

                    search_results.append(deepcopy(self.product_info))
        except TimeoutException:
            self.status = Status.Time_error
        except WebDriverException:
            self.status = Status.Other
        finally:
            return self.status
