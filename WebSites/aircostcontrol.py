from bs4 import BeautifulSoup
from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests


class Aircostcontrol(ParserRequests):
    def __init__(self):
        super().__init__()

    def login_function(self, login: str, password: str) -> Status:
        login_data = {
            "back": "",
            "email": login,
            "password": password,
            "submitLogin": 1
        }

        if not self.request_wrapper(self.session.post, url="https://ecommerce.aircostcontrol.com/login",
                                    data=login_data):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        if page.find(string="Authentication failed."):
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

        params = {
            "controller": "search",
            "orderby": "position",
            "orderway": "desc",
            "submit": "",
            "search_query": number
        }

        if not self.request_wrapper(self.session.get, url="https://ecommerce.aircostcontrol.com/search", params=params):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        ref = page.select_one("a[class='btn btn-primary w-100 mb-2']")

        if ref is None or not self.request_wrapper(self.session.get, url=ref["href"]):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        self.product_info["part number"] = page.find("label", string="PN:").find_next_sibling().text
        self.product_info["description"] = page.find("label", string="Description:").next_sibling.text
        self.product_info["condition"] = page.find("label", string="Condition:").find_next_sibling().text
        self.product_info["QTY"] = qty.text if ((
            qty := page.select_one("span[class='hidden-in-product-pp']"))) is not None else ""
        self.product_info["price"] = price.find_all("td")[1].text if ((
            price := page.select_one("tr[data-discount-type='amount']"))) is not None else ""
        self.product_info["lead time"] = page.find("label", string="Lead-time:").find_next_sibling().text

        search_results.append(deepcopy(self.product_info))

        return self.status
