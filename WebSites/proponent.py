from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserSelenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from subprocess import CREATE_NO_WINDOW


class Proponent(ParserSelenium):
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
        options.page_load_strategy = "eager"

        chrome_service = webdriver.ChromeService()
        chrome_service.creation_flags = CREATE_NO_WINDOW

        super().__init__(options=options, service=chrome_service)

    def click_on_banners(self):
        try:
            cookie_button = self.driver.find_element(By.XPATH, "//button[@data-tid='banner-decline']")
            cookie_button.click()
        except NoSuchElementException:
            pass

        try:
            close_button = self.driver.find_element(By.XPATH, "//div[@class='fancybox-item fancybox-close']")
            close_button.click()
        except NoSuchElementException:
            pass

    def login_function(self, login: str, password: str) -> Status:
        try:
            self.driver.delete_all_cookies()

            if self.request_wrapper(url="https://procart.proponent.com/"):
                input_user_name = self.driver.find_element(By.XPATH, "//input[@name='ctl00$MainContent$txtUserName']")
                input_password = self.driver.find_element(By.XPATH, "//input[@name='ctl00$MainContent$txtPassword']")
                login_button = self.driver.find_element(By.XPATH, "//input[@name='ctl00$MainContent$btnLogin']")

                input_user_name.send_keys(login)
                input_password.send_keys(password)
                self.click_on_banners()
                login_button.click()

                self.logged_in = True
                self.status = Status.OK

                WebDriverWait(self.driver, self.delay).until(ec.staleness_of(login_button))
        except TimeoutException:
            self.status = Status.Time_error
            self.logged_in = False
        except WebDriverException:
            self.status = Status.Other
            self.logged_in = False
        finally:
            return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.logged_in:
            self.status = Status.Login_error
            return self.status

        self.status = Status.OK
        self.reset_product_info()

        try:
            WebDriverWait(self.driver, self.delay).until(
                ec.presence_of_element_located((By.XPATH,
                                                "//input[@name='ctl00$MainContent$rptControls$ctl00$txtPart']")))

            input_field = self.driver.find_element(By.XPATH,
                                                   "//input[@name='ctl00$MainContent$rptControls$ctl00$txtPart']")
            search_button = self.driver.find_element(By.XPATH, "//input[@name='ctl00$MainContent$btnSearch']")

            input_field.clear()
            input_field.send_keys(number)
            self.click_on_banners()
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
                self.product_info["part number"] = self.driver.find_element(
                    By.XPATH, "//td[@aria-describedby='jQGridDemo_Cust_part']").text
                self.product_info["description"] = self.driver.find_element(
                    By.XPATH, "//td[@aria-describedby='jQGridDemo_Item_description1']").text
                self.product_info["price"] = price if (price := self.driver.find_element(
                    By.XPATH, "//td[@aria-describedby='jQGridDemo_Price']").text) else ""
                self.product_info["QTY"] = self.driver.find_element(
                    By.XPATH, "//td[@aria-describedby='jQGridDemo_QtyAvailable']").text
                self.product_info["condition"] = "New"
                try:
                    self.product_info["lead time"] = self.driver.find_element(
                        By.XPATH, "//ul[@class='gridnotes']/li[contains(text(), 'Lead time')]"
                    ).text.split("Lead time is")[1]
                except NoSuchElementException:
                    pass

                WebDriverWait(self.driver, self.delay).until(
                    ec.presence_of_element_located((By.XPATH, "//select[@id='ddlWarehouse_jQGridDemo_1_t']")))
                warehouse_options = self.driver.find_element(
                    By.XPATH, "//select[@id='ddlWarehouse_jQGridDemo_1_t']").find_elements(By.TAG_NAME, "option")

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

                        self.product_info["warehouse"] = option.text.split(": ")[1]
                        self.product_info["QTY"] = self.driver.find_element(
                            By.XPATH, "//td[@aria-describedby='jQGridDemo_1_t_WhsQty']/span").text
                        try:
                            self.product_info["condition"] = self.driver.find_element(
                                By.XPATH, "//div[@class='column medium-4'][2]").text.replace("Part Condition", "")
                        except NoSuchElementException:
                            self.product_info["condition"] = "New"

                        date_next_in = self.driver.find_element(
                            By.XPATH, "//td[@aria-describedby='jQGridDemo_1_t_Due_date']").text
                        qty_due_in = self.driver.find_element(
                            By.XPATH, "//td[@aria-describedby='jQGridDemo_1_t_TotQty']").text

                        if date_next_in and qty_due_in and date_next_in != ' ' and qty_due_in != ' ':
                            self.product_info["other information"] = (f"date next in: {date_next_in}\n"
                                                                      f"QTY due in: {qty_due_in}")
                        elif date_next_in and date_next_in != ' ':
                            self.product_info["other information"] = f"date next in: {date_next_in}"
                        elif qty_due_in and qty_due_in != ' ':
                            self.product_info["other information"] = f"QTY due in: {qty_due_in}"
                        else:
                            self.product_info["other information"] = ""

                        search_results.append(deepcopy(self.product_info))
                else:
                    search_results.append(deepcopy(self.product_info))
        except TimeoutException:
            self.status = Status.Time_error
        except WebDriverException:
            self.status = Status.Other
        finally:
            self.driver.back()
            return self.status
