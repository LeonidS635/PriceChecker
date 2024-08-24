from bs4 import BeautifulSoup
from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests


class Skyspares(ParserRequests):
    def __init__(self):
        super().__init__()

    def login_function(self, login: str, password: str) -> Status:
        self.logged_in = True
        self.status = Status.OK
        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.request_wrapper(self.session.get, url=f"https://go.skyspares.aero/part/{number}"):
            if self.response.status_code == 404:
                self.status = Status.OK
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        part_number = page.select_one("h1").text
        if part_number.lower() == number.lower():
            self.product_info["part number"] = part_number
            self.product_info["description"] = page.select_one("table tr > td:nth-of-type(2)").text
            self.product_info["QTY"] = page.select_one("table tr:nth-of-type(2) > td:nth-of-type(2)").text

            if not self.request_wrapper(self.session.get, url=f"https://go.skyspares.aero/part/{number}/",
                                        params={"inline": "true"}, cookies={"currency": "USD"}):
                return self.status

            page = BeautifulSoup(self.response.text, "lxml")
            batches = page.select("div[class='batch-list-for-condition'] > div")
            if batches:
                for row in batches:
                    self.product_info["condition"] = row.select_one("div[class='col-2'] > span[class='hidden-xs']").text
                    self.product_info["QTY"] = row.select_one("div[class='col-4 text-right']").text
                    self.product_info["price"] = "".join(row.select_one("div[class='col-5 text-right']").text.split())
                    search_results.append(deepcopy(self.product_info))
            else:
                search_results.append(deepcopy(self.product_info))

        return self.status
