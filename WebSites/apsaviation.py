from bs4 import BeautifulSoup
from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests


class Apsaviation(ParserRequests):
    def __init__(self):
        super().__init__()

    def login_function(self, login: str, password: str) -> Status:
        self.logged_in = True
        self.status = Status.OK
        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.request_wrapper(self.session.get, url="https://shop.aps-aviation.com/catalogsearch/result/",
                                    params={"q": number}):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        part_number_div = page.select_one("div[class='productSku']")
        if (part_number_div is not None and
                (part_number := part_number_div.get_text(strip=True)).lower() == number.lower()):
            self.product_info["part number"] = part_number
            self.product_info["description"] = page.select_one("strong[class='product name product-item-name']").text
            self.product_info["QTY"] = page.select_one("div[class='stock available']").text
            search_results.append(deepcopy(self.product_info))

        return self.status
