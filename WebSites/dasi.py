from bs4 import BeautifulSoup
from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests
from PIL import Image


class Dasi(ParserRequests):
    def __init__(self):
        super().__init__()

        self.login_data = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": "",
            "__VIEWSTATEGENERATOR": "",
            "__EVENTVALIDATION": "",
            "ctl00$ctl00$cph1$cph1$ctrlCustomerLogin$LoginForm$UserName": "",
            "ctl00$ctl00$cph1$cph1$ctrlCustomerLogin$LoginForm$Password": "",
            "ctl00$ctl00$cph1$cph1$ctrlCustomerLogin$LoginForm$CaptchaCtrl$txtCode": "",
            "ctl00$ctl00$cph1$cph1$ctrlCustomerLogin$LoginForm$LoginButton": "Log in"
        }

    def download_captcha(self):
        if not self.request_wrapper(self.session.get, url="https://store.dasi.com/login.aspx"):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        self.login_data["__VIEWSTATE"] = page.select_one("input[name='__VIEWSTATE']")["value"]
        self.login_data["__VIEWSTATEGENERATOR"] = page.select_one("input[name='__VIEWSTATEGENERATOR']")["value"]
        self.login_data["__EVENTVALIDATION"] = page.select_one("input[name='__EVENTVALIDATION']")["value"]

        captcha_url = page.select_one("img[alt='captcha']")["src"]
        if not self.request_wrapper(self.session.get, url=("https://store.dasi.com" + captcha_url)):
            return None

        img_bytes = self.response.content
        file = "../captcha.png"
        with open(file, "wb") as f:
            f.write(img_bytes)

        img = Image.open(file)
        return img

    def login_function(self, login: str, password: str, captcha_code: str) -> Status:
        login_url = "https://store.dasi.com/login.aspx"
        self.login_data["ctl00$ctl00$cph1$cph1$ctrlCustomerLogin$LoginForm$UserName"] = login
        self.login_data["ctl00$ctl00$cph1$cph1$ctrlCustomerLogin$LoginForm$Password"] = password
        self.login_data["ctl00$ctl00$cph1$cph1$ctrlCustomerLogin$LoginForm$CaptchaCtrl$txtCode"] = captcha_code

        if not self.request_wrapper(self.session.post, url=login_url, data=self.login_data):
            return self.status

        if self.response.url == login_url:
            self.logged_in = False
            self.status = Status.Login_error
        else:
            self.logged_in = True
            self.status = Status.OK

        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.logged_in:
            self.status = Status.Login_error
            return self.status

        if not self.request_wrapper(self.session.get, url="https://store.dasi.com/search.aspx",
                                    params={"searchterms": number}):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        tables = page.select("table[class='prodlist']")
        part_nums = [part_num.text.split()[0].strip() for part_num in page.select("div[class='product_list_title']")]

        for i in range(len(part_nums)):
            if part_nums[i] != number:
                break

            for tr in tables[i].select("tr"):
                td = tr.select("td")
                if not td:
                    continue

                condition, description, warehouse, lead_time, trace_to_org, _, _, avail, price, _, _, _, _, _ = td
                self.product_info["part number"] = part_nums[i]
                self.product_info["description"] = description.text
                self.product_info["QTY"] = avail.find("span").text
                self.product_info["price"] = price.find("span").text
                self.product_info["condition"] = condition.text
                self.product_info["lead time"] = lead_time.text
                self.product_info["warehouse"] = warehouse.find("span").text
                self.product_info["other information"] = f"trace to org: {" ".join([
                    word.strip() for word in trace_to_org.text.split()])}" if trace_to_org and trace_to_org.text else ""

                search_results.append(deepcopy(self.product_info))

        return self.status
