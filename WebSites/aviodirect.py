from bs4 import BeautifulSoup
from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests


class Aviodirect(ParserRequests):
    def __init__(self):
        super().__init__()

    def login_function(self, login: str, password: str) -> Status:
        self.logged_in = True
        self.status = Status.OK
        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        params = {"post_type": "product", "product_cat": 0, "s": number}
        headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                                 "Chrome/127.0.0.0 Safari/537.36"}
        if not self.request_wrapper(self.session.get, url="https://aviodirect.com/", params=params, headers=headers):
            if self.response.status_code == 409:
                self.status = Status.OK
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")

        part_title = page.select_one("h1[class='product_title entry-title']")
        if part_title is None:
            return self.status

        self.product_info["part number"], self.product_info["description"] = part_title.text.split(
            " | ") if '|' in part_title.text else part_title.text.split(" – ")
        self.product_info["price"] = page.select_one("p[class='price']").text
        self.product_info["condition"] = page.select_one(
            "div[class='woocommerce-product-details__short-description']").text

        search_results.append(deepcopy(self.product_info))

        return self.status
