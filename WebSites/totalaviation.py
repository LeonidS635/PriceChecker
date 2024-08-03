from bs4 import BeautifulSoup
from copy import deepcopy
from Logic.data_file import Status
from Logic.parser import ParserRequests


class Totalaviation(ParserRequests):
    def __init__(self):
        super().__init__()

    def login_function(self, login: str, password: str) -> Status:
        self.logged_in = True
        self.status = Status.OK
        return self.status

    def search_part(self, number: str, search_results: list) -> Status:
        if not self.request_wrapper(self.session.get,
                                    url="https://subscription.totalaviation.com/stock-search-public/do",
                                    params={"q": number}):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        for part in page.select("div[class='result']"):
            if rows := part.select("dd"):
                self.product_info["part number"], self.product_info["description"], self.product_info["QTY"], \
                    self.product_info["condition"], _, _, _ = [elem.text for elem in rows]

                search_results.append(deepcopy(self.product_info))

        return self.status
