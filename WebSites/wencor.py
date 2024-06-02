from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from subprocess import CREATE_NO_WINDOW


class Wencor:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
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
            self.driver.get("https://fly.wencor.com/log-in")
        except TimeoutException:
            self.status = "Time error"
            return self.status
        except WebDriverException:
            self.status = "Connection error"
            return self.status

        try:
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
            self.status = "OK"

            try:
                self.driver.find_element(By.XPATH, "//li[@class='error']")
                self.status = "Login error"
                self.logged_in = False
            except NoSuchElementException:
                pass
        except TimeoutException:
            self.status = "Login error"
            self.logged_in = False
        finally:
            return self.status

    def search_part(self, number, search_results):
        if not self.logged_in:
            self.status = "Login error"
            return self.status

        self.status = "OK"

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

                part_id = self.driver.find_element(By.XPATH, "//div[@class='product-title']/h1").get_attribute(
                    "innerHTML")
                description = self.driver.find_element(By.XPATH, "//div[@class='product-description']").text.lower()

                WebDriverWait(self.driver, self.delay).until(
                    ec.presence_of_element_located((By.XPATH, "//*[@class='attributes-table second-column']")))

                try:
                    interchanges = self.driver.find_element(By.XPATH, "//*[text()='Interchanges']/following::td").text
                except NoSuchElementException:
                    interchanges = ''

                if part_id == number or part_id in interchanges.split(' ; '):
                    price = self.driver.find_element(By.XPATH,
                                                     "//h2[@class='price new price-large']").get_attribute("innerHTML")
                    if price == "$0.00":
                        price = ''

                    try:
                        qty = self.driver.find_element(By.XPATH, "//div[@class='stock-quantity']").get_attribute(
                            "innerHTML").split()[2]
                    except NoSuchElementException:
                        qty = ''

                    lead_time = self.driver.find_element(By.XPATH,
                                                         "//*[text()='Standard Lead Time']/following::td").text

                    search_results.append({
                        "vendor": "wencor",
                        "part number": part_id,
                        "description": description,
                        "QTY": qty,
                        "price": price,
                        "lead time": lead_time,
                        "other information": f"interchanges: {interchanges}"
                    })
        except TimeoutException:
            self.status = "Time error"
        finally:
            return self.status

    def change_delay(self, new_delay):
        self.delay = new_delay
