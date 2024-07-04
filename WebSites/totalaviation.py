from bs4 import BeautifulSoup
from copy import deepcopy
from requests import Session, Response
from requests.exceptions import Timeout, RequestException
from typing import Callable


class Totalaviation:
    def __init__(self):
        self.session = Session()

        self.delay = 20
        self.response = None
        self.status = "OK"

    def __del__(self):
        self.session.close()

    def request_wrapper(self, request: Callable[[], Response]) -> bool:
        try:
            self.response = request()
            self.response.raise_for_status()
        except Timeout:
            self.status = "Time error"
            return False
        except RequestException:
            self.status = "Connection error"
            return False
        else:
            self.status = "OK"
            return True

    def login_function(self, _: str, __: str) -> str:
        return self.status

    def search_part(self, number: str, search_results: list) -> str:
        product_info = {
            "vendor": "totalaviation",
            "part number": "",
            "description": "",
            "QTY": "",
            "price": "",
            "condition": "",
            "lead time": "",
            "warehouse": "",
            "other information": ""
        }

        def reset_product_info():
            product_info.clear()
            product_info["vendor"] = "totalaviation"

        search_url = f"https://subscription.totalaviation.com/stock-search-public/do?q={number}"
        if not self.request_wrapper(lambda: self.session.get(search_url, timeout=self.delay)):
            return self.status

        page = BeautifulSoup(self.response.text, "lxml")
        if rows := page.select("div[class='search-result-row'] > dd"):
            part_number, description, qty, condition, _, _, _ = rows

            reset_product_info()
            product_info["part number"] = part_number.text
            product_info["description"] = description.text.lower()
            product_info["condition"] = condition.text
            product_info["QTY"] = qty.text

            search_results.append(deepcopy(product_info))

        return self.status

    def change_delay(self, new_delay):
        self.delay = new_delay
