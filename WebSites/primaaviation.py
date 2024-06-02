from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from subprocess import CREATE_NO_WINDOW


class Primaaviation:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        chrome_service = webdriver.ChromeService()
        chrome_service.creation_flags = CREATE_NO_WINDOW

        self.driver = webdriver.Chrome(options=options, service=chrome_service)

        self.delay = 20

        self.status = "OK"

    def __del__(self):
        self.driver.quit()

    def login_function(self, login, password):
        try:
            self.driver.get("https://primaaviation.com/inventory")
        except ConnectionError:
            self.status = "Connection error"
            return self.status

        return self.status

    def search_part(self, number, search_results):
        self.status = "OK"

        part_input = self.driver.find_element(By.XPATH, "//input[@id='srch']")
        part_input.clear()
        part_input.send_keys(number)

        try:
            res_table = self.driver.find_element(By.XPATH, "//table[@id='dTable']")
        except NoSuchElementException:
            return self.status

        for part in res_table.find_elements(By.XPATH, ".//tbody/tr"):
            columns = part.find_elements(By.XPATH, ".//td")
            if len(columns) == 1:
                break

            part_id, condition, qty, description, _ = part.find_elements(By.XPATH, ".//td")

            search_results.append({
                "vendor": "primaaviation",
                "part number": part_id.text,
                "description": description.text,
                "QTY": qty.text,
                "condition": condition.text
            })

        return self.status
