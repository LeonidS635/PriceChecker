from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, \
    WebDriverException
from subprocess import CREATE_NO_WINDOW


class Satair:
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
            self.driver.get("https://www.satair.com/market/search")
        except TimeoutException:
            self.status = "Time error"
            return self.status
        except WebDriverException:
            self.status = "Connection error"
            return self.status

        try:
            # WebDriverWait(self.driver, self.delay).until(
            #     ec.presence_of_element_located((By.XPATH, "//button[@class='cky-btn cky-btn-custom-accept']")))
            # self.driver.find_element(By.XPATH, "//button[@class='cky-btn cky-btn-custom-accept']").click()

            WebDriverWait(self.driver, self.delay).until(ec.presence_of_element_located((By.XPATH,
                                                                                         "//input[@name='email']")))

            input_user_name = self.driver.find_element(By.XPATH, "//input[@name='email']")
            input_password = self.driver.find_element(By.XPATH, "//input[@name='password']")
            login_button = self.driver.find_element(By.XPATH, "//button[@class='button medium default market-site']")

            input_user_name.send_keys(login)
            input_password.send_keys(password)

            login_button.send_keys(Keys.RETURN)
            self.logged_in = True
            self.status = "OK"

            try:
                self.driver.find_element(By.XPATH, "//div[@class='notification__copy']")
                self.status = "Login failed!"
                self.logged_in = False
            except NoSuchElementException:
                pass
        except TimeoutException:
            self.status = "Login error"
        finally:
            return self.status


    def search_part(self, number, search_results):
        if not self.logged_in:
            self.status = "Login error"
            return self.status

        self.status = "OK"

        input_field = self.driver.find_element(By.XPATH, "//input[@id='search-products']")
        input_field.send_keys(number)

        try:
            WebDriverWait(self.driver, self.delay).until(
                ec.visibility_of_element_located((By.XPATH, "//div[@class='search-result']")))

            parts = self.driver.find_elements(By.XPATH, "//div[@class='search-item-outer-wrapper']")

            while True:
                try:
                    load_more_button = self.driver.find_element(By.XPATH,
                                                                "//button[@class='button medium default market-site']")
                    load_more_button.click()
                    WebDriverWait(self.driver, self.delay).until(lambda driver:
                                                                 len(driver.find_elements(
                                                                     By.XPATH,
                                                                     "//div[@class='search-item-outer-wrapper']")) !=
                                                                 len(parts))

                    parts = self.driver.find_elements(By.XPATH, "//div[@class='search-item-outer-wrapper']")
                except NoSuchElementException:
                    break
            for part in parts:
                WebDriverWait(part, self.delay).until(
                    ec.visibility_of_element_located((By.XPATH,
                                                      ".//span[@class='search-item-header__title__number']")))
                part_id = part.find_element(By.XPATH, ".//span[@class='search-item-header__title__number']").text
                description = part.find_element(By.XPATH,
                                                ".//span[@class='search-item-header__title__name']").text.lower()

                if part_id.split(':')[0] != number:
                    try:
                        part.find_element(By.XPATH, "//div[@class='partnumber_interchangeable']")
                    except NoSuchElementException:
                        break
                else:
                    part.find_element(By.XPATH, ".//a[@class='search-item-link']").send_keys(Keys.RETURN)

                    WebDriverWait(self.driver, self.delay).until(
                        ec.visibility_of_element_located((By.XPATH,
                                                          "//div[@class='product-details-component-wrapper']")))
                    page = self.driver.find_element(By.XPATH, "//div[@class='product-details-component-wrapper']")

                    WebDriverWait(page, self.delay).until(
                        ec.invisibility_of_element_located((By.XPATH,
                                                            ".//div[@class='product-price-label-loader']")))
                    WebDriverWait(page, self.delay).until(
                        ec.visibility_of_element_located((By.XPATH, ".//span[contains(@class, 'price') or"
                                                                    "@class='product-price--restricted']")))

                    try:
                        price = page.find_element(By.XPATH, ".//span[@class='price']").text.strip().replace(',', '')
                        price = '$' + price[:-2] + '.' + price[-2:]
                    except NoSuchElementException:
                        price = ''

                    qty = ''

                    WebDriverWait(page, self.delay).until(ec.none_of(
                        ec.visibility_of_any_elements_located(
                            (By.XPATH,
                             ".//div[@class='item-availability-wrapper item-availability-wrapper--loading']"))))
                    WebDriverWait(page, self.delay).until(
                        ec.visibility_of_element_located((By.XPATH, ".//span[@class='item-availability-info']")))
                    lead_time = page.find_element(By.XPATH, ".//span[@class='item-availability-info']")
                    try:
                        qty = lead_time.find_element(By.XPATH, ".//span[@class='item-availability-info__quantity']")

                        lead_time = qty.find_element(By.XPATH, "./following::span").text
                        qty = qty.text
                    except NoSuchElementException:
                        lead_time = lead_time.text.lower()
                        if lead_time == "n/a":
                            lead_time = ''

                    WebDriverWait(page, self.delay).until(
                        ec.visibility_of_element_located((By.XPATH,
                                                          ".//span[@class='search-item-specs__value-additional']")))
                    location = page.find_element(By.XPATH,
                                                 ".//span[@class='search-item-specs__value-additional']").text
                    if location == '-':
                        location = ''

                    WebDriverWait(page, self.delay).until(
                        ec.visibility_of_element_located((By.XPATH,
                                                          ".//span[@class='search-item-specs__value-additional']")))
                    part_condition = page.find_element(By.XPATH,
                                                       ".//p[@class="
                                                       "'product-details-list-item-title product-details-title-label' "
                                                       "and contains(text(), 'Condition')]/following::p").text

                    interchanges_list = []
                    try:
                        interchanges = page.find_element(By.XPATH, ".//div[@class='interchangeable-list-items']")
                    except NoSuchElementException:
                        pass
                    else:
                        for item_number in interchanges.find_elements(By.XPATH, ".//span[@class='product__title']"):
                            interchanges_list.append(item_number.find_element(By.CLASS_NAME,
                                                                              "product__title__manufacturer-aid"
                                                                              ).text +
                                                     item_number.find_element(
                                                         By.CLASS_NAME,
                                                         "product__title__manufacturer-code").text.strip())

                    interchanges = " ; ".join(interchanges_list) if interchanges_list else ''
                    if interchanges:
                        other_information = f"interchanges: {interchanges}"
                    else:
                        other_information = ''

                    try:
                        product_details_section = page.find_element(By.XPATH,
                                                                    ".//div[@class='product-details-section']")
                        supplies_table = product_details_section.find_element(By.XPATH,
                                                                              ".//div[@class='simple-table "
                                                                              "product-details-table']")
                    except NoSuchElementException:
                        if lead_time.find('\n') != -1:
                            qty, availability = lead_time.split('\n')

                        search_results.append({
                            "vendor": "satair",
                            "part number": part_id,
                            "description": description,
                            "QTY": qty,
                            "price": price,
                            "condition": part_condition,
                            "lead time": lead_time,
                            "warehouse": location,
                            "other information": other_information
                        })
                    else:
                        for row in supplies_table.find_elements(By.XPATH, ".//div[@class='table-row']"):
                            cols = row.find_elements(By.CLASS_NAME, "simple-table-item-cell")

                            location = cols[0].text
                            qty = cols[2].text

                            if qty == '-':
                                qty = ''
                            else:
                                qty = qty.replace("EA", '').strip()

                            if location == '-':
                                location = ''

                            search_results.append({
                                "vendor": "satair",
                                "part number": part_id,
                                "description": description,
                                "QTY": qty,
                                "price": price,
                                "condition": part_condition,
                                "lead time": lead_time,
                                "warehouse": location,
                                "other information": other_information
                            })
                    finally:
                        WebDriverWait(self.driver, self.delay).until(
                            ec.element_to_be_clickable((By.XPATH, "//button[@class='close-btn']")))
                        self.driver.find_element(By.XPATH, "//button[@class='close-btn']").send_keys(Keys.RETURN)
        except TimeoutException:
            self.status = "Time error"
        finally:
            try:
                while input_field.get_attribute("value") != '':
                    input_field.send_keys(Keys.BACKSPACE)
            except ElementNotInteractableException:
                WebDriverWait(self.driver, self.delay).until(
                    ec.element_to_be_clickable((By.XPATH, "//button[@class='close-btn']")))
                self.driver.find_element(By.XPATH, "//button[@class='close-btn']").send_keys(Keys.RETURN)

                while input_field.get_attribute("value") != '':
                    input_field.send_keys(Keys.BACKSPACE)
            finally:
                return self.status

    def change_delay(self, new_delay):
        self.delay = new_delay
