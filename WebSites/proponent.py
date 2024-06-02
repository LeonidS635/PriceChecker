from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, \
    WebDriverException
from subprocess import CREATE_NO_WINDOW


class Proponent:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.page_load_strategy = "eager"

        chrome_service = webdriver.ChromeService()
        chrome_service.creation_flags = CREATE_NO_WINDOW

        self.driver = webdriver.Chrome(options=options, service=chrome_service)

        self.delay = 20

        self.logged_in = False
        self.status = "OK"

    def __del__(self):
        self.driver.quit()

    def login_function(self, login, password):
        try:
            self.driver.delete_all_cookies()
            self.driver.set_page_load_timeout(self.delay)

            try:
                self.driver.get("https://procart.proponent.com/")
            except TimeoutException:
                self.status = "Time error"
                return self.status
            except WebDriverException:
                self.status = "Connection error"
                return self.status

            input_user_name = self.driver.find_element(By.XPATH, "//input[@name='ctl00$MainContent$txtUserName']")
            input_password = self.driver.find_element(By.XPATH, "//input[@name='ctl00$MainContent$txtPassword']")
            login_button = self.driver.find_element(By.XPATH, "//input[@name='ctl00$MainContent$btnLogin']")

            input_user_name.send_keys(login)
            input_password.send_keys(password)

            try:
                login_button.click()
            except ElementClickInterceptedException:
                try:
                    close_button = self.driver.find_element(By.XPATH, "//div[@class='fancybox-item fancybox-close']")
                    close_button.click()
                except NoSuchElementException:
                    pass

                login_button.click()

            self.logged_in = True
            self.status = "OK"

            WebDriverWait(self.driver, self.delay).until(ec.staleness_of(login_button))
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

        try:
            WebDriverWait(self.driver, self.delay).until(
                ec.presence_of_element_located((By.XPATH,
                                                "//input[@name='ctl00$MainContent$rptControls$ctl00$txtPart']")))

            input_field = self.driver.find_element(By.XPATH,
                                                   "//input[@name='ctl00$MainContent$rptControls$ctl00$txtPart']")
            search_button = self.driver.find_element(By.XPATH, "//input[@name='ctl00$MainContent$btnSearch']")

            input_field.clear()
            input_field.send_keys(number)

            try:
                search_button.click()
            except ElementClickInterceptedException:
                try:
                    cookie_button = self.driver.find_element(By.XPATH, "//button[@id='catapultCookie']")
                    cookie_button.click()
                except NoSuchElementException:
                    pass

                try:
                    close_button = self.driver.find_element(By.XPATH, "//div[@class='fancybox-item fancybox-close']")
                    close_button.click()
                except NoSuchElementException:
                    pass

                search_button.click()

            WebDriverWait(self.driver, self.delay).until(
                ec.presence_of_element_located((By.XPATH, "//td[@aria-describedby='jQGridDemo_Item_description1']")))

            WebDriverWait(self.driver, self.delay).until(
                ec.element_to_be_clickable((By.XPATH, "//a[@class='expandAll button white iconButton']")))
            self.driver.find_element(By.XPATH, "//a[@class='expandAll button white iconButton']").click()

            WebDriverWait(self.driver, self.delay).until(
                ec.invisibility_of_element_located((By.XPATH, "//div[@class='loading-div']")))

            if (self.driver.find_element(
                    By.XPATH, "//td[@aria-describedby='jQGridDemo_Item_description1']").text.find("Proponent") == -1):
                part_id = self.driver.find_element(By.XPATH, "//td[@aria-describedby='jQGridDemo_Cust_part']").text
                description = self.driver.find_element(By.XPATH,
                                                       "//td[@aria-describedby='jQGridDemo_Item_description1']"
                                                       ).text.lower()
                price = self.driver.find_element(By.XPATH, "//td[@aria-describedby='jQGridDemo_Price']").text
                total_qty = self.driver.find_element(By.XPATH, "//td[@aria-describedby='jQGridDemo_QtyAvailable']").text
                try:
                    lead_time = self.driver.find_element(By.XPATH,
                                                         "//ul[@class='gridnotes']/li[contains(text(), 'Lead time')]"). \
                        text.split("Lead time is")[1].strip()
                except NoSuchElementException:
                    lead_time = ''

                WebDriverWait(self.driver, self.delay).until(
                    ec.presence_of_element_located((By.XPATH, "//select[@id='ddlWarehouse_jQGridDemo_1_t']")))
                warehouse_options = self.driver.find_element(By.XPATH, "//select[@id='ddlWarehouse_jQGridDemo_1_t']"). \
                    find_elements(By.TAG_NAME, "option")

                if not warehouse_options:
                    try:
                        warehouse = self.driver.find_element(By.XPATH, "//span[@id='lblWarehouseName_jQGridDemo_1_t']")
                        if warehouse.text:
                            warehouse_options.append(warehouse)
                    except NoSuchElementException:
                        pass

                if warehouse_options:
                    for option in warehouse_options:
                        try:
                            option.click()
                        except WebDriverException:
                            pass

                        warehouse = option.text.split(": ")[1]
                        date_next_in = self.driver.find_element(By.XPATH,
                                                                "//td[@aria-describedby='jQGridDemo_1_t_Due_date']"
                                                                ).text
                        qty_due_in = self.driver.find_element(By.XPATH,
                                                              "//td[@aria-describedby='jQGridDemo_1_t_TotQty']").text
                        qty_available = self.driver.find_element(By.XPATH,
                                                                 "//td[@aria-describedby='jQGridDemo_1_t_WhsQty']"
                                                                 "/span").text
                        try:
                            part_condition = self.driver.find_element(By.XPATH, "//div[@class='column medium-4'][2]"
                                                                      ).text.replace("Part Condition", '').strip()
                        except NoSuchElementException:
                            part_condition = "New"

                        if date_next_in and qty_due_in and date_next_in != ' ' and qty_due_in != ' ':
                            other_information = f"date next in: {date_next_in}\nQTY due in: {qty_due_in}"
                        elif date_next_in and date_next_in != ' ':
                            other_information = f"date next in: {date_next_in}"
                        elif qty_due_in and qty_due_in != ' ':
                            other_information = f"QTY due in: {qty_due_in}"
                        else:
                            other_information = ''

                        search_results.append({
                            "vendor": "proponent.com",
                            "part number": part_id,
                            "description": description,
                            "QTY": qty_available,
                            "price": price,
                            "condition": part_condition,
                            "lead time": lead_time,
                            "warehouse": warehouse,
                            "other information": other_information
                        })
                else:
                    search_results.append({
                        "vendor": "proponent",
                        "part number": part_id,
                        "description": description,
                        "QTY": total_qty,
                        "price": price,
                        "lead time": lead_time,
                    })
        except TimeoutException:
            self.status = "Time error"
        finally:
            self.driver.back()

            return self.status

    def change_delay(self, new_delay):
        self.delay = new_delay
