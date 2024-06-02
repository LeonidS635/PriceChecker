from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from subprocess import CREATE_NO_WINDOW


class Turboresources:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        chrome_service = webdriver.ChromeService()
        chrome_service.creation_flags = CREATE_NO_WINDOW

        self.driver = webdriver.Chrome(options=options, service=chrome_service)

        self.delay = 20

        self.logged_in = True
        self.status = "OK"

        self.url = "https://turboresources.com/shop/search/"

    def __del__(self):
        self.driver.quit()

    def login_function(self, *_):
        self.status = "OK"
        return self.status

    def search_part(self, number, search_results):
        self.status = "OK"

        try:
            self.driver.get(self.url + f"?search={number}")
        except TimeoutException:
            self.status = "Time error"
            return self.status
        except WebDriverException:
            self.status = "Connection error"
            return self.status

        try:
            WebDriverWait(self.driver, self.delay).until(
                ec.visibility_of_any_elements_located((By.XPATH,
                                                       "//div[@id='foundPartsContainer'] |"
                                                       "//div[@id='foundOtherPartsContainer'] |"
                                                       "//div[@id='notFoundPartsContainer']")))
        except TimeoutException:
            self.status = "Time error"
            return self.status

        part_grid = self.driver.find_element(By.XPATH, "//div[@id='foundPartsContainer']")
        if part_grid.text != "":
            try:
                part_grid.find_element(By.XPATH, ".//h3[text()='No parts found :(']")
            except NoSuchElementException:
                try:
                    WebDriverWait(part_grid, self.delay).until(
                        ec.presence_of_all_elements_located((By.XPATH, ".//div[@class='part-preview']")))
                except TimeoutException:
                    self.status = "Time error"
                    return self.status

                part_refs = []
                parts = part_grid.find_elements(By.XPATH, "//div[@class='part-preview']")

                for part in parts:
                    part_id, description, condition, qty = [i.text for i in
                                                            part.find_element(By.XPATH, ".//ul[@class='part-heading']").
                                                            find_elements(By.TAG_NAME, "li")]
                    description = description.lower()

                    if part_id == number:
                        part_refs.append(part.find_element(By.XPATH, ".//parent::a").get_attribute("href"))
                        search_results.append({
                            "vendor": "turboresources",
                            "part number": part_id,
                            "description": description,
                            "QTY": qty,
                            "condition": condition,
                        })
            finally:
                return self.status

            # for ref in part_refs:
            #     self.driver.get(ref)
            #
            #     request_button = self.driver.find_element(By.XPATH,
            #                                               "//button[@class='button product-form__input product-form__"
            #                                               "input_button' and contains(text(), 'Request Quote')]")
            #     try:
            #         request_button.click()
            #     except ElementClickInterceptedException:
            #         close_button = self.driver.find_elements(By.XPATH, "//i[@class='fa fa-fw fa-times']")[0]
            #         close_button.click()
            #
            #         request_button.click()
            #
            #     email_field = self.driver.find_elements(By.XPATH, "//input[@id='email_field']")[4]
            #     name_field = self.driver.find_elements(By.XPATH, "//input[@id='name_field']")[1]
            #     company_field = self.driver.find_elements(By.XPATH, "//input[@id='company_field']")[1]
            #     email_field.send_keys("sales@airpartsol.com")
            #     name_field.send_keys("sales@airpartsol.com")
            #     company_field.send_keys("sales@airpartsol.com")
            #
            #     submit_button = self.driver.find_elements(By.XPATH,
            #                                               "//button[@class='button button_centered' and "
            #                                               "contains(text(), 'Submit')]")[3]
            #     try:
            #         submit_button.click()
            #     except ElementClickInterceptedException:
            #         close_button = self.driver.find_elements(By.XPATH, "//i[@class='fa fa-fw fa-times']")[0]
            #         close_button.click()
            #
            #         submit_button.click()

    def change_delay(self, new_delay):
        self.delay = new_delay
