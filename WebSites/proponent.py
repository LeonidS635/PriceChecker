from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserSelenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException
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
        cookie_button: WebElement | None = self.request_wrapper(self.driver.find_element,
                                                                exceptions_to_ignore=(NoSuchElementException,),
                                                                by=By.XPATH,
                                                                value="//button[@data-tid='banner-decline']")
        close_button: WebElement | None = self.request_wrapper(self.driver.find_element,
                                                               exceptions_to_ignore=(NoSuchElementException,),
                                                               by=By.XPATH,
                                                               value="//div[@class='fancybox-item fancybox-close']")
        if cookie_button is not None:
            self.request_wrapper(cookie_button.click)
        if close_button is not None:
            self.request_wrapper(close_button.click)

    def login_function(self, login: str, password: str) -> Status:
        try:
            self.request_wrapper(self.driver.delete_all_cookies)
            self.request_wrapper(self.driver.get, url="https://procart.proponent.com/")

            input_user_name: WebElement = self.request_wrapper(self.driver.find_element, by=By.XPATH,
                                                               value="//input[@name='ctl00$MainContent$txtUserName']")
            input_password: WebElement = self.request_wrapper(self.driver.find_element, by=By.XPATH,
                                                              value="//input[@name='ctl00$MainContent$txtPassword']")
            login_button: WebElement = self.request_wrapper(self.driver.find_element, by=By.XPATH,
                                                            value="//input[@name='ctl00$MainContent$btnLogin']")

            self.request_wrapper(input_user_name.send_keys, login)
            self.request_wrapper(input_password.send_keys, password)
            self.click_on_banners()
            self.request_wrapper(login_button.click)
            self.request_wrapper(WebDriverWait(self.driver, self.delay).until, method=ec.staleness_of(login_button))

            self.logged_in = True
            self.status = Status.OK
        finally:
            return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.logged_in:
            self.status = Status.Login_error
            return self.status

        self.status = Status.OK
        self.reset_product_info()
        try:
            self.request_wrapper(WebDriverWait(self.driver, self.delay).until, method=ec.presence_of_element_located(
                (By.XPATH, "//input[@name='ctl00$MainContent$rptControls$ctl00$txtPart']")))

            input_field: WebElement = self.request_wrapper(self.driver.find_element, by=By.XPATH,
                                                           value="//input[@name='ctl00$MainContent$rptControls$ctl00$"
                                                                 "txtPart']")
            search_button: WebElement = self.request_wrapper(self.driver.find_element, by=By.XPATH,
                                                             value="//input[@name='ctl00$MainContent$btnSearch']")
            self.request_wrapper(input_field.clear)
            self.request_wrapper(input_field.send_keys, number)
            self.click_on_banners()
            self.request_wrapper(search_button.click)
            self.request_wrapper(WebDriverWait(self.driver, self.delay).until, method=ec.presence_of_element_located(
                (By.XPATH, "//td[@aria-describedby='jQGridDemo_Item_description1']")))
            self.request_wrapper(WebDriverWait(self.driver, self.delay).until, method=ec.element_to_be_clickable(
                (By.XPATH, "//a[@class='expandAll button white iconButton']")))

            expand_all_button: WebElement = self.request_wrapper(self.driver.find_element, by=By.XPATH,
                                                                 value="//a[@class='expandAll button white "
                                                                       "iconButton']")
            self.request_wrapper(expand_all_button.click)
            self.request_wrapper(WebDriverWait(self.driver, self.delay).until,
                                 method=ec.invisibility_of_element_located((By.XPATH, "//div[@class='loading-div']")))

            if ((description := self.request_wrapper(self.driver.find_element, by=By.XPATH,
                                                     value="//td[@aria-describedby='jQGridDemo_Item_description1']"
                                                     ).text).find("Proponent") == -1):
                self.product_info["part number"] = self.request_wrapper(
                    self.driver.find_element, by=By.XPATH,
                    value="//td[@aria-describedby='jQGridDemo_Cust_part']").text
                self.product_info["description"] = description
                self.product_info["price"] = self.request_wrapper(
                    self.driver.find_element, by=By.XPATH, value="//td[@aria-describedby='jQGridDemo_Price']").text
                self.product_info["QTY"] = self.request_wrapper(
                    self.driver.find_element, by=By.XPATH,
                    value="//td[@aria-describedby='jQGridDemo_QtyAvailable']").text
                self.product_info["condition"] = "New"
                if (lead_time := self.request_wrapper(
                        self.driver.find_element, exceptions_to_ignore=(NoSuchElementException,), by=By.XPATH,
                        value="//ul[@class='gridnotes']/li[contains(text(), 'Lead time')]")) is not None:
                    self.product_info["lead time"] = lead_time.text.split("Lead time is")[1]

                self.request_wrapper(WebDriverWait(self.driver, self.delay).until,
                                     method=ec.presence_of_element_located(
                                         (By.XPATH, "//select[@id='ddlWarehouse_jQGridDemo_1_t']")))

                warehouse_options: list[WebElement] = self.request_wrapper(
                    self.request_wrapper(self.driver.find_element,
                                         by=By.XPATH,
                                         value="//select[@id='ddlWarehouse_jQGridDemo_1_t']"
                                         ).find_elements,
                    by=By.TAG_NAME, value="option")

                if not warehouse_options:
                    warehouse: WebElement | None = self.request_wrapper(self.driver.find_element,
                                                                        exceptions_to_ignore=(NoSuchElementException,),
                                                                        by=By.XPATH,
                                                                        value="//span[@id='lblWarehouseName_jQ"
                                                                              "GridDemo_1_t']")
                    if warehouse is not None and warehouse.text:
                        warehouse_options.append(warehouse)

                if warehouse_options:
                    for option in warehouse_options:
                        self.request_wrapper(option.click)

                        self.product_info["warehouse"] = option.text.split(": ")[1]
                        self.product_info["QTY"] = self.request_wrapper(self.driver.find_element,
                                                                        by=By.XPATH,
                                                                        value="//td[@aria-describedby='jQ"
                                                                              "GridDemo_1_t_WhsQty']/span").text
                        if (condition := self.request_wrapper(
                                self.driver.find_element, exceptions_to_ignore=(NoSuchElementException,), by=By.XPATH,
                                value="//div[@class='column medium-4'][2]")) is not None:
                            self.product_info["condition"] = condition.text.replace("Part Condition", "")

                        date_next_in = self.request_wrapper(self.driver.find_element,
                                                            by=By.XPATH,
                                                            value="//td[@aria-describedby="
                                                                  "'jQGridDemo_1_t_Due_date']").text
                        qty_due_in = self.request_wrapper(self.driver.find_element,
                                                          by=By.XPATH,
                                                          value="//td[@aria-describedby='jQGridDemo_1_t_TotQty']").text

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
        finally:
            self.driver.back()
            return self.status
