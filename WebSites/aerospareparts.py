from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from subprocess import CREATE_NO_WINDOW


class Aerospareparts:
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
            self.driver.get("https://aerospareparts.com/Utilisateur/Login")
        except TimeoutException:
            self.status = "Time error"
            return self.status
        except WebDriverException:
            self.status = "Connection error"
            return self.status

        try:
            input_user_name = self.driver.find_element(By.XPATH, "//input[@name='UserName']")
            input_password = self.driver.find_element(By.XPATH, "//input[@name='Password']")
            login_button = self.driver.find_element(By.XPATH, "//div[@class='form-horizontal']/input")
        except NoSuchElementException:
            self.status = "Login error"
        else:
            input_user_name.send_keys(login)
            input_password.send_keys(password)

            login_button.click()
            self.logged_in = True
            self.status = "OK"

            try:
                self.driver.find_element(By.XPATH,
                                         "//li[text()='The user name, the email or the password is incorrect.']")
                self.status = "Login error"
                self.logged_in = False
            except NoSuchElementException:
                pass
        finally:
            return self.status

    def search_part(self, number, search_results):
        if not self.logged_in:
            self.status = "Login error"
            return self.status

        self.status = "OK"

        try:
            self.driver.get("https://aerospareparts.com/PartNumber/" + number)
        except WebDriverException:
            self.status = "Connection error"
            return self.status

        titles = [title.text.replace(number, '').replace(':', '').strip() for title in
                  self.driver.find_elements(By.XPATH, "//h4[@class='Mine']")]
        tables = self.driver.find_elements(By.XPATH, "//table[@class='Grid']")

        quote_request_refs = {}

        try:
            part_id = self.driver.find_element(By.XPATH,
                                               "//span[contains(text(), 'Part Number')]/following::span").text
            description = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Description')]"
                                                             "/following::span").text.lower()
        except NoSuchElementException:
            part_id = number
            description = ''

        for i in range(len(tables)):
            title = titles[i]
            try:
                quote_request_refs[title] = tables[i].find_element(
                    By.XPATH, ".//a[@class='AutoquoteActionLink']").get_attribute("href")
            except NoSuchElementException:
                if title == "on request":
                    headers = [header.text for header in tables[i].find_elements(By.TAG_NAME, "th")]
                    rows = tables[i].find_elements(By.XPATH, ".//tbody/tr")
                    for row in rows:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        search_results.append({
                            "vendor": "aerospareparts.com" + " (" + title + ')',
                            "part number": part_id,
                            "description": description,
                            "condition": cols[headers.index("CD")].text,
                            "lead time": cols[headers.index("Std Leadtime")].text,
                            "warehouse": cols[headers.index("Incoterms")].text
                        })

        for title, ref in quote_request_refs.items():
            try:
                self.driver.get(ref)

                WebDriverWait(self.driver, self.delay).until(ec.element_to_be_clickable(
                    (By.XPATH, "//input[@value='Quote now']")))
            except TimeoutException:
                self.status = "Time error"
                return self.status

            self.driver.find_element(By.XPATH, "//input[@value='Quote now']").click()

            try:
                condition = self.driver.find_element(By.XPATH, "//label[contains(text(), 'Condition')]"
                                                               "/following::span[1]").text
            except NoSuchElementException:
                condition = ''

            try:
                qty = self.driver.find_element(By.XPATH, "//label[contains(text(), 'Stock available')]"
                                                         "/following::span[1]").text
            except NoSuchElementException:
                qty = ''

            try:
                table = self.driver.find_element(By.XPATH, "//table[@class='Grid']")
                names_cols = [el.text.strip() for el in table.find_elements(By.TAG_NAME, "th")]
                for row in table.find_elements(By.XPATH, ".//tbody/tr"):
                    cols = [el.text.strip() for el in row.find_elements(By.TAG_NAME, "td")]

                    location = cols[names_cols.index("Incoterms")]
                    lead_time = cols[names_cols.index("LT")]
                    price = cols[names_cols.index("Unit price")]

                    search_results.append({
                        "vendor": f"aerospareparts ({title})",
                        "part number": part_id,
                        "description": description,
                        "QTY": qty,
                        "price": price,
                        "condition": condition,
                        "lead time": lead_time,
                        "warehouse": location
                    })
            except NoSuchElementException:
                if title == "on request":
                    self.driver.get("https://aerospareparts.com/PartNumber/" + number)

                    table = self.driver.find_elements(By.XPATH, "//table[@class='Grid']")[titles.index(title)]

                    headers = [header.text for header in table.find_elements(By.TAG_NAME, "th")]
                    rows = table.find_elements(By.XPATH, ".//tbody/tr")
                    for row in rows:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        search_results.append({
                            "vendor": f"aerospareparts ({title})",
                            "part number": part_id,
                            "description": description,
                            "condition": cols[headers.index("CD")].text,
                            "lead time": cols[headers.index("Std Leadtime")].text,
                            "warehouse": cols[headers.index("Incoterms")].text
                        })

        return self.status

    def change_delay(self, new_delay):
        self.delay = new_delay
