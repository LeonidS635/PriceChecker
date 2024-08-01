from bs4 import BeautifulSoup
from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests


class Primaaviation(ParserRequests):
    def __init__(self):
        super().__init__()

    def login_function(self, login: str, password: str) -> Status:
        self.logged_in = True
        self.status = Status.OK
        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.request_wrapper(self.session.get, url="https://primaaviation.com/inventory"):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        for part in page.css.iselect("table[id='dTable'] > tbody > tr"):
            part_number, condition, qty, description, _ = part.select("td")
            if part_number.text != number:
                continue

            self.product_info["part number"] = part_number.text
            self.product_info["description"] = description.text
            self.product_info["QTY"] = qty.text
            self.product_info["condition"] = condition.text

            search_results.append(deepcopy(self.product_info))

        return self.status
