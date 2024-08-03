from bs4 import BeautifulSoup
from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests


class Lasaero(ParserRequests):
    def __init__(self):
        super().__init__()

    def login_function(self, login: str, password: str) -> Status:
        if not self.request_wrapper(self.session.get, url="https://www.lasaero.com/account/"):
            return self.status

        page = BeautifulSoup(self.response.text, 'lxml')
        csrf = page.select_one("input[name='csrfmiddlewaretoken']")["value"]

        login_data = {
            "csrfmiddlewaretoken": csrf,
            "refresh_page": "True",
            "return_path_jx": "/account/",
            "shopper_email": login,
            "shopper_pass": password,
        }
        headers = {
            "Host": "www.lasaero.com",
            "Origin": "https://www.lasaero.com",
            "Refer": "https://www.lasaero.com/account/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/121.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }

        if not self.request_wrapper(self.session.post, url="https://www.lasaero.com/ajax/contact/login/",
                                    data=login_data, headers=headers):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        if page.find(string="We could not log you in. Please try again, or"):
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

        if not self.request_wrapper(self.session.get, url=("https://www.lasaero.com/part/" + number)):
            if self.response.status_code == 404:
                self.status = Status.OK
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        res_table = page.select_one("table[class='table table-bordered table-responsive table-condensed']")

        _, description, _, qty_in_stock, _, qty_on_order, _, price, _, lead_time = res_table.find_all("td")
        self.product_info["part number"] = page.select_one("h1").text
        self.product_info["description"] = description.text
        self.product_info["QTY"] = qty_in_stock.text
        self.product_info["price"] = '$' + price_text if ((
            price_text := price.text[1:].replace("/ Each", "").strip())) != "POA" else ""
        self.product_info["lead time"] = lead_time.text
        self.product_info["other information"] = f"qty on order: {qty_on_order.text}"

        search_results.append(deepcopy(self.product_info))

        return self.status
